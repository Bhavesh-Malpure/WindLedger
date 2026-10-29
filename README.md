# WindLedger --- UK Wind Forecast & Day-Ahead Procurement Analysis

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite-61DAFB.svg)](https://react.dev/)
[![Tailwind
CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC.svg)](https://tailwindcss.com/)
[![Data](https://img.shields.io/badge/Data-Elexon%20BMRS-1E3A8A.svg)](https://bmrs.elexon.co.uk/)

WindLedger is a web-based analysis portal for comparing UK national
wind-generation forecasts with actual generation for January 2026
delivery dates. It helps users review forecast error, forecast
publication cutoffs, and forecast-vintage changes in a repeatable
workflow.

The project contains a React/Vite frontend and a Python/FastAPI backend.
The backend is designed to retrieve actuals and forecasts from the
Elexon BMRS API and provides configurable fixture-mode behavior for
controlled testing.

## Deployed application

-   **Frontend:** https://windledger-frontend.onrender.com
-   **Backend health endpoint:**
    https://windledger-backend.onrender.com/api/health
-   **Backend API documentation:**
    https://windledger-backend.onrender.com/docs

The health endpoint confirms that the API process responds; it does
**not** independently verify upstream Elexon connectivity. Check the
analysis response's source and warning fields when interpreting results.

## Features

-   **Day-ahead cutoff handling:** Select a delivery date and cutoff
    settings. The backend selects forecast vintages eligible before the
    configured cutoff to help prevent look-ahead bias.
-   **Configurable analysis settings:** Supports cutoff-hour and
    cutoff-day-offset parameters, plus interval-alignment modes.
-   **Forecast accuracy metrics:** Reports metrics including MAE, RMSE,
    bias, WAPE, peak absolute error, interval coverage, and
    actual/forecast energy volumes when available.
-   **Actual-versus-forecast visualization:** Displays a time-series
    comparison of actual generation and forecast generation.
-   **Forecast-vintage comparison:** Supports reviewing forecasts
    published at different times before the cutoff.
-   **Settlement-interval ledger:** Presents interval-level comparison
    data; CSV export is available through the frontend when exposed by
    the current UI.
-   **Data-source transparency:** The API response can report
    data-source information, fixture status, and warnings so users can
    distinguish analysis modes.
-   **API endpoints:** Provides endpoints for available dates, analysis,
    and forecast-vintage comparison.

## Architecture

``` text
Browser
  |
  v
React + Vite frontend (Render Static Site)
  |
  | HTTPS requests to /api endpoints
  v
FastAPI backend (Render web service / Docker)
  |
  +--> Elexon BMRS API clients
  |      +--> FUELHH actual generation
  |      +--> WINDFOR forecast generation
  |
  +--> Cutoff and vintage selection
  +--> Time-series alignment
  +--> Metrics calculation
  +--> JSON API response
```

The frontend and backend are deployed separately. The frontend's API
service points to the deployed backend URL, and the backend CORS
configuration must allow the frontend origin.

## Repository structure

``` text
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── analysis.py          # Analysis API route
│   │   │       ├── dates.py             # Available delivery dates route
│   │   │       └── vintages.py          # Forecast-vintage comparison route
│   │   ├── clients/
│   │   │   ├── fuelhh_client.py         # Actual-generation API client
│   │   │   └── windfor_client.py        # Forecast-generation API client
│   │   ├── core/
│   │   │   ├── config.py                # Settings and environment configuration
│   │   │   └── errors.py                # Domain/API error handling
│   │   ├── models/
│   │   │   └── schemas.py               # Typed request/response models
│   │   ├── services/
│   │   │   ├── alignment_engine.py      # Interval alignment
│   │   │   ├── cutoff_engine.py         # Cutoff and eligible-vintage selection
│   │   │   ├── metrics.py               # Forecast evaluation metrics
│   │   │   └── procurement_service.py   # Analysis orchestration
│   │   ├── utils/
│   │   │   └── timezone.py              # UTC/time handling helpers
│   │   └── main.py                      # FastAPI app, CORS and health endpoint
│   ├── fixtures/                        # Fixture datasets used in configured test/fallback modes
│   ├── tests/                            # Backend unit and integration tests
│   ├── Dockerfile                        # Backend container definition
│   └── requirements.txt                 # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/                  # Dashboard and chart components
│   │   ├── services/
│   │   │   └── api.js                   # Frontend-to-backend API client
│   │   ├── App.jsx                       # Main application and UI state
│   │   ├── index.css                     # Global styles
│   │   └── main.jsx                      # React entry point
│   ├── index.html
│   ├── package.json                     # Frontend scripts and dependencies
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   └── vite.config.js                   # Vite development configuration
├── docs/
│   ├── progress.md                      # Development milestone notes
│   ├── technical_design.md              # Technical design and methodology
│   └── video_audio_script.md            # Demo/technical walkthrough script
├── .env.example                         # Example environment settings, if included
├── .gitignore
└── README.md
```

> The tree describes the main application files. Exact contents may vary
> slightly as the project evolves.

## Data sources and scope

The application is scoped to **January 1--31, 2026** delivery dates for
UK national wind generation.

1.  **Actual generation --- Elexon BMRS FUELHH**
    -   Uses the FUELHH dataset and filters for wind generation.
    -   Actual generation is represented in MW and is aligned with
        delivery intervals.
    -   [FUELHH stream
        documentation](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream)
2.  **Forecast generation --- Elexon BMRS WINDFOR**
    -   Uses the WINDFOR dataset and forecast publication timestamps.
    -   Forecast vintage selection considers the configured day-ahead
        cutoff.
    -   [WINDFOR stream
        documentation](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream)

The application uses UTC for cutoff calculations. In the default
configuration, the cutoff is 11:00 UTC on the day before delivery
(`D-1`). This is an application default and should be checked against
the market process being modelled before operational use.

### Alignment and metrics

The default `half_hourly_expanded` mode aligns hourly forecasts to
half-hourly settlement intervals by applying each hourly forecast value
to both half-hour periods in that hour. The `exact` mode supports
exact-time matching where applicable.

The analysis may include:

-   **MAE (MW):** Mean absolute forecast error.
-   **RMSE (MW):** Root mean squared error, which weights larger errors
    more heavily.
-   **Bias (MW):** Mean signed error; interpretation depends on the sign
    convention returned by the API.
-   **WAPE (%):** Weighted absolute percentage error, subject to the
    API's zero-denominator handling.
-   **Peak absolute error (MW):** Largest absolute interval error.
-   **Coverage:** Matched intervals relative to expected intervals.
-   **Energy volumes (MWh):** Actual and forecast volume totals when
    supplied by the analysis response.

Forecast accuracy is only one input to procurement decisions. Demand,
market prices, interconnector flows, other generation, balancing costs,
and risk limits are outside the scope of this wind-forecast comparison
alone.

## Run locally

### Prerequisites

-   Python 3.10 or later
-   Node.js 18 or later
-   npm
-   Git (optional, for cloning)

### 1. Get the code

``` bash
git clone <YOUR_PUBLIC_REPOSITORY_URL>
cd <REPOSITORY_DIRECTORY>
```

Replace the placeholders with the URL and directory name of the
submitted public repository.

### 2. Start the backend

From the repository root:

**Windows PowerShell / Command Prompt**

``` powershell
cd backend
python -m venv .venv
# PowerShell:
.\.venv\Scripts\Activate.ps1
# Command Prompt:
.\.venv\Scripts\activate.bat

python -m pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend is available at `http://localhost:8000`. Interactive API
documentation is at `http://localhost:8000/docs`.

If activation is restricted by PowerShell policy, use Command Prompt or
run the Python commands using the virtual environment's interpreter
directly.

### 3. Start the frontend

Open a second terminal from the repository root:

``` bash
cd frontend
npm install
npm run dev
```

Vite normally serves the frontend at `http://localhost:5173`.

For local development, ensure the frontend API configuration targets the
local backend and that the backend CORS origins include the local
frontend origin. The deployed frontend uses the deployed backend URL, so
local and deployed API settings may differ.

## Configuration

Backend settings are defined in `backend/app/core/config.py` and can be
overridden by environment variables supported by Pydantic Settings. The
backend also reads a `.env` file when present.

Relevant settings include:

  -----------------------------------------------------------------------
  Setting                             Purpose
  ----------------------------------- -----------------------------------
  `ELEXON_API_BASE_URL`               Base URL for the Elexon BMRS API

  `ENVIRONMENT`                       Application environment label

  `CORS_ORIGINS`                      Allowed browser origins, according
                                      to the settings format

  `HTTP_TIMEOUT_SECONDS`              Upstream HTTP timeout

  `MAX_RETRIES`                       Retry limit for upstream requests

  `FORCE_FIXTURE_MODE`                Forces fixture data when enabled

  `ALLOW_FIXTURE_FALLBACK`            Controls whether fallback to
                                      fixtures is permitted
  -----------------------------------------------------------------------

Do not commit API credentials, secrets, or environment-specific private
values. If fixture data is returned, treat it as test/demo data and do
not describe it as live upstream data.

## API reference

The base path is `/api`.

### `GET /api/health`

Returns application health information, version, environment, and
fixture-mode configuration. The endpoint does not itself call Elexon to
test upstream connectivity.

Example:

``` bash
curl https://windledger-backend.onrender.com/api/health
```

### `GET /api/dates`

Returns the delivery dates available to the application, with
actuals/forecast availability flags where supplied.

Example:

``` bash
curl https://windledger-backend.onrender.com/api/dates
```

### `GET /api/analysis`

Runs forecast-versus-actual analysis for a delivery date.

Common query parameters:

  -----------------------------------------------------------------------
  Parameter                           Description
  ----------------------------------- -----------------------------------
  `delivery_date`                     Required date in `YYYY-MM-DD`
                                      format; supported scope is January
                                      2026

  `cutoff_hour`                       Cutoff hour in UTC; default is `11`

  `cutoff_day_offset`                 Days before delivery for the
                                      cutoff; default is `1`

  `alignment_mode`                    `half_hourly_expanded` or `exact`,
                                      depending on supported route
                                      validation

  `force_fixture`                     Optional switch to force fixture
                                      data for a request, if enabled by
                                      the API
  -----------------------------------------------------------------------

Example:

``` bash
curl "https://windledger-backend.onrender.com/api/analysis?delivery_date=2026-01-15&cutoff_hour=11&cutoff_day_offset=1&alignment_mode=half_hourly_expanded"
```

Inspect the returned data-source, fixture, warning, coverage, and metric
fields before interpreting results.

### `GET /api/vintages/compare`

Compares eligible forecast vintages for a delivery date, subject to the
cutoff and route parameters.

Example:

``` bash
curl "https://windledger-backend.onrender.com/api/vintages/compare?delivery_date=2026-01-15&cutoff_hour=11"
```

For the full request and response schemas, see the deployed [OpenAPI
documentation](https://windledger-backend.onrender.com/docs).

## Tests

The backend test suite covers areas such as API routes, cutoff and
alignment behavior, client parsing, fixture handling, and metric
calculations.

Run the tests from the repository root:

``` bash
cd backend
python -m pip install -r requirements.txt
pytest -v
```

Use the test output from your current checkout as the source of truth
for the number of tests passing.

## Deployment

The submitted deployment currently uses Render:

-   **Frontend:** Render Static Site, built from the `frontend`
    directory.
-   **Backend:** Render web service built from the `backend` directory's
    Dockerfile.
-   **Frontend API configuration:** `frontend/src/services/api.js`.
-   **Backend CORS configuration:** `backend/app/core/config.py` and the
    middleware setup in `backend/app/main.py`.

For a new deployment, configure the frontend and backend services to
match their respective build settings, set the correct backend API URL
in the frontend, and allow the deployed frontend origin in backend CORS
settings. After deployment, verify the frontend, backend health
endpoint, and an actual analysis request independently.

## Demo video

Add the **unlisted YouTube demo link** here after recording and
uploading the final video. The recording must be no longer than 10
minutes and should contain: 1. A customer-facing portal and analysis
overview (maximum 5 minutes). 2. A technical walkthrough covering
architecture, design, analysis logic, codebase, and development
practices (maximum 5 minutes).

Do not submit this README with the demo-link placeholder still present;
replace this section with the actual unlisted video URL before
submission.

## AI assistance disclosure

AI-assisted tools were used during development and documentation. Review
the final implementation and test results before submission, and ensure
this disclosure accurately reflects the tools and contributions used for
this project.
