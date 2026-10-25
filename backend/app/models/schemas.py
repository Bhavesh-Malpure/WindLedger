from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date

class FuelHHRecord(BaseModel):
    """Schema for parsed FUELHH actual generation record (Elexon BMRS)."""
    dataset: str = "FUELHH"
    publish_time: datetime
    start_time: datetime
    settlement_date: date
    settlement_period: int
    fuel_type: str
    generation: float

    @field_validator("generation")
    @classmethod
    def validate_generation(cls, v: float) -> float:
        if v < 0:
            # Negative generation in rare balancing edge cases or metering error; preserve numeric value
            return float(v)
        return float(v)

class WindforRecord(BaseModel):
    """Schema for parsed WINDFOR wind forecast record (Elexon BMRS)."""
    dataset: str = "WINDFOR"
    publish_time: datetime
    start_time: datetime
    generation: float

class DeliveryIntervalAnalysis(BaseModel):
    """Aligned forecast vs actual record for a single delivery interval."""
    start_time: datetime
    settlement_period: Optional[int] = None
    actual_generation_mw: Optional[float] = None
    forecast_generation_mw: Optional[float] = None
    forecast_publish_time: Optional[datetime] = None
    error_mw: Optional[float] = None  # forecast - actual
    absolute_error_mw: Optional[float] = None  # |forecast - actual|
    percentage_error: Optional[float] = None  # |forecast - actual| / actual * 100 (null if actual <= 0)
    status: str = "MATCHED"  # MATCHED, MISSING_FORECAST, MISSING_ACTUAL

class AccuracyMetrics(BaseModel):
    """Forecast performance metrics calculated across matched intervals."""
    mae_mw: Optional[float] = Field(None, description="Mean Absolute Error in MW")
    rmse_mw: Optional[float] = Field(None, description="Root Mean Square Error in MW")
    bias_mw: Optional[float] = Field(None, description="Mean Error (Forecast - Actual) in MW; positive = overforecast")
    wape_percent: Optional[float] = Field(None, description="Weighted Absolute Percentage Error (Sum |Error| / Sum Actual * 100)")
    peak_absolute_error_mw: Optional[float] = Field(None, description="Maximum single-interval absolute error in MW")
    matched_intervals: int = Field(..., description="Number of intervals with valid forecast and actual pair")
    total_expected_intervals: int = Field(..., description="Total expected intervals in delivery day (e.g. 48 for HH, 24 for hourly)")
    coverage_percent: float = Field(..., description="Matched intervals / Total expected intervals * 100")
    total_actual_volume_mwh: Optional[float] = Field(None, description="Total outturn actual energy in MWh")
    total_forecast_volume_mwh: Optional[float] = Field(None, description="Total forecast energy in MWh")

class VintageSummary(BaseModel):
    """Metadata summary of an available forecast vintage published prior to delivery."""
    publish_time: datetime
    intervals_count: int
    first_delivery_time: Optional[datetime] = None
    last_delivery_time: Optional[datetime] = None
    is_eligible: bool
    is_selected: bool = False

class VintageSeriesItem(BaseModel):
    """Interval point for an alternative vintage."""
    start_time: datetime
    forecast_generation_mw: float

class VintageComparisonResponse(BaseModel):
    """Comparison of multiple forecast vintages across the delivery day."""
    delivery_date: str
    vintages: Dict[str, List[VintageSeriesItem]]  # publish_time ISO -> list of points

class AnalysisResponse(BaseModel):
    """Main response contract for day-ahead procurement analysis."""
    delivery_date: str
    decision_cutoff_utc: datetime
    cutoff_hour_utc: int
    selected_vintage_publish_time: Optional[datetime] = None
    data_source: str = "Elexon BMRS (FUELHH & WINDFOR)"
    freshness_timestamp: datetime
    metrics: AccuracyMetrics
    intervals: List[DeliveryIntervalAnalysis]
    available_vintages: List[VintageSummary]
    data_limitations: List[str]
    is_fixture_data: bool = False
    actuals_source: str = "live"
    forecast_source: str = "live"
    source_warning: Optional[str] = None

class DeliveryDateStatus(BaseModel):
    """Availability status of a January 2026 delivery date."""
    date_str: str  # YYYY-MM-DD
    has_actuals: bool
    has_forecasts: bool
    is_valid_january_2026: bool

class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = "ok"
    version: str = "1.0.0"
    timestamp: datetime
    environment: str
    upstream_elexon_status: str
    is_fixture_mode: bool
    note: Optional[str] = None
