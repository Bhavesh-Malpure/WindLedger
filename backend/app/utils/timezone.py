from datetime import datetime, timezone, date, timedelta
from typing import Union
from dateutil import parser as date_parser

def parse_utc_iso(dt_input: Union[str, datetime]) -> datetime:
    """Parse an ISO timestamp or datetime and guarantee timezone-aware UTC datetime."""
    if isinstance(dt_input, datetime):
        if dt_input.tzinfo is None:
            return dt_input.replace(tzinfo=timezone.utc)
        return dt_input.astimezone(timezone.utc)
    
    # String input
    dt = date_parser.parse(dt_input)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt

def format_utc_iso(dt: datetime) -> str:
    """Format datetime to standard ISO8601 UTC string with trailing 'Z'."""
    utc_dt = parse_utc_iso(dt)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def get_cutoff_datetime(
    delivery_date: Union[date, str],
    cutoff_hour: int = 11,
    cutoff_day_offset: int = 1
) -> datetime:
    """
    Calculate the day-ahead decision cutoff in UTC.
    For delivery date D, cutoff is typically at (D - cutoff_day_offset) at cutoff_hour:00:00 UTC.
    Example: Delivery 2026-01-15 -> Cutoff 2026-01-14 11:00:00 UTC.
    Example boundary: Delivery 2026-01-01 -> Cutoff 2025-12-31 11:00:00 UTC.
    """
    if isinstance(delivery_date, str):
        delivery_date = date.fromisoformat(delivery_date)
    
    cutoff_date = delivery_date - timedelta(days=cutoff_day_offset)
    return datetime(
        cutoff_date.year,
        cutoff_date.month,
        cutoff_date.day,
        cutoff_hour,
        0,
        0,
        tzinfo=timezone.utc
    )

def is_in_january_2026(target_date: Union[date, str]) -> bool:
    """Check if date falls strictly within January 2026."""
    if isinstance(target_date, str):
        try:
            target_date = date.fromisoformat(target_date)
        except ValueError:
            return False
    return target_date.year == 2026 and target_date.month == 1
