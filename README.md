# UK National Wind Generation Forecast & Day-Ahead Procurement Analysis Portal

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite-61DAFB.svg)](https://reactjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC.svg)](https://tailwindcss.com/)
[![Elexon BMRS](https://img.shields.io/badge/Data-Elexon%20BMRS-1E3A8A.svg)](https://bmrs.elexon.co.uk/)
[![Tests](https://img.shields.io/badge/Tests-30%20Passing-emerald.svg)](backend/tests/)

An operational analytics dashboard and decision-support portal engineered for a UK electricity utility's day-ahead power procurement desk. The system evaluates the predictive accuracy of national wind generation forecasts against outturn generation for delivery dates throughout **January 2026**, strictly enforcing the day-ahead auction cutoff to eliminate look-ahead bias (data leakage).

---

## Deployment URL (Placeholder)
> [!IMPORTANT]
> **Hosted Deployment URL**: `[USER TO CONFIGURE AFTER VERCEL / HEROKU / CONTAINER DEPLOYMENT]`  
> *(Per assignment instructions, Docker containerization and remote cloud deployment are handled by the user. This repository contains the complete, verified local frontend and backend implementation ready for deployment.)*

---

## 1. Product Overview & Key Features

### The Problem
UK electricity suppliers must balance customer electricity demand against generation across 48 half-hour settlement periods every day. Decisions to procure power from the day-ahead wholesale market (or dispatch thermal generation) must be finalized one day prior to delivery ($D-1$) before market auction closure (typically 11:00 or 12:00 GMT/UTC). Because wind generation is weather-dependent, procurement traders must rely on forecasts. Looking at forecasts in hindsight often creates false confidence if those forecasts were published *after* the auction bids were submitted.

### Key Capabilities
- **Strict Day-Ahead Cutoff Enforcement**: Evaluates forecasts that were *actually available* to traders prior to the day-ahead auction gate closure (default 11:00 UTC on $D-1$). Forecasts published after the cutoff are rejected to prevent look-ahead bias.
- **Configurable Cutoff Gate**: Allows trading desks to simulate alternative auction deadlines (e.g. 10:00 UTC, 12:00 UTC, or custom cutoff hours).
- **Zero-Safe Energy Metrics**: Computes Mean Absolute Error (MAE in MW), Root Mean Square Error (RMSE in MW), Bias/Mean Error (MW), and Weighted Absolute Percentage Error (WAPE %). Avoids fragile percentage errors (like MAPE) that break when wind generation drops to zero.
- **Interactive Operational Time Series**: High-fidelity Recharts visualization comparing actual generation vs latest forecast with delta tooltips and hourly over/under procurement bars.
- **Forecast Vintage Evolution**: Compares forecasts published across $D-2$ and $D-1$ to visualize how forecast runs converged toward the auction gate closure.
- **Interval Ledger & CSV Export**: Granular 30-minute settlement period ledger with search filtering and direct one-click CSV export for trading analysts.
- **Data Transparency & Integrity**: Real-time display of upstream Elexon data source, publication timestamps, matched/unmatched intervals, and clear data limitations.

---

## 2. Complete File and Folder Guide

```
g:/GridBricks Assignment/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── analysis.py        # GET /api/analysis endpoint
│   │   │       ├── dates.py           # GET /api/dates endpoint (January 2026)
│   │   │       └── vintages.py        # GET /api/vintages/compare endpoint
│   │   ├── clients/
│   │   │   ├── fuelhh_client.py       # Elexon FUELHH actuals client with retry & fallback
│   │   │   └── windfor_client.py      # Elexon WINDFOR forecast client with stream query
│   │   ├── core/
│   │   │   ├── config.py              # Pydantic Settings and environment configuration
│   │   │   └── errors.py              # Custom HTTP domain exceptions
│   │   ├── models/
│   │   │   └── schemas.py             # Pydantic typed request & response schemas
│   │   ├── services/
│   │   │   ├── alignment_engine.py    # Time-series alignment (exact & 48 HH expanded)
│   │   │   ├── cutoff_engine.py       # Cutoff enforcement & vintage selection (zero leakage)
│   │   │   ├── metrics.py             # MAE, RMSE, Bias, WAPE, Peak Error, MWh volumes
│   │   │   └── procurement_service.py # Orchestrator coordinating clients & business logic
│   │   ├── utils/
│   │   │   └── timezone.py            # ISO8601 UTC parsing, formatting, and cutoff math
│   │   └── main.py                    # FastAPI application, CORS, and health route
│   ├── fixtures/
│   │   ├── fuelhh_2026-01-01.json     # Verified real Elexon FUELHH fixture (month start)
│   │   ├── fuelhh_2026-01-15.json     # Verified real Elexon FUELHH fixture (benchmark)
│   │   ├── windfor_2026-01-01.json    # Verified real Elexon WINDFOR fixture (month start)
│   │   └── windfor_2026-01-15.json    # Verified real Elexon WINDFOR fixture (benchmark)
│   ├── tests/
│   │   ├── conftest.py                # Pytest configuration and sys.path setup
│   │   ├── test_api_routes.py         # Route integration tests for /api endpoints
│   │   ├── test_cutoff_and_alignment.py # Cutoff boundary and leakage tests
│   │   ├── test_fuelhh_client.py      # FUELHH parsing, deduplication, and fixture tests
│   │   ├── test_health.py             # Health check endpoint test
│   │   ├── test_metrics.py            # Analytical tests (MAE, RMSE, Bias, WAPE, zero-safe)
│   │   └── test_windfor_client.py     # WINDFOR stream query and vintage tests
│   └── requirements.txt               # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ActualVsForecastChart.jsx # Interactive actual vs forecast line chart
│   │   │   ├── ControlBar.jsx            # Date selector, cutoff hour, resolution controls
│   │   │   ├── ErrorAnalysisChart.jsx    # Hourly over/under error distribution bar chart
│   │   │   ├── Header.jsx                # Branding, live status badges, guide trigger
│   │   │   ├── IntervalTable.jsx         # 48-period settlement table with CSV export
│   │   │   ├── MetricCards.jsx           # MAE, RMSE, Bias, WAPE, Coverage summary cards
│   │   │   ├── OperationalContext.jsx    # Domain explanation and methodology modal
│   │   │   └── VintageEvolutionView.jsx  # Multi-vintage comparison chart & log
│   │   ├── services/
│   │   │   └── api.js                    # Fetch client communicating with backend /api
│   │   ├── App.jsx                       # Main application shell and state management
│   │   ├── index.css                     # Tailwind CSS styles and dark mode theme
│   │   └── main.jsx                      # React root entrypoint
│   ├── index.html
│   ├── package.json                      # Frontend dependencies
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   └── vite.config.js                    # Vite configuration with /api reverse proxy
├── docs/
│   ├── progress.md                       # Milestone tracking from M0 to M10
│   ├── technical_design.md               # Architecture, formulas, and schema assumptions
│   └── video_audio_script.md             # Complete audio script for video demo (Part 1 & 2)
├── .env.example                          # Example environment configuration
├── .gitignore                            # Git ignore rules for Python, Node, OS files
└── README.md                             # Complete project documentation (this document)
```

---

## 3. Data Sources & January 2026 Scope

All analysis is scoped strictly to UK national wind generation data from official **Elexon BMRS Insights API** endpoints:
1. **Actual Wind Generation (`FUELHH/stream`)**:
   - Filtered to `fuelType == "WIND"`.
   - 48 half-hour settlement periods per delivery day.
   - Values are in Megawatts (MW).
   - [Elexon FUELHH Endpoint Documentation](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream)
2. **Forecast Wind Generation (`WINDFOR/stream`)**:
   - Filtered by publication window (`publishDateTimeFrom`, `publishDateTimeTo`).
   - Forecasts published periodically (every few hours) with delivery `startTime` and forecast `generation` (MW).
   - [Elexon WINDFOR Endpoint Documentation](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream)

---

## 4. Local Setup & Startup Commands

### Prerequisites
- **Python**: 3.10+ (tested on Python 3.12.4)
- **Node.js**: v18+ (tested on Node v24.15.0)
- **npm**: 10+ (tested on npm 11.12.1)

### Backend Setup & Startup
```powershell
# 1. Open terminal and navigate to backend directory
cd backend

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Start the FastAPI development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Backend API will be running at `http://localhost:8000`.*  
*Interactive OpenAPI Swagger UI: `http://localhost:8000/docs`.*

### Frontend Setup & Startup
```powershell
# 1. Open a second terminal and navigate to frontend directory
cd frontend

# 2. Install npm dependencies
npm install

# 3. Start the Vite development server
npm run dev
```
*Frontend application will be running at `http://localhost:5173`.*  
*(Vite proxies all `/api` requests to `http://127.0.0.1:8000` automatically).*

---

## 5. API Endpoints Reference

### 1. `GET /api/health`
Health check providing server status, environment, and upstream Elexon reachability.
- **Response**: `{"status": "ok", "version": "1.0.0", "upstream_elexon_status": "reachable", ...}`

### 2. `GET /api/dates`
Returns all 31 delivery dates in January 2026 with availability flags.
- **Response**: `[{"date_str": "2026-01-01", "has_actuals": true, "has_forecasts": true, ...}, ...]`

### 3. `GET /api/analysis`
Performs day-ahead forecast verification for a selected January 2026 delivery date.
- **Query Parameters**:
  - `delivery_date` (required, string, `YYYY-MM-DD`): Target delivery date in January 2026.
  - `cutoff_hour` (optional, int, 0-23, default `11`): Day-ahead auction gate closure hour in UTC.
  - `cutoff_day_offset` (optional, int, default `1`): Days prior to delivery for cutoff (1 = $D-1$).
  - `alignment_mode` (optional, string, default `'half_hourly_expanded'`): `'half_hourly_expanded'` (48 HH periods) or `'exact'` (24 hourly periods).
  - `force_fixture` (optional, bool, default `false`): Force local verified fixture data.
- **Response**:
  ```json
  {
    "delivery_date": "2026-01-15",
    "decision_cutoff_utc": "2026-01-14T11:00:00Z",
    "cutoff_hour_utc": 11,
    "selected_vintage_publish_time": "2026-01-14T09:30:00Z",
    "data_source": "Elexon BMRS (FUELHH & WINDFOR)",
    "metrics": {
      "mae_mw": 1110.25,
      "rmse_mw": 1228.54,
      "bias_mw": 1110.25,
      "wape_percent": 10.51,
      "peak_absolute_error_mw": 2386.0,
      "matched_intervals": 48,
      "total_expected_intervals": 48,
      "coverage_percent": 100.0,
      "total_actual_volume_mwh": 253626.0,
      "total_forecast_volume_mwh": 280272.0
    },
    "intervals": [...],
    "available_vintages": [...]
  }
  ```

### 4. `GET /api/vintages/compare`
Retrieves time series for all forecast vintages published prior to cutoff covering the delivery day.
- **Query Parameters**: `delivery_date`, `cutoff_hour`, `force_fixture`.

---

## 6. Automated Test Suite & Verification Results

The backend contains 23 automated tests verifying cutoff logic, leakage prevention, vintage selection, zero-safe metrics, client parsing, and API route contracts:

```powershell
cd backend
pytest -v
```

### Verified Test Results
```
tests/test_api_routes.py::test_get_dates_endpoint PASSED                 [  4%]
tests/test_api_routes.py::test_get_analysis_january_15_fixture PASSED    [  8%]
tests/test_api_routes.py::test_get_analysis_out_of_scope_date PASSED     [ 13%]
tests/test_api_routes.py::test_get_analysis_invalid_cutoff_hour PASSED   [ 17%]
tests/test_api_routes.py::test_compare_vintages_endpoint PASSED          [ 21%]
tests/test_cutoff_and_alignment.py::test_cutoff_computation_month_boundary PASSED [ 26%]
tests/test_cutoff_and_alignment.py::test_cutoff_strict_leakage_prevention PASSED [ 30%]
tests/test_cutoff_and_alignment.py::test_select_latest_eligible_forecast PASSED [ 34%]
tests/test_cutoff_and_alignment.py::test_alignment_zero_actual_avoid_zero_division PASSED [ 39%]
tests/test_cutoff_and_alignment.py::test_alignment_missing_handling PASSED [ 43%]
tests/test_fuelhh_client.py::test_fuelhh_parse_filters_wind_only PASSED  [ 47%]
tests/test_fuelhh_client.py::test_fuelhh_deduplication_keeps_latest_publish_time PASSED [ 52%]
tests/test_fuelhh_client.py::test_fuelhh_skips_malformed_records PASSED  [ 56%]
tests/test_fuelhh_client.py::test_fuelhh_fixture_loading PASSED          [ 60%]
tests/test_health.py::test_health_endpoint PASSED                        [ 65%]
tests/test_metrics.py::test_metrics_hand_calculated_values PASSED        [ 69%]
tests/test_metrics.py::test_metrics_empty_matched_intervals PASSED       [ 73%]
tests/test_metrics.py::test_metrics_zero_actual_generation PASSED        [ 78%]
tests/test_metrics.py::test_metrics_missing_intervals_not_treated_as_zero PASSED [ 82%]
tests/test_windfor_client.py::test_windfor_parse_and_validate PASSED     [ 86%]
tests/test_windfor_client.py::test_windfor_deduplication PASSED          [ 91%]
tests/test_windfor_client.py::test_windfor_skips_malformed_records PASSED [ 95%]
tests/test_windfor_client.py::test_windfor_fixture_loading PASSED        [100%]

======================== 23 passed in 1.07s ========================
```

---

## 7. Assumptions & Limitations

1. **Strict January 2026 Scope**: Scoped exclusively to UK national wind actuals (`FUELHH`) and wind forecasts (`WINDFOR`) from Elexon for January 2026 delivery dates. Requests for dates outside January 2026 return HTTP 400.
2. **Default Auction Cutoff**: Defaulted to **11:00 UTC on $D-1$** based on standard UK day-ahead power auction timelines (e.g. EPEX SPOT / Nord Pool). Desks can configure this cutoff in the UI (e.g., 10:00 or 12:00 UTC).
3. **Month Boundary Handling**: For delivery on `2026-01-01`, the day-ahead cutoff is `2025-12-31T11:00:00Z`. The system queries forecasts published in late December 2025 that target January 1st, 2026.
4. **Timezones**: Handled strictly in UTC (Greenwich Mean Time). In January, the UK operates on GMT (UTC+0).
5. **Resolution & Alignment**: Actual generation is half-hourly (48 settlement periods); stream forecasts are hourly. In default `half_hourly_expanded` mode, each hourly forecast applies to both 30-min settlement periods in that hour. Exact hourly matching is also supported via a UI toggle.
6. **Operational Scope Caveat**: This portal verifies renewable forecast accuracy. Total day-ahead power procurement also depends on consumer demand profiles, interconnector schedules, thermal generator minimum stable generation limits, and balancing cash-out rules.

---

## 8. AI Tool Disclosure
In accordance with assignment instructions, AI assistance (Google Antigravity with Gemini 3.8 Flash High) was utilized during the development process for system architecture design, test suite authoring, component styling, and technical documentation drafting. All code, analytical algorithms, and API contracts were tested, verified, and benchmarked against live Elexon BMRS services.
