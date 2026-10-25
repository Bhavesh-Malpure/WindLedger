import math
import logging
from typing import List, Optional
from app.models.schemas import DeliveryIntervalAnalysis, AccuracyMetrics

logger = logging.getLogger(__name__)

class MetricsCalculator:
    """
    Calculates forecast verification and accuracy metrics across matched intervals.
    Follows UK energy procurement standards:
    - MAE (MW): average magnitude of procurement deviation
    - RMSE (MW): penalizes large deviations (costly imbalance risk)
    - Bias / Mean Error (MW): net direction of error (positive = over-procured / long; negative = under-procured / short)
    - WAPE (%): aggregate volume-weighted error; avoids division-by-zero on individual calm hours
    """

    @staticmethod
    def calculate(
        intervals: List[DeliveryIntervalAnalysis],
        total_expected_intervals: int = 48,
        interval_duration_hours: Optional[float] = None
    ) -> AccuracyMetrics:
        """
        Compute metrics from aligned delivery intervals.
        Only valid matched intervals with both actual and forecast generation are evaluated.
        """
        matched = [
            it for it in intervals
            if it.actual_generation_mw is not None and it.forecast_generation_mw is not None
        ]
        count = len(matched)

        if count == 0:
            return AccuracyMetrics(
                mae_mw=None,
                rmse_mw=None,
                bias_mw=None,
                wape_percent=None,
                peak_absolute_error_mw=None,
                matched_intervals=0,
                total_expected_intervals=total_expected_intervals,
                coverage_percent=0.0,
                total_actual_volume_mwh=None,
                total_forecast_volume_mwh=None
            )

        errors = [it.forecast_generation_mw - it.actual_generation_mw for it in matched]
        abs_errors = [abs(e) for e in errors]
        actual_values = [it.actual_generation_mw for it in matched]
        forecast_values = [it.forecast_generation_mw for it in matched]

        # 1. MAE
        mae = sum(abs_errors) / count

        # 2. RMSE
        mse = sum(e ** 2 for e in errors) / count
        rmse = math.sqrt(mse)

        # 3. Bias (Mean Error): forecast - actual
        bias = sum(errors) / count

        # 4. WAPE: (sum |F - A| / sum A) * 100
        sum_actual = sum(actual_values)
        if sum_actual > 0:
            wape = (sum(abs_errors) / sum_actual) * 100.0
        else:
            wape = None  # Undefined if total actual generation was zero

        # 5. Peak Absolute Error
        peak_abs_error = max(abs_errors)

        # 6. Volumes in MWh: Power (MW) * Duration (hours)
        # For standard UK settlement (48 periods/day), each interval is 0.5 hours (30 minutes).
        # For hourly resolution (24 periods/day), each interval is 1.0 hour.
        if interval_duration_hours is not None:
            duration_hours = interval_duration_hours
        elif total_expected_intervals == 24:
            duration_hours = 1.0
        else:
            duration_hours = 0.5

        total_actual_mwh = sum_actual * duration_hours
        total_forecast_mwh = sum(forecast_values) * duration_hours

        # Coverage percentage
        coverage = (count / total_expected_intervals) * 100.0 if total_expected_intervals > 0 else 0.0

        return AccuracyMetrics(
            mae_mw=round(mae, 2),
            rmse_mw=round(rmse, 2),
            bias_mw=round(bias, 2),
            wape_percent=round(wape, 2) if wape is not None else None,
            peak_absolute_error_mw=round(peak_abs_error, 2),
            matched_intervals=count,
            total_expected_intervals=total_expected_intervals,
            coverage_percent=round(coverage, 1),
            total_actual_volume_mwh=round(total_actual_mwh, 1),
            total_forecast_volume_mwh=round(total_forecast_mwh, 1)
        )
