from fastapi import APIRouter, Query
from datetime import date
from typing import Optional
from app.models.schemas import VintageComparisonResponse
from app.services.procurement_service import ProcurementAnalysisService
from app.core.config import settings

router = APIRouter(prefix="/vintages", tags=["Vintages"])
service = ProcurementAnalysisService()

@router.get("/compare", response_model=VintageComparisonResponse)
def compare_forecast_vintages(
    delivery_date: date = Query(
        ...,
        description="Delivery date in January 2026 (format YYYY-MM-DD, e.g. 2026-01-15)"
    ),
    cutoff_hour: Optional[int] = Query(
        settings.default_cutoff_hour_utc,
        ge=0,
        le=23,
        description="Day-ahead cutoff hour in UTC (default 11)"
    ),
    cutoff_day_offset: Optional[int] = Query(
        settings.default_cutoff_day_offset,
        ge=1,
        le=3,
        description="Days prior to delivery (default 1)"
    ),
    force_fixture: Optional[bool] = Query(
        None,
        description="Override to force fixture data"
    )
):
    """
    Retrieve time series of all eligible forecast vintages published prior to cutoff
    for the selected delivery date to observe forecast evolution.
    """
    return service.compare_vintages(
        delivery_date=delivery_date,
        cutoff_hour=cutoff_hour,
        cutoff_day_offset=cutoff_day_offset,
        force_fixture=force_fixture
    )
