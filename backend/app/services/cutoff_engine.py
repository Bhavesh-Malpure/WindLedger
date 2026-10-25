import logging
from datetime import datetime, date, timezone
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict

from app.models.schemas import WindforRecord, VintageSummary
from app.utils.timezone import parse_utc_iso, get_cutoff_datetime

logger = logging.getLogger(__name__)

class CutoffEngine:
    """
    Enforces day-ahead decision cutoff rules and selects eligible forecast records
    without look-ahead bias (data leakage).
    """

    def __init__(self, default_cutoff_hour: int = 11, default_cutoff_day_offset: int = 1):
        self.default_cutoff_hour = default_cutoff_hour
        self.default_cutoff_day_offset = default_cutoff_day_offset

    def compute_cutoff(
        self,
        delivery_date: date,
        cutoff_hour: Optional[int] = None,
        cutoff_day_offset: Optional[int] = None
    ) -> datetime:
        """Calculate the UTC datetime cutoff for the given delivery date."""
        hour = self.default_cutoff_hour if cutoff_hour is None else cutoff_hour
        offset = self.default_cutoff_day_offset if cutoff_day_offset is None else cutoff_day_offset
        return get_cutoff_datetime(delivery_date, cutoff_hour=hour, cutoff_day_offset=offset)

    def filter_eligible_forecasts(
        self,
        records: List[WindforRecord],
        cutoff_datetime: datetime
    ) -> Tuple[List[WindforRecord], List[WindforRecord]]:
        """
        Split forecast records into eligible (published <= cutoff) and rejected (published > cutoff).
        Guarantees zero data leakage.
        """
        eligible: List[WindforRecord] = []
        rejected: List[WindforRecord] = []

        for r in records:
            if r.publish_time <= cutoff_datetime:
                eligible.append(r)
            else:
                rejected.append(r)

        if rejected:
            logger.info(
                f"Cutoff filter rejected {len(rejected)} records published after cutoff {cutoff_datetime.isoformat()}"
            )
        return eligible, rejected

    def select_latest_eligible_forecasts(
        self,
        eligible_records: List[WindforRecord]
    ) -> Dict[datetime, WindforRecord]:
        """
        For each unique delivery interval (start_time), select the forecast record
        with the latest publish_time.
        Returns:
            Dict[start_time, WindforRecord]
        """
        by_start_time: Dict[datetime, WindforRecord] = {}

        for r in eligible_records:
            current = by_start_time.get(r.start_time)
            if current is None or r.publish_time > current.publish_time:
                by_start_time[r.start_time] = r

        return by_start_time

    def extract_vintage_summaries(
        self,
        all_records: List[WindforRecord],
        cutoff_datetime: datetime,
        selected_latest_vintage_time: Optional[datetime] = None
    ) -> List[VintageSummary]:
        """
        Group records by publish_time and generate a summary list of all available vintages.
        """
        by_vintage: Dict[datetime, List[WindforRecord]] = defaultdict(list)
        for r in all_records:
            by_vintage[r.publish_time].append(r)

        summaries: List[VintageSummary] = []
        for pub_time in sorted(by_vintage.keys()):
            recs = by_vintage[pub_time]
            starts = [r.start_time for r in recs]
            is_eligible = pub_time <= cutoff_datetime
            is_selected = (pub_time == selected_latest_vintage_time)

            summaries.append(
                VintageSummary(
                    publish_time=pub_time,
                    intervals_count=len(recs),
                    first_delivery_time=min(starts) if starts else None,
                    last_delivery_time=max(starts) if starts else None,
                    is_eligible=is_eligible,
                    is_selected=is_selected
                )
            )

        return summaries
