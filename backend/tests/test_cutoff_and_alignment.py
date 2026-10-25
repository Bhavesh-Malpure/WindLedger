import pytest
from datetime import datetime, date, timezone
from app.services.cutoff_engine import CutoffEngine
from app.services.alignment_engine import AlignmentEngine
from app.models.schemas import WindforRecord, FuelHHRecord

def test_cutoff_computation_month_boundary():
    engine = CutoffEngine(default_cutoff_hour=11, default_cutoff_day_offset=1)
    
    # Boundary: Jan 1st 2026 rolls over to Dec 31st 2025
    cutoff_jan1 = engine.compute_cutoff(date(2026, 1, 1))
    assert cutoff_jan1 == datetime(2025, 12, 31, 11, 0, 0, tzinfo=timezone.utc)
    
    # Mid-month: Jan 15th
    cutoff_jan15 = engine.compute_cutoff(date(2026, 1, 15))
    assert cutoff_jan15 == datetime(2026, 1, 14, 11, 0, 0, tzinfo=timezone.utc)
    
    # Custom cutoff hour: 12:00 UTC
    cutoff_custom = engine.compute_cutoff(date(2026, 1, 15), cutoff_hour=12)
    assert cutoff_custom == datetime(2026, 1, 14, 12, 0, 0, tzinfo=timezone.utc)

def test_cutoff_strict_leakage_prevention():
    engine = CutoffEngine()
    cutoff = datetime(2026, 1, 14, 11, 0, 0, tzinfo=timezone.utc)
    
    records = [
        # Exactly on cutoff -> eligible
        WindforRecord(
            dataset="WINDFOR",
            publish_time=datetime(2026, 1, 14, 11, 0, 0, tzinfo=timezone.utc),
            start_time=datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc),
            generation=10000
        ),
        # Before cutoff -> eligible
        WindforRecord(
            dataset="WINDFOR",
            publish_time=datetime(2026, 1, 14, 9, 30, 0, tzinfo=timezone.utc),
            start_time=datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc),
            generation=9500
        ),
        # 1 second after cutoff -> STRICTLY REJECTED (leakage prevention)
        WindforRecord(
            dataset="WINDFOR",
            publish_time=datetime(2026, 1, 14, 11, 0, 1, tzinfo=timezone.utc),
            start_time=datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc),
            generation=12000
        ),
        # Hours after cutoff -> REJECTED
        WindforRecord(
            dataset="WINDFOR",
            publish_time=datetime(2026, 1, 14, 15, 30, 0, tzinfo=timezone.utc),
            start_time=datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc),
            generation=11000
        )
    ]
    
    eligible, rejected = engine.filter_eligible_forecasts(records, cutoff)
    assert len(eligible) == 2
    assert len(rejected) == 2
    assert all(r.publish_time <= cutoff for r in eligible)
    assert all(r.publish_time > cutoff for r in rejected)

def test_select_latest_eligible_forecast():
    engine = CutoffEngine()
    start_t = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
    
    records = [
        # Vintage 1 (early)
        WindforRecord(
            dataset="WINDFOR",
            publish_time=datetime(2026, 1, 13, 18, 0, tzinfo=timezone.utc),
            start_time=start_t,
            generation=8000
        ),
        # Vintage 2 (latest before cutoff)
        WindforRecord(
            dataset="WINDFOR",
            publish_time=datetime(2026, 1, 14, 9, 30, tzinfo=timezone.utc),
            start_time=start_t,
            generation=9200
        ),
        # Vintage 3 (intermediate)
        WindforRecord(
            dataset="WINDFOR",
            publish_time=datetime(2026, 1, 14, 4, 30, tzinfo=timezone.utc),
            start_time=start_t,
            generation=8700
        )
    ]
    
    selected = engine.select_latest_eligible_forecasts(records)
    assert len(selected) == 1
    assert selected[start_t].generation == 9200
    assert selected[start_t].publish_time == datetime(2026, 1, 14, 9, 30, tzinfo=timezone.utc)

