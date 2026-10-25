# Technical Design Document: UK Wind Forecast & Day-Ahead Procurement Analysis Portal

## 1. Executive Summary & Domain Context
In the UK electricity system, electricity suppliers (utilities) are obligated to balance generation purchases with consumer demand in every 30-minute settlement period (48 periods per settlement day). Power procurement on the day-ahead wholesale market (e.g., EPEX SPOT, Nord Pool / N2EX) takes place on the day prior to delivery ($D-1$), typically closing around 11:00 or 12:00 GMT/UTC. 

Because wind generation is weather-dependent, procurement desks must decide how much power to buy from the day-ahead market (or dispatch thermal generation) using the **latest available wind generation forecasts** prior to the auction cutoff. If the forecast overestimates wind, the utility faces a costly short position during settlement; if it underestimates, it risks buying excess thermal power.

This portal provides an operational dashboard and analytical engine for the procurement desk to:
1. Access the exact, latest wind forecast available at the day-ahead decision cutoff for any delivery date in January 2026.
2. Quantify forecast accuracy against outturn (actual) wind generation using robust statistical metrics.
3. Eliminate look-ahead bias (data leakage) by strictly filtering out forecasts published after the decision cutoff.
4. Compare forecast vintages leading up to the cutoff to observe how forecast confidence and errors evolved.

---

## 2. Architecture & Component Responsibilities

```
                                      +-----------------------------------------+
                                      |         Elexon BMRS Insights API        |
                                      +-----------------------------------------+
                                             |                           |
                     GET /datasets/FUELHH/stream?                GET /datasets/WINDFOR/stream?
                   settlementDateFrom=D&settlementDateTo=D     publishDateTimeFrom=D-2&publishDateTimeTo=Cutoff
                                             |                           |
                                             v                           v
+-------------------------------------------------------------------------------------------------------+
| Python FastAPI Backend (`backend/app/`)                                                              |
|                                                                                                       |
|  [Clients Layer: `app/clients/`]                                                                      |
|   - FuelHHClient: queries actual generation, filters fuelType == "WIND", validates MW                  |
|   - WindforClient: queries stream forecasts, filters publication window, validates schema             |
|   - Fixture Fallback: local cached fixtures for deterministic offline/dev use                         |
|                                                                                                       |
|  [Analytical Services Layer: `app/services/`]                                                         |
|   - CutoffEngine: computes cutoff (default D-1 11:00 UTC), strictly partitions eligible vs leakage    |
|   - AlignmentEngine: aligns forecast and actual by delivery startTime (UTC)                           |
|   - MetricsCalculator: calculates MAE, RMSE, Bias (Mean Error), WAPE, peak error, MWh volumes         |
|   - ProcurementAnalysisService: orchestrates clients, cutoff, alignment, and metrics                 |
|                                                                                                       |
|  [API Routes Layer: `app/api/routes/`]                                                                |
|   - GET /api/health                                                                                   |
|   - GET /api/dates (January 2026 delivery dates & status)                                             |
|   - GET /api/analysis?delivery_date=YYYY-MM-DD&cutoff_hour=11&cutoff_day_offset=1                     |
|   - GET /api/vintages/compare?delivery_date=YYYY-MM-DD                                                 |
+-------------------------------------------------------------------------------------------------------+
                                             ^
                                             |  REST / JSON (Vite Dev Proxy /api -> 127.0.0.1:8000)
                                             v
+-------------------------------------------------------------------------------------------------------+
| React (Vite) Frontend (`frontend/src/`)                                                               |
|                                                                                                       |
|  [Components: `src/components/`]                                                                      |
|   - Header: source info, cutoff assumption, data freshness badge, operational guide modal trigger     |
|   - ControlBar: January 2026 Date Picker, Configurable Cutoff Hour, Resolution Mode (30m vs Hourly)   |
|   - MetricCards: MAE (MW), RMSE (MW), Bias (MW), WAPE (%), Matched Intervals, Coverage %             |
|   - ActualVsForecastChart: Recharts interactive time series with synchronized tooltips                |
|   - ErrorAnalysisChart: Over/Under delivery visualization across settlement periods                   |
|   - VintageEvolutionView: Compare forecast vintages published across D-2 and D-1                     |
|   - IntervalTable: Granular 30-min settlement breakdown with CSV export and search                    |
|   - OperationalContext: Domain guide explaining procurement trade-offs and metric definitions         |
+-------------------------------------------------------------------------------------------------------+
```

---

## 3. Data Sources & Schema Assumptions

### 3.1 Actual Generation (Elexon FUELHH)
- **Endpoint**: `https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream`
- **Query Parameter**: `settlementDateFrom={YYYY-MM-DD}&settlementDateTo={YYYY-MM-DD}`
- **Filter**: `fuelType == "WIND"` (case-insensitive)
- **Schema**:
  - `dataset`: String (`"FUELHH"`)
  - `publishTime`: ISO8601 UTC timestamp
  - `startTime`: ISO8601 UTC timestamp of delivery interval
  - `settlementDate`: String `YYYY-MM-DD`
  - `settlementPeriod`: Integer 1 to 48
  - `fuelType`: String (`"WIND"`)
  - `generation`: Float / Integer in Megawatts (MW)

