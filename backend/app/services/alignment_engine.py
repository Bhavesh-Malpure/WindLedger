import logging
from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Optional, Literal

from app.models.schemas import (
    FuelHHRecord,
    WindforRecord,
    DeliveryIntervalAnalysis
)

logger = logging.getLogger(__name__)

AlignmentMode = Literal["exact", "half_hourly_expanded"]

class AlignmentEngine:
    """
    Aligns actual wind generation (FUELHH) and forecast records (WINDFOR)
    across delivery intervals with transparent status reporting.
    """

    def align(
        self,
        actuals: List[FuelHHRecord],
        forecast_by_start: Dict[datetime, WindforRecord],
        delivery_date: date,
        mode: AlignmentMode = "half_hourly_expanded"
    ) -> List[DeliveryIntervalAnalysis]:
        """
        Align actuals and forecasts for all 48 half-hour settlement periods of delivery_date.
        In 'half_hourly_expanded' mode (default), an hourly forecast at HH:00 is applied
        to both HH:00 (period 2k-1) and HH:30 (period 2k).
        In 'exact' mode, only exact startTime matches are paired.
        """
        actual_by_start = {a.start_time: a for a in actuals}
        aligned_intervals: List[DeliveryIntervalAnalysis] = []

        # Generate all 48 expected half-hour delivery intervals for the day
        start_of_day = datetime(delivery_date.year, delivery_date.month, delivery_date.day, 0, 0, 0, tzinfo=timezone.utc)
        
        for p in range(1, 49):
            interval_start = start_of_day + timedelta(minutes=30 * (p - 1))
            actual_rec = actual_by_start.get(interval_start)

            # Determine matching forecast
            forecast_rec: Optional[WindforRecord] = None
            if mode == "exact":
                forecast_rec = forecast_by_start.get(interval_start)
            else:
                # In half_hourly_expanded:
                # If interval is HH:00, exact match with HH:00 forecast
                # If interval is HH:30, match with the hourly forecast of HH:00
                if interval_start.minute == 0:
                    forecast_rec = forecast_by_start.get(interval_start)
                else:
                    hour_start = interval_start.replace(minute=0)
                    forecast_rec = forecast_by_start.get(hour_start)

            actual_mw = actual_rec.generation if actual_rec else None
            forecast_mw = forecast_rec.generation if forecast_rec else None
            forecast_pub = forecast_rec.publish_time if forecast_rec else None

            # Determine error and status
            error_mw: Optional[float] = None
            abs_error_mw: Optional[float] = None
            pct_error: Optional[float] = None
            status_val = "MATCHED"

            if actual_mw is not None and forecast_mw is not None:
                error_mw = round(forecast_mw - actual_mw, 2)
                abs_error_mw = round(abs(error_mw), 2)
                if actual_mw > 0:
                    pct_error = round((abs_error_mw / actual_mw) * 100, 2)
                else:
                    pct_error = None  # Undefined / zero division avoided
                status_val = "MATCHED"
            elif actual_mw is None and forecast_mw is not None:
                status_val = "MISSING_ACTUAL"
            elif actual_mw is not None and forecast_mw is None:
                status_val = "MISSING_FORECAST"
            else:
                status_val = "MISSING_BOTH"

            aligned_intervals.append(
                DeliveryIntervalAnalysis(
                    start_time=interval_start,
                    settlement_period=p,
                    actual_generation_mw=actual_mw,
                    forecast_generation_mw=forecast_mw,
                    forecast_publish_time=forecast_pub,
                    error_mw=error_mw,
                    absolute_error_mw=abs_error_mw,
                    percentage_error=pct_error,
                    status=status_val
                )
            )

        return aligned_intervals
