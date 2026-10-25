from fastapi import HTTPException, status
from typing import Optional, Any, Dict

class ElexonAPIError(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_502_BAD_GATEWAY):
        super().__init__(status_code=status_code, detail=f"Elexon upstream error: {detail}")

class DataNotFoundError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class InvalidDateRangeError(HTTPException):
    def __init__(self, detail: str = "Requested delivery date is outside of January 2026 scope"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class CutoffViolationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
