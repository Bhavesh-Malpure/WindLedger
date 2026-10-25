import pytest
from datetime import datetime, timezone, date
from app.clients.fuelhh_client import FuelHHClient
from app.models.schemas import FuelHHRecord

@pytest.fixture
def client():
    return FuelHHClient()

def test_fuelhh_parse_filters_wind_only(client):
    raw_data = [
        {
            "dataset": "FUELHH",
            "publishTime": "2026-01-01T01:00:00Z",
            "startTime": "2026-01-01T00:00:00Z",
            "settlementDate": "2026-01-01",
            "settlementPeriod": 1,
            "fuelType": "BIOMASS",
            "generation": 1200
        },
        {
            "dataset": "FUELHH",
            "publishTime": "2026-01-01T01:00:00Z",
            "startTime": "2026-01-01T00:00:00Z",
            "settlementDate": "2026-01-01",
            "settlementPeriod": 1,
            "fuelType": "WIND",
            "generation": 8500.5
        },
        {
            "dataset": "FUELHH",
            "publishTime": "2026-01-01T01:30:00Z",
            "startTime": "2026-01-01T00:30:00Z",
            "settlementDate": "2026-01-01",
            "settlementPeriod": 2,
            "fuelType": "CCGT",
            "generation": 5000
        }
    ]
    records = client._parse_and_validate(raw_data)
    assert len(records) == 1
    assert records[0].fuel_type == "WIND"
    assert records[0].generation == 8500.5
    assert records[0].settlement_period == 1

def test_fuelhh_deduplication_keeps_latest_publish_time(client):
    raw_data = [
        {
            "dataset": "FUELHH",
            "publishTime": "2026-01-01T01:00:00Z",
            "startTime": "2026-01-01T00:00:00Z",
            "settlementDate": "2026-01-01",
            "settlementPeriod": 1,
            "fuelType": "WIND",
            "generation": 8000
        },
        {
            "dataset": "FUELHH",
            "publishTime": "2026-01-01T02:00:00Z",  # Later publish time
            "startTime": "2026-01-01T00:00:00Z",
            "settlementDate": "2026-01-01",
            "settlementPeriod": 1,
            "fuelType": "WIND",
            "generation": 8200  # Updated measurement
        }
    ]
    records = client._parse_and_validate(raw_data)
    assert len(records) == 1
    assert records[0].generation == 8200
    assert records[0].publish_time == datetime(2026, 1, 1, 2, 0, tzinfo=timezone.utc)

def test_fuelhh_skips_malformed_records(client):
    raw_data = [
        {"fuelType": "WIND"},  # Missing startTime, publishTime, generation
        {"fuelType": "WIND", "startTime": "invalid-time", "generation": 100},
        {
            "dataset": "FUELHH",
            "publishTime": "2026-01-01T01:00:00Z",
            "startTime": "2026-01-01T00:00:00Z",
            "settlementDate": "2026-01-01",
            "settlementPeriod": 1,
            "fuelType": "WIND",
            "generation": "not-a-number"
        },
        {
            "dataset": "FUELHH",
            "publishTime": "2026-01-01T01:00:00Z",
            "startTime": "2026-01-01T00:00:00Z",
            "settlementDate": "2026-01-01",
            "settlementPeriod": 1,
            "fuelType": "WIND",
            "generation": 9000
        }
    ]
    records = client._parse_and_validate(raw_data)
    assert len(records) == 1
    assert records[0].generation == 9000

def test_fuelhh_fixture_loading(client):
    # Test loading from backend/fixtures/fuelhh_2026-01-01.json
    records, is_fixture = client.fetch_actuals("2026-01-01", force_fixture=True)
    assert is_fixture is True
    assert len(records) == 48  # Complete day of half-hour periods
    assert records[0].settlement_period == 1
    assert records[-1].settlement_period == 48
    assert records[0].start_time.isoformat() == "2026-01-01T00:00:00+00:00"


def test_fuelhh_derives_start_time_from_settlement_period_when_missing(client):
    raw_data = [{
        "dataset": "FUELHH",
        "publishTime": "2026-01-01T02:00:00Z",
        "settlementDate": "2026-01-01",
        "settlementPeriod": 2,
        "fuelType": "WIND",
        "generation": 9000
    }]
    records = client._parse_and_validate(raw_data)
    assert len(records) == 1
    assert records[0].start_time == datetime(2026, 1, 1, 0, 30, tzinfo=timezone.utc)


def test_fuelhh_does_not_silently_fallback_when_live_fails(client, monkeypatch):
    from app.core.config import settings
    from app.core.errors import ElexonAPIError

    monkeypatch.setattr(settings, "allow_fixture_fallback", False)
    monkeypatch.setattr(client, "_fetch_live", lambda date_str: (_ for _ in ()).throw(RuntimeError("network down")))
    with pytest.raises(ElexonAPIError) as exc:
        client.fetch_actuals("2026-01-15", force_fixture=False)
    assert exc.value.status_code == 502
    assert "No fixture fallback was used" in exc.value.detail
