import logging
import json
import time
from pathlib import Path
from typing import List, Tuple, Union, Optional
from datetime import datetime, date, timedelta, timezone
import httpx

from app.core.config import settings
from app.core.errors import ElexonAPIError
from app.models.schemas import WindforRecord
from app.utils.timezone import parse_utc_iso, format_utc_iso

logger = logging.getLogger(__name__)

class WindforClient:
    """Client for fetching and validating UK national wind forecasts from Elexon BMRS WINDFOR dataset."""

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None):
        self.base_url = (base_url or settings.elexon_api_base_url).rstrip("/")
        self.endpoint = f"{self.base_url}/datasets/WINDFOR/stream"
        self.timeout = timeout or settings.http_timeout_seconds
        self.fixture_dir = Path(settings.fixture_dir)

    def fetch_forecasts(
        self,
        publish_from: datetime,
        publish_to: datetime,
        delivery_date: Optional[Union[date, str]] = None,
        force_fixture: Optional[bool] = None
    ) -> Tuple[List[WindforRecord], bool]:
        """Fetch forecast vintages and return (records, is_fixture_data).

        The documented WINDFOR endpoint is queried by delivery-time range; its
        publishTime values are then filtered locally to the requested vintage window.
        Fixtures are never substituted silently by default.
        """
        use_fixture = settings.force_fixture_mode if force_fixture is None else force_fixture
        date_str = delivery_date.isoformat() if isinstance(delivery_date, date) else (str(delivery_date) if delivery_date else None)
        if use_fixture:
            if not date_str:
                return [], True
            return self._load_fixture(date_str, publish_from, publish_to), True

        upstream_error = "live endpoint returned no valid forecast records for the requested delivery date and publication window"
        try:
            raw_data = self._fetch_live(publish_from, publish_to, delivery_date)
            records = self._parse_and_validate(raw_data, delivery_date)
            records = [r for r in records if publish_from <= r.publish_time <= publish_to]
            if records:
                return records, False
        except Exception as exc:
            upstream_error = str(exc)
            logger.warning("Live WINDFOR request failed for delivery date %s: %s", date_str, exc)

        if settings.allow_fixture_fallback and date_str:
            records = self._load_fixture(date_str, publish_from, publish_to)
            if records:
                logger.warning("Using explicitly enabled WINDFOR fixture fallback for %s", date_str)
                return records, True

        raise ElexonAPIError(
            f"Unable to retrieve valid live WINDFOR forecast records for {date_str or 'requested date'}. "
            f"No fixture fallback was used. Details: {upstream_error}. "
            "For an intentional offline demo, set FORCE_FIXTURE_MODE=true."
        )

    def fetch_forecasts_for_delivery_date(
        self,
        delivery_date: Union[date, str],
        cutoff_datetime: datetime,
        lookback_days: int = 2,
        force_fixture: Optional[bool] = None
    ) -> Tuple[List[WindforRecord], bool]:
        """
        Convenience method to query forecasts published leading up to cutoff_datetime for a delivery date.
        Queries from (cutoff_datetime - lookback_days) up to cutoff_datetime.
        """
        if isinstance(delivery_date, str):
            delivery_date = date.fromisoformat(delivery_date)

        publish_from = cutoff_datetime - timedelta(days=lookback_days)
        publish_to = cutoff_datetime

        return self.fetch_forecasts(
            publish_from=publish_from,
            publish_to=publish_to,
            delivery_date=delivery_date,
            force_fixture=force_fixture
        )

    def _fetch_live(
        self,
        publish_from: datetime,
        publish_to: datetime,
        delivery_date: Optional[Union[date, str]] = None,
    ) -> List[dict]:
        """Query raw WINDFOR records by publication-time window.

        Day-ahead evaluation needs historical forecast vintages, not merely the latest
        forecast currently available for a delivery interval. Query the raw WINDFOR
        dataset stream by publication time, then filter by delivery date and cutoff.
        """
        if delivery_date is None:
            raise ValueError("delivery_date is required for the WINDFOR endpoint")
        target_date = date.fromisoformat(str(delivery_date)) if not isinstance(delivery_date, date) else delivery_date
        params = {
            "publishDateTimeFrom": format_utc_iso(publish_from),
            "publishDateTimeTo": format_utc_iso(publish_to),
        }
        headers = {
            "Accept": "application/json",
            "User-Agent": "UK-Wind-Procurement-Portal/1.0"
        }

        retries = settings.max_retries
        backoff = 1.0

        for attempt in range(1, retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(self.endpoint, params=params, headers=headers)
                    if resp.status_code == 200:
                        payload = resp.json()
                        if isinstance(payload, dict):
                            payload = payload.get("data", payload.get("results", []))
                        if not isinstance(payload, list):
                            raise ValueError("Unexpected WINDFOR response: expected a JSON list or an object containing data")
                        return payload
                    elif resp.status_code in (429, 502, 503, 504):
                        logger.warning(f"WINDFOR upstream returned {resp.status_code} on attempt {attempt}/{retries}")
                    else:
                        logger.error(f"WINDFOR upstream returned unhandled status {resp.status_code}: {resp.text[:200]}")
                        break
            except (httpx.RequestError, httpx.TimeoutException) as req_err:
                logger.warning(f"WINDFOR request error on attempt {attempt}/{retries}: {req_err}")

            if attempt < retries:
                time.sleep(backoff)
                backoff *= settings.retry_backoff_factor

        raise RuntimeError(f"Failed to retrieve WINDFOR data after {retries} attempts.")

    def _parse_and_validate(
        self,
        raw_items: List[dict],
        delivery_date: Optional[Union[date, str]] = None
    ) -> List[WindforRecord]:
        """Filter to delivery_date, validate schema, normalize timestamps, and deduplicate deterministically."""
        target_date_str = delivery_date.isoformat() if isinstance(delivery_date, date) else (str(delivery_date) if delivery_date else None)
        by_key = {}

        for item in raw_items:
            try:
                # Prefer settlementDate + settlementPeriod when the raw dataset
                # provides them. These fields identify the delivery interval even if
                # startTime in a reduced payload is absent or represents publication.
                start_time = None
                raw_settlement_date = item.get("settlementDate")
                raw_settlement_period = item.get("settlementPeriod")
                if raw_settlement_date is not None and raw_settlement_period is not None:
                    try:
                        settlement_date = (
                            date.fromisoformat(raw_settlement_date)
                            if isinstance(raw_settlement_date, str) else raw_settlement_date
                        )
                        settlement_period = int(raw_settlement_period)
                        if 1 <= settlement_period <= 50:
                            start_time = datetime(
                                settlement_date.year, settlement_date.month, settlement_date.day,
                                tzinfo=timezone.utc
                            ) + timedelta(minutes=30 * (settlement_period - 1))
                    except (TypeError, ValueError):
                        start_time = None

                if start_time is None:
                    raw_start = item.get("startTime")
                    if not raw_start:
                        continue
                    start_time = parse_utc_iso(raw_start)

                if target_date_str and start_time.strftime("%Y-%m-%d") != target_date_str:
                    continue

                gen_raw = item.get("generation")
                if gen_raw is None:
                    continue
                generation = float(gen_raw)

                raw_publish = item.get("publishTime")
                if not raw_publish:
                    continue
                publish_time = parse_utc_iso(raw_publish)

                record = WindforRecord(
                    dataset=item.get("dataset", "WINDFOR"),
                    publish_time=publish_time,
                    start_time=start_time,
                    generation=generation
                )

                # Deduplicate key: (start_time, publish_time)
                key = (record.start_time, record.publish_time)
                by_key[key] = record

            except Exception as parse_err:
                logger.warning(f"Skipping malformed WINDFOR record: {parse_err}")

        # Return sorted by publish_time, then start_time
        sorted_records = sorted(by_key.values(), key=lambda r: (r.publish_time, r.start_time))
        return sorted_records

    def _load_fixture(
        self,
        date_str: str,
        publish_from: Optional[datetime] = None,
        publish_to: Optional[datetime] = None
    ) -> List[WindforRecord]:
        """Load offline fixture data for testing and offline resilience."""
        fixture_file = self.fixture_dir / f"windfor_{date_str}.json"
        if fixture_file.exists():
            with open(fixture_file, "r", encoding="utf-8") as f:
                payload = json.load(f)
            data = payload.get("data", payload.get("results", [])) if isinstance(payload, dict) else payload
            records = self._parse_and_validate(data, date_str)
            if publish_from or publish_to:
                filtered = []
                for r in records:
                    if publish_from and r.publish_time < publish_from:
                        continue
                    if publish_to and r.publish_time > publish_to:
                        continue
                    filtered.append(r)
                return filtered
            return records
        logger.warning(f"No WINDFOR fixture file found at {fixture_file}")
        return []