def test_alignment_zero_actual_avoid_zero_division():
    aligner = AlignmentEngine()
    delivery_d = date(2026, 1, 15)
    
    actuals = [
        FuelHHRecord(
            dataset="FUELHH",
            publish_time=datetime(2026, 1, 16, 0, 0, tzinfo=timezone.utc),
            start_time=datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc),
            settlement_date=delivery_d,
            settlement_period=1,
            fuel_type="WIND",
            generation=0.0  # Zero wind generation (complete calm)
        )
    ]
    forecasts = {
        datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc): WindforRecord(
            dataset="WINDFOR",
            publish_time=datetime(2026, 1, 14, 9, 30, tzinfo=timezone.utc),
            start_time=datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc),
            generation=500.0
        )
    }
    
    intervals = aligner.align(actuals, forecasts, delivery_d, mode="exact")
    # First interval has actual = 0.0, forecast = 500.0
    int_1 = intervals[0]
    assert int_1.actual_generation_mw == 0.0
    assert int_1.forecast_generation_mw == 500.0
    assert int_1.error_mw == 500.0
    assert int_1.percentage_error is None  # Avoided division by zero!
    assert int_1.status == "MATCHED"

def test_alignment_missing_handling():
    aligner = AlignmentEngine()
    delivery_d = date(2026, 1, 15)
    
    # Only 1 actual period (period 1) and 1 forecast period (period 3)
    actuals = [
        FuelHHRecord(
            dataset="FUELHH",
            publish_time=datetime(2026, 1, 16, 0, 0, tzinfo=timezone.utc),
            start_time=datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc),
            settlement_date=delivery_d,
            settlement_period=1,
            fuel_type="WIND",
            generation=5000.0
        )
    ]
    forecasts = {
        datetime(2026, 1, 15, 1, 0, tzinfo=timezone.utc): WindforRecord(
            dataset="WINDFOR",
            publish_time=datetime(2026, 1, 14, 9, 30, tzinfo=timezone.utc),
            start_time=datetime(2026, 1, 15, 1, 0, tzinfo=timezone.utc),
            generation=6000.0
        )
    }
    
    intervals = aligner.align(actuals, forecasts, delivery_d, mode="exact")
    assert len(intervals) == 48
    # Period 1 (00:00): actual present, forecast missing
    assert intervals[0].status == "MISSING_FORECAST"
    assert intervals[0].error_mw is None
    # Period 3 (01:00): forecast present, actual missing
    assert intervals[2].status == "MISSING_ACTUAL"
    assert intervals[2].error_mw is None
    # Period 4 (01:30): both missing
    assert intervals[3].status == "MISSING_BOTH"


def test_extract_vintage_summaries_tags_eligibility():
    engine = CutoffEngine()
    cutoff = datetime(2026, 1, 14, 11, 0, 0, tzinfo=timezone.utc)
    
    records = [
        WindforRecord(
            dataset="WINDFOR",
            publish_time=datetime(2026, 1, 14, 9, 30, tzinfo=timezone.utc),
            start_time=datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc),
            generation=9500
        ),
        WindforRecord(
            dataset="WINDFOR",
            publish_time=datetime(2026, 1, 14, 15, 30, tzinfo=timezone.utc),  # Post-cutoff
            start_time=datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc),
            generation=9800
        )
    ]
    
    summaries = engine.extract_vintage_summaries(records, cutoff, selected_latest_vintage_time=datetime(2026, 1, 14, 9, 30, tzinfo=timezone.utc))
    assert len(summaries) == 2
    s_early = next(s for s in summaries if s.publish_time == datetime(2026, 1, 14, 9, 30, tzinfo=timezone.utc))
    s_late = next(s for s in summaries if s.publish_time == datetime(2026, 1, 14, 15, 30, tzinfo=timezone.utc))
    
    assert s_early.is_eligible is True
    assert s_early.is_selected is True
    assert s_late.is_eligible is False
    assert s_late.is_selected is False
