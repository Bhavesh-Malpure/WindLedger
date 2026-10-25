from fastapi import APIRouter, Query, HTTPException, status
from datetime import date
from typing import Optional, Literal

from app.models.schemas import AnalysisResponse
from app.services.procurement_service import ProcurementAnalysisService
from app.core.config import settings

router = APIRouter(prefix="/analysis", tags=["Analysis"])
service = ProcurementAnalysisService()

@router.get("", response_model=AnalysisResponse)
def get_procurement_analysis(
    delivery_date: date = Query(
        ...,
        description="Delivery date in January 2026 (format YYYY-MM-DD, e.g. 2026-01-15)"
    ),
    cutoff_hour: Optional[int] = Query(
        settings.default_cutoff_hour_utc,
        ge=0,
        le=23,
        description="Day-ahead auction decision cutoff hour in UTC (default 11)"
    ),
    cutoff_day_offset: Optional[int] = Query(
        settings.default_cutoff_day_offset,
        ge=1,
        le=3,
        description="Days prior to delivery for cutoff (default 1 for D-1)"
    ),
    alignment_mode: Literal["half_hourly_expanded", "exact"] = Query(
        "half_hourly_expanded",
        description="Interval matching: 'half_hourly_expanded' (48 settlement periods) or 'exact' (24 hourly periods)"
    ),
    force_fixture: Optional[bool] = Query(
        None,
        description="Override to force local fixture mode for testing"
    )
):
    """
    Evaluate the latest wind generation forecast available by the day-ahead auction cutoff
    against actual generation for each interval of the specified January 2026 delivery date.
    """
    return service.analyze_delivery_date(
        delivery_date=delivery_date,
        cutoff_hour=cutoff_hour,
        cutoff_day_offset=cutoff_day_offset,
        alignment_mode=alignment_mode,
        force_fixture=force_fixture
    )
