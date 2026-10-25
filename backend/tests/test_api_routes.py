import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_dates_endpoint():
    response = client.get("/api/dates")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 31
    assert data[0]["date_str"] == "2026-01-01"
    assert data[-1]["date_str"] == "2026-01-31"

def test_get_analysis_january_15_fixture():
    response = client.get(
        "/api/analysis",
        params={
            "delivery_date": "2026-01-15",
            "cutoff_hour": 11,
            "cutoff_day_offset": 1,
            "alignment_mode": "half_hourly_expanded",
            "force_fixture": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    
    assert data["delivery_date"] == "2026-01-15"
    assert data["cutoff_hour_utc"] == 11
    assert "decision_cutoff_utc" in data
    
    # Check metrics
    metrics = data["metrics"]
    assert metrics["matched_intervals"] > 0
    assert metrics["mae_mw"] is not None
    assert metrics["rmse_mw"] is not None
    assert metrics["bias_mw"] is not None
    assert metrics["wape_percent"] is not None
    
    # Check intervals
    intervals = data["intervals"]
    assert len(intervals) == 48
    assert intervals[0]["settlement_period"] == 1
    assert intervals[-1]["settlement_period"] == 48
    
    # Check vintages
    vintages = data["available_vintages"]
    assert len(vintages) > 0

def test_get_analysis_out_of_scope_date():
    response = client.get(
        "/api/analysis",
        params={
            "delivery_date": "2026-02-01",  # February is out of scope!
            "force_fixture": True
        }
    )
    assert response.status_code == 400
    assert "outside January 2026" in response.json()["detail"]

def test_get_analysis_invalid_cutoff_hour():
    response = client.get(
        "/api/analysis",
        params={
            "delivery_date": "2026-01-15",
            "cutoff_hour": 25  # Must be 0-23
        }
    )
    assert response.status_code == 422

def test_compare_vintages_endpoint():
    response = client.get(
        "/api/vintages/compare",
        params={
            "delivery_date": "2026-01-15",
            "cutoff_hour": 11,
            "force_fixture": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["delivery_date"] == "2026-01-15"
    assert "vintages" in data
    assert len(data["vintages"]) > 0


def test_get_analysis_exact_mode():
    response = client.get(
        "/api/analysis",
        params={
            "delivery_date": "2026-01-15",
            "alignment_mode": "exact",
            "force_fixture": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    metrics = data["metrics"]
    assert metrics["matched_intervals"] == 24
    assert metrics["total_expected_intervals"] == 24
    assert metrics["coverage_percent"] == 100.0
    assert metrics["mae_mw"] == 1093.62
    assert metrics["bias_mw"] == 1093.62

def test_get_analysis_month_boundary_rollover():
    response = client.get(
        "/api/analysis",
        params={
            "delivery_date": "2026-01-01",
            "cutoff_hour": 11,
            "force_fixture": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["delivery_date"] == "2026-01-01"
    # Cutoff must roll over to December 31, 2025 at 11:00 UTC
    assert data["decision_cutoff_utc"] == "2025-12-31T11:00:00Z"
    assert data["metrics"]["matched_intervals"] == 48

def test_get_analysis_custom_cutoff_hour():
    response = client.get(
        "/api/analysis",
        params={
            "delivery_date": "2026-01-15",
            "cutoff_hour": 14,
            "force_fixture": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["cutoff_hour_utc"] == 14
    assert data["decision_cutoff_utc"] == "2026-01-14T14:00:00Z"

def test_get_analysis_invalid_date_format():
    response = client.get(
        "/api/analysis",
        params={
            "delivery_date": "not-a-date"
        }
    )
    assert response.status_code == 422
