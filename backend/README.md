# UK National Wind Forecast Portal — Backend

FastAPI backend for evaluating January 2026 UK wind generation forecasts against FUELHH outturn. It uses Elexon Insights API endpoints and computes interval alignment and accuracy metrics.

## Run locally (Windows PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://127.0.0.1:8000/docs` and `http://127.0.0.1:8000/api/health`. The health route confirms the app process only; it does not probe Elexon.

## Source-data integrity

- Actuals: `GET /datasets/FUELHH/stream`, filtered to `fuelType == WIND` and the requested settlement date. Where `startTime` is absent, the interval start is derived from settlement date and settlement period.
- Forecasts: raw WINDFOR dataset stream `GET /datasets/WINDFOR/stream`, queried with `publishDateTimeFrom` and `publishDateTimeTo` so historical publication vintages can be considered. Records are then filtered to the requested delivery date and the day-ahead decision cutoff. The latest-forecast endpoint is not used for vintage selection because it may return only the latest available forecast rather than the historical vintage required for a no-look-ahead evaluation.
- The default is **fail closed**: if live data cannot be retrieved, the API returns an upstream error rather than silently substituting local fixtures.
- For an intentional offline/demo run, set `FORCE_FIXTURE_MODE=true` in `.env`, or pass `force_fixture=true` to supported analysis endpoints. Responses then expose `is_fixture_data=true`, `actuals_source=fixture`, `forecast_source=fixture`, and an explicit warning.
- `ALLOW_FIXTURE_FALLBACK=true` is optional and off by default. Enable only if the frontend visibly labels fallback data.
- The bundled fixtures are retained for tests and offline demonstrations. Their source provenance has **not** been independently verified. Do not present fixture-based results as verified live Elexon observations.

## Endpoints

- `GET /api/health` — application health; upstream Elexon status is `not_checked`.
- `GET /api/dates` — January 2026 delivery-date list.
- `GET /api/analysis?delivery_date=2026-01-15` — forecast/outturn analysis. Use `&force_fixture=true` for intentional fixture testing.
- `GET /api/vintages/compare?delivery_date=2026-01-15` — eligible forecast-vintage series.

## Tests

From `backend/`: `python -m pytest -q`

## Important interpretation notes

- The 11:00 UTC D-1 cutoff is a configurable modelling assumption in this app, not a claim that it is the universal auction deadline for every UK electricity market product.
- The forecast selected is the latest eligible record per delivery interval; a single `selected_vintage_publish_time` is the latest timestamp among selected records and does not guarantee every interval came from one complete vintage.
- Hourly WINDFOR values are expanded to both half-hourly settlement periods only in `half_hourly_expanded` mode.
