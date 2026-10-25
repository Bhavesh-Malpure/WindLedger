import logging
import json
import time
from pathlib import Path
from typing import List, Tuple, Union, Optional
from datetime import date, datetime, timedelta, timezone
import httpx

from app.core.config import settings
from app.core.errors import ElexonAPIError
from app.models.schemas import FuelHHRecord
from app.utils.timezone import parse_utc_iso

logger = logging.getLogger(__name__)

class FuelHHClient:
    """Client for fetching and validating UK actual generation from Elexon BMRS FUELHH dataset."""

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None):
        self.base_url = (base_url or settings.elexon_api_base_url).rstrip("/")
        self.endpoint = f"{self.base_url}/datasets/FUELHH/stream"
        self.timeout = timeout or settings.http_timeout_seconds
        self.fixture_dir = Path(settings.fixture_dir)

    def fetch_actuals(
        self,
        delivery_date: Union[date, str],
        force_fixture: Optional[bool] = None
    ) -> Tuple[List[FuelHHRecord], bool]:
        """Fetch actuals and return (records, is_fixture_data).

        Fixtures are used only when explicitly requested, or when the operator
        explicitly enables ALLOW_FIXTURE_FALLBACK. The default is fail-closed so
        an upstream outage cannot silently produce apparently-live results.
        """
        date_str = delivery_date.isoformat() if isinstance(delivery_date, date) else str(delivery_date)
        use_fixture = settings.force_fixture_mode if force_fixture is None else force_fixture
        if use_fixture:
            return self._load_fixture(date_str), True

        upstream_error = "live endpoint returned no valid WIND records"
        try:
            raw_data = self._fetch_live(date_str)
            records = self._parse_and_validate(raw_data)
            if records:
                return records, False
        except Exception as exc:
            upstream_error = str(exc)
            logger.warning("Live FUELHH request failed for %s: %s", date_str, exc)

        if settings.allow_fixture_fallback:
            records = self._load_fixture(date_str)
            if records:
                logger.warning("Using explicitly enabled FUELHH fixture fallback for %s", date_str)
                return records, True

        raise ElexonAPIError(
            f"Unable to retrieve valid live FUELHH WIND records for {date_str}. "
            f"No fixture fallback was used. Details: {upstream_error}. "
            "For an intentional offline demo, set FORCE_FIXTURE_MODE=true."
        )

    def _fetch_live(self, date_str: str) -> List[dict]:
        """Query Elexon BMRS FUELHH stream endpoint with bounded retries."""
        params = {
            "settlementDateFrom": date_str,
            "settlementDateTo": date_str,
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
                            raise ValueError("Unexpected FUELHH response: expected a JSON list or an object containing data")
                        return payload
                    elif resp.status_code in (429, 502, 503, 504):
                        logger.warning(f"FUELHH upstream returned {resp.status_code} on attempt {attempt}/{retries}")
                    else:
                        logger.error(f"FUELHH upstream returned unhandled status {resp.status_code}: {resp.text[:200]}")
                        break
            except (httpx.RequestError, httpx.TimeoutException) as req_err:
                logger.warning(f"FUELHH request error on attempt {attempt}/{retries}: {req_err}")

            if attempt < retries:
                time.sleep(backoff)
                backoff *= settings.retry_backoff_factor

        raise RuntimeError(f"Failed to retrieve FUELHH data for {date_str} after {retries} attempts.")

    def _parse_and_validate(self, raw_items: List[dict]) -> List[FuelHHRecord]:
        """Filter to WIND, validate schema, normalize timestamps, and deduplicate deterministically."""
        records: List[FuelHHRecord] = []
        by_start_time = {}

        for item in raw_items:
            # Check fuelType (must be WIND)
            fuel_type = str(item.get("fuelType", "")).upper()
            if fuel_type != "WIND":
                continue

            try:
                # Handle possible null or missing generation
                gen_raw = item.get("generation")
                if gen_raw is None:
                    continue
                generation = float(gen_raw)

                settlement_date = date.fromisoformat(item["settlementDate"]) if isinstance(item["settlementDate"], str) else item["settlementDate"]
                settlement_period = int(item["settlementPeriod"])
                raw_start_time = item.get("startTime")
                if raw_start_time:
                    start_time = parse_utc_iso(raw_start_time)
                else:
                    # FUELHH stream payloads may identify a settlement interval by
                    # settlementDate + settlementPeriod without a startTime field.
                    # SP1 starts at 00:00 UTC, SP2 at 00:30 UTC, etc.
                    if settlement_period < 1 or settlement_period > 50:
                        raise ValueError(f"Invalid settlementPeriod: {settlement_period}")
                    start_time = datetime(
                        settlement_date.year, settlement_date.month, settlement_date.day,
                        tzinfo=timezone.utc
                    ) + timedelta(minutes=30 * (settlement_period - 1))
                raw_publish_time = item.get("publishTime")
                # Some reduced dataset payloads omit publishTime; retain an explicit
                # deterministic timestamp only if the source provides it. Do not invent it.
                if not raw_publish_time:
                    raise ValueError("Missing publishTime")
                publish_time = parse_utc_iso(raw_publish_time)

                record = FuelHHRecord(
                    dataset=item.get("dataset", "FUELHH"),
                    publish_time=publish_time,
                    start_time=start_time,
                    settlement_date=settlement_date,
                    settlement_period=settlement_period,
                    fuel_type="WIND",
                    generation=generation
                )

                # Deduplicate: if duplicate startTime, keep the one with latest publishTime
                key = record.start_time
                if key not in by_start_time or record.publish_time > by_start_time[key].publish_time:
                    by_start_time[key] = record

            except Exception as parse_err:
                logger.warning(f"Skipping malformed FUELHH record: {parse_err}")

        # Return sorted by startTime
        sorted_records = sorted(by_start_time.values(), key=lambda r: r.start_time)
        return sorted_records

    def _load_fixture(self, date_str: str) -> List[FuelHHRecord]:
        """Load offline fixture data for testing and offline resiliency."""
        fixture_file = self.fixture_dir / f"fuelhh_{date_str}.json"
        if fixture_file.exists():
            with open(fixture_file, "r", encoding="utf-8") as f:
                payload = json.load(f)
            data = payload.get("data", payload.get("results", [])) if isinstance(payload, dict) else payload
            return self._parse_and_validate(data)
        logger.warning(f"No FUELHH fixture file found at {fixture_file}")
        return []
