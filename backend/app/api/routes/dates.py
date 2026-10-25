from fastapi import APIRouter
from typing import List
from app.models.schemas import DeliveryDateStatus
from app.services.procurement_service import ProcurementAnalysisService

router = APIRouter(prefix="/dates", tags=["Dates"])
service = ProcurementAnalysisService()

@router.get("", response_model=List[DeliveryDateStatus])
def get_available_dates():
    """
    List all supported delivery dates in January 2026 for the procurement analysis portal.
    """
    return service.get_january_2026_dates()
