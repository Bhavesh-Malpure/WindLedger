import pytest
from datetime import datetime, timezone
from app.services.metrics import MetricsCalculator
from app.models.schemas import DeliveryIntervalAnalysis

def make_interval(p: int, actual: float = None, forecast: float = None):
    err = (forecast - actual) if (actual is not None and forecast is not None) else None
    abs_err = abs(err) if err is not None else None
    return DeliveryIntervalAnalysis(
        start_time=datetime(2026, 1, 15, (p - 1) // 2, 30 * ((p - 1) % 2), tzinfo=timezone.utc),
        settlement_period=p,
        actual_generation_mw=actual,
        forecast_generation_mw=forecast,
        error_mw=err,
        absolute_error_mw=abs_err,
        status="MATCHED" if (actual is not None and forecast is not None) else "MISSING"
    )

def test_metrics_hand_calculated_values():
    # 3 intervals with known values
    intervals = [
        make_interval(1, actual=1000.0, forecast=1100.0),  # err = +100
        make_interval(2, actual=2000.0, forecast=1900.0),  # err = -100
        make_interval(3, actual=3000.0, forecast=3200.0),  # err = +200
    ]
    
    metrics = MetricsCalculator.calculate(intervals, total_expected_intervals=3)
    
    assert metrics.matched_intervals == 3
    assert metrics.coverage_percent == 100.0
    # MAE = (100 + 100 + 200) / 3 = 133.33
    assert metrics.mae_mw == 133.33
    # RMSE = sqrt((10000 + 10000 + 40000) / 3) = sqrt(20000) = 141.42
    assert metrics.rmse_mw == 141.42
    # Bias = (100 - 100 + 200) / 3 = 66.67
    assert metrics.bias_mw == 66.67
    # WAPE = (400 / 6000) * 100 = 6.67%
    assert metrics.wape_percent == 6.67
    # Peak error
    assert metrics.peak_absolute_error_mw == 200.0

def test_metrics_empty_matched_intervals():
    intervals = [
        make_interval(1, actual=None, forecast=1000.0),
        make_interval(2, actual=2000.0, forecast=None),
        make_interval(3, actual=None, forecast=None)
    ]
    metrics = MetricsCalculator.calculate(intervals, total_expected_intervals=48)
    assert metrics.matched_intervals == 0
    assert metrics.coverage_percent == 0.0
    assert metrics.mae_mw is None
    assert metrics.rmse_mw is None
    assert metrics.bias_mw is None
    assert metrics.wape_percent is None
    assert metrics.peak_absolute_error_mw is None

def test_metrics_zero_actual_generation():
    # Extreme case: wind is 0 across all matched intervals (e.g. calm)
    intervals = [
        make_interval(1, actual=0.0, forecast=500.0),
        make_interval(2, actual=0.0, forecast=300.0),
    ]
    metrics = MetricsCalculator.calculate(intervals, total_expected_intervals=48)
    assert metrics.matched_intervals == 2
    assert metrics.mae_mw == 400.0
    assert metrics.bias_mw == 400.0
    # WAPE denominator sum(actual) is 0 -> should return None, never raise ZeroDivisionError
    assert metrics.wape_percent is None

def test_metrics_missing_intervals_not_treated_as_zero():
    # If out of 48 periods, only 24 are matched:
    intervals = [make_interval(p, actual=1000.0, forecast=1100.0) for p in range(1, 25)]
    # 24 missing periods
    intervals.extend([make_interval(p, actual=None, forecast=None) for p in range(25, 49)])
    
    metrics = MetricsCalculator.calculate(intervals, total_expected_intervals=48)
    # The denominator for MAE MUST be 24, not 48!
    assert metrics.matched_intervals == 24
    assert metrics.coverage_percent == 50.0
    assert metrics.mae_mw == 100.0  # (24 * 100) / 24 = 100.0
    assert metrics.bias_mw == 100.0


def test_metrics_underforecast_negative_bias():
    # Test case where actual generation exceeds forecast (under-forecast / short position avoided)
    intervals = [
        make_interval(1, actual=5000.0, forecast=4200.0),  # err = -800 MW
        make_interval(2, actual=6000.0, forecast=5500.0),  # err = -500 MW
        make_interval(3, actual=7000.0, forecast=6100.0),  # err = -900 MW
    ]
    metrics = MetricsCalculator.calculate(intervals, total_expected_intervals=48, interval_duration_hours=0.5)
    
    assert metrics.matched_intervals == 3
    # Bias must be negative: (-800 - 500 - 900) / 3 = -2200 / 3 = -733.33 MW
    assert metrics.bias_mw == -733.33
    # MAE must remain positive: (800 + 500 + 900) / 3 = 733.33 MW
    assert metrics.mae_mw == 733.33
    # RMSE: sqrt((640000 + 250000 + 810000) / 3) = sqrt(1700000 / 3) = sqrt(566666.67) = 752.77 MW
    assert metrics.rmse_mw == 752.77
    # WAPE: 2200 / 18000 * 100 = 12.22%
    assert metrics.wape_percent == 12.22
    # Volumes: sum(actual) = 18000 MW * 0.5 hr = 9000.0 MWh
    assert metrics.total_actual_volume_mwh == 9000.0
    # sum(forecast) = 15800 MW * 0.5 hr = 7900.0 MWh
    assert metrics.total_forecast_volume_mwh == 7900.0

def test_metrics_partial_interval_coverage():
    # Only 12 out of 48 settlement periods present (25% coverage)
    intervals = [make_interval(p, actual=2000.0, forecast=2100.0) for p in range(1, 13)]
    intervals.extend([make_interval(p, actual=None, forecast=None) for p in range(13, 49)])
    
    metrics = MetricsCalculator.calculate(intervals, total_expected_intervals=48, interval_duration_hours=0.5)
    assert metrics.matched_intervals == 12
    assert metrics.total_expected_intervals == 48
    assert metrics.coverage_percent == 25.0
    assert metrics.mae_mw == 100.0
    assert metrics.bias_mw == 100.0
    # 12 intervals * 2000 MW * 0.5 hr = 12,000 MWh
    assert metrics.total_actual_volume_mwh == 12000.0
    assert metrics.total_forecast_volume_mwh == 12600.0