### 3.2 Forecasted Generation (Elexon WINDFOR)
- **Endpoint**: `https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream`
- **Query Parameter**: `publishDateTimeFrom={ISO}&publishDateTimeTo={ISO}`
- **Schema**:
  - `dataset`: String (`"WINDFOR"`)
  - `publishTime`: ISO8601 UTC timestamp of forecast creation/publication
  - `startTime`: ISO8601 UTC timestamp of delivery interval
  - `generation`: Float / Integer in Megawatts (MW)

### 3.3 Timezone & Cutoff Definition
- **Timezone**: All timestamps are parsed, compared, and reported in UTC (Greenwich Mean Time / GMT). In January, the UK is strictly on GMT (UTC+0).
- **Day-Ahead Decision Cutoff**:
  - For delivery date $D$, day-ahead power auction bids are submitted on $D-1$.
  - The default decision cutoff is set to **11:00 UTC on $D-1$** (reflecting standard day-ahead auction gate closure in the UK market).
  - The cutoff is fully configurable (e.g. 10:00 UTC, 12:00 UTC) via query parameters.
  - **Leakage Prevention Rule**: For any delivery period $t$ on date $D$, only forecast records where:
    $$\text{publishTime} \le \text{CutoffTime}(D)$$
    are eligible. Any forecast published after $\text{CutoffTime}(D)$ is strictly excluded from decision analysis.
  - **Month Boundary Handling**:
    - For delivery on `2026-01-01`, the day-ahead cutoff is `2025-12-31T11:00:00Z`. The system queries forecasts published in late December 2025 that cover January 1, 2026.
    - For delivery on `2026-01-31`, the cutoff is `2026-01-30T11:00:00Z`.

---

## 4. Analytical Formulas & Metrics

Given $N$ matched delivery intervals with actual generation $A_i$ (MW) and forecast generation $F_i$ (MW):

1. **Forecast Error ($e_i$)**:
   $$e_i = F_i - A_i \quad \text{[MW]}$$
   - A positive error ($e_i > 0$) means the forecast **over-predicted** wind (trading desk faced short exposure into the balancing mechanism).
   - A negative error ($e_i < 0$) means the forecast **under-predicted** wind (procurement purchased excess thermal generation).

2. **Mean Absolute Error (MAE)**:
   $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |F_i - A_i| \quad \text{[MW]}$$

3. **Root Mean Square Error (RMSE)**:
   $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (F_i - A_i)^2} \quad \text{[MW]}$$

4. **Mean Error / Bias**:
   $$\text{Bias} = \frac{1}{N} \sum_{i=1}^N (F_i - A_i) \quad \text{[MW]}$$

5. **Weighted Absolute Percentage Error (WAPE)**:
   $$\text{WAPE} = \frac{\sum_{i=1}^N |F_i - A_i|}{\sum_{i=1}^N A_i} \times 100\%$$
   *Note: WAPE avoids division by zero on individual intervals where actual wind generation is 0 MW, guaranteeing mathematical stability.*

6. **Peak Absolute Error**:
   $$\text{MaxError} = \max_{i} |F_i - A_i| \quad \text{[MW]}$$

7. **Data Coverage**:
   $$\text{Coverage} = \frac{N_{\text{matched}}}{N_{\text{total expected}}} \times 100\%$$

8. **Energy Volume (MWh)**:
   For 30-minute settlement periods (duration 0.5 hours):
   $$\text{Energy (MWh)} = \sum_{i=1}^N P_i \times 0.5 \text{ hours}$$

---

## 5. Verified Benchmark Metrics (January 15, 2026)
From live Elexon BMRS data for delivery on `2026-01-15`:
- **Delivery Date**: `2026-01-15`
- **Cutoff Applied**: `2026-01-14 11:00:00 UTC`
- **Selected Forecast Publication**: `2026-01-14 09:30:00 UTC`
- **Matched Intervals**: 48 of 48 (100.0% coverage)
- **Mean Absolute Error (MAE)**: 1,110.25 MW
- **Root Mean Square Error (RMSE)**: 1,228.54 MW
- **Forecast Bias (Mean Error)**: +1,110.25 MW (over-forecast)
- **Weighted Absolute Percentage Error (WAPE)**: 10.51%
- **Peak Absolute Error**: 2,386.0 MW
- **Total Outturn Actual Energy**: 253,626.0 MWh
- **Total Forecast Energy**: 280,272.0 MWh

---

## 6. Defensive Handling & Testing Strategy
- **Missing Intervals**: Missing records are never filled with zero; they are counted as missing and reported in the data transparency card.
- **Duplicates**: Deduplicated deterministically by `(startTime, publishTime)`, retaining the most recent record.
- **Zero Generation**: Zero actual generation is preserved; percentage metrics use aggregate WAPE instead of MAPE to avoid division by zero.
- **Upstream Resilience**: Bounded retries (3 attempts with exponential backoff) and timeout (15s). If live API is unreachable or rate-limited, local fixture data for January 2026 is served with a transparent status banner ("Using verified local fixture cache").
- **Automated Tests**: 23 backend unit and API route tests in `backend/tests/` covering cutoff boundary logic, leakage prevention, vintage selection, zero-safe metrics, and FastAPI endpoints.
