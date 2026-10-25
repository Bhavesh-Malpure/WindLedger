import pytest
from datetime import datetime, timezone, date
from app.clients.windfor_client import WindforClient
from app.models.schemas import WindforRecord

@pytest.fixture
def client():
    return WindforClient()

def test_windfor_parse_and_validate(client):
    raw_data = [
        {
            "dataset": "WINDFOR",
            "publishTime": "2025-12-31T09:30:00Z",
            "startTime": "2026-01-01T00:00:00Z",
            "generation": 14500.0
        },
        {
            "dataset": "WINDFOR",
            "publishTime": "2025-12-31T09:30:00Z",
            "startTime": "2026-01-01T01:00:00Z",
            "generation": 14200.0
        },
        # Record for Jan 2nd should be filtered out when targeting Jan 1st
        {
            "dataset": "WINDFOR",
            "publishTime": "2025-12-31T09:30:00Z",
            "startTime": "2026-01-02T00:00:00Z",
            "generation": 12000.0
        }
    ]
    records = client._parse_and_validate(raw_data, delivery_date="2026-01-01")
    assert len(records) == 2
    assert records[0].start_time == datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    assert records[0].generation == 14500.0
    assert records[1].start_time == datetime(2026, 1, 1, 1, 0, tzinfo=timezone.utc)

def test_windfor_deduplication(client):
    raw_data = [
        {
            "dataset": "WINDFOR",
            "publishTime": "2025-12-31T09:30:00Z",
            "startTime": "2026-01-01T00:00:00Z",
            "generation": 14500.0
        },
        {
            "dataset": "WINDFOR",
            "publishTime": "2025-12-31T09:30:00Z",
            "startTime": "2026-01-01T00:00:00Z",
            "generation": 14500.0  # Exact duplicate
        }
    ]
    records = client._parse_and_validate(raw_data, delivery_date="2026-01-01")
    assert len(records) == 1

def test_windfor_skips_malformed_records(client):
    raw_data = [
        {"dataset": "WINDFOR"},  # missing times and generation
        {"dataset": "WINDFOR", "publishTime": "invalid", "startTime": "2026-01-01T00:00:00Z", "generation": 100},
        {"dataset": "WINDFOR", "publishTime": "2025-12-31T09:30:00Z", "startTime": "2026-01-01T00:00:00Z", "generation": "bad"},
        {
            "dataset": "WINDFOR",
            "publishTime": "2025-12-31T09:30:00Z",
            "startTime": "2026-01-01T00:00:00Z",
            "generation": 15000.0
        }
    ]
    records = client._parse_and_validate(raw_data, delivery_date="2026-01-01")
    assert len(records) == 1
    assert records[0].generation == 15000.0

def test_windfor_fixture_loading(client):
    cutoff = datetime(2026, 1, 14, 11, 0, tzinfo=timezone.utc)
    records, is_fixture = client.fetch_forecasts_for_delivery_date(
        delivery_date="2026-01-15",
        cutoff_datetime=cutoff,
        lookback_days=2,
        force_fixture=True
    )
    assert is_fixture is True
    assert len(records) > 0
    # Every record should have publish_time <= cutoff
    for r in records:
        assert r.publish_time <= cutoff
        assert r.start_time.strftime("%Y-%m-%d") == "2026-01-15"



def test_windfor_uses_raw_dataset_endpoint_and_publication_time_parameters(client, monkeypatch):
    import httpx
    assert client.endpoint.endswith("/datasets/WINDFOR/stream")
    captured = {}

    class FakeResponse:
        status_code = 200
        def json(self):
            return []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def get(self, url, params=None, headers=None):
            captured["url"] = url
            captured["params"] = params
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)
    client._fetch_live(
        datetime(2026, 1, 13, 11, tzinfo=timezone.utc),
        datetime(2026, 1, 14, 11, tzinfo=timezone.utc),
        date(2026, 1, 15),
    )
    assert captured["params"]["publishDateTimeFrom"] == "2026-01-13T11:00:00Z"
    assert captured["params"]["publishDateTimeTo"] == "2026-01-14T11:00:00Z"


def test_windfor_does_not_silently_fallback_when_live_fails(client, monkeypatch):
    from app.core.config import settings
    from app.core.errors import ElexonAPIError

    monkeypatch.setattr(settings, "allow_fixture_fallback", False)
    monkeypatch.setattr(client, "_fetch_live", lambda *args: (_ for _ in ()).throw(RuntimeError("network down")))
    with pytest.raises(ElexonAPIError) as exc:
        client.fetch_forecasts_for_delivery_date(
            delivery_date="2026-01-15",
            cutoff_datetime=datetime(2026, 1, 14, 11, tzinfo=timezone.utc),
            force_fixture=False,
        )
    assert exc.value.status_code == 502
    assert "No fixture fallback was used" in exc.value.detail


def test_windfor_uses_settlement_period_as_delivery_key_when_present(client):
    raw_data = [{
        "dataset": "WINDFOR",
        "publishTime": "2026-01-14T10:30:00Z",
        "startTime": "2026-01-14T10:30:00Z",
        "settlementDate": "2026-01-15",
        "settlementPeriod": 3,
        "generation": 12345
    }]
    records = client._parse_and_validate(raw_data, delivery_date="2026-01-15")
    assert len(records) == 1
    assert records[0].start_time == datetime(2026, 1, 15, 1, 0, tzinfo=timezone.utc)
