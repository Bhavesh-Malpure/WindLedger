# Video Audio & Narration Script
## UK Wind Forecast & Day-Ahead Procurement Analysis Portal

**Total Duration**: ~9:15 (Strict requirement: <= 10:00 maximum)
- **Part 1**: Client Pitch & Operational Demonstration (0:00 - 4:25, duration ~4:25, max 5:00)
- **Part 2**: Technical Lead Review & Architecture Deep-Dive (4:25 - 9:15, duration ~4:50, max 5:00)

---

## Part 1: Client Pitch & Operational Walkthrough (0:00 - 4:25)
**Target Audience**: Head of Day-Ahead Power Procurement & Power Trading Desk  
**Core Objective**: Demonstrate how this portal eliminates day-ahead procurement blind spots, quantifies forecast error risk, and prevents look-ahead bias in January 2026 power buying.

---

### [0:00 - 0:40] Introduction & The Day-Ahead Procurement Challenge
- **Visual on Screen**: 
  - Browser opens to `http://localhost:5173/`.
  - Dashboard header is visible: "UK National Wind Forecast Portal · January 2026".
  - Connection status badge shows "Live Elexon Stream" and "API: Connected".
- **Narration**:
  > *"Good morning. As an electricity supplier in the UK, your day-ahead power procurement desk faces a high-stakes mandate every morning: before wholesale auctions close around 11:00 AM, you have to purchase enough electricity to cover your consumers' demand. Every megawatt of wind generation you expect reduces the expensive thermal or balancing power you have to buy. But renewable generation is weather-dependent, and trading desks often suffer from a subtle bias: looking at forecast accuracy in hindsight, using weather models that weren't actually in your hands when you placed your bids.*
  >
  > *Today, I'm presenting our operational Day-Ahead Wind Forecast Analysis Portal, built specifically for your January 2026 procurement operations using official national Elexon BMRS market data."*

---

### [0:40 - 2:00] Live Date Selection, Cutoff Enforcement & Verified KPIs
- **Visual on Screen**:
  - Presenter selects delivery date: `2026-01-15` in the date picker.
  - Cutoff indicator highlights: `2026-01-14 11:00:00 UTC` (D-1 Auction Gate Closure).
  - Point cursor to the "Latest Eligible Vintage" badge: `2026-01-14 09:30:00 UTC`.
  - Hover over the 4 Metric Cards showing verified numbers.
- **Narration**:
  > *"Let's look at delivery on January 15th, 2026. The day-ahead auction cutoff occurred on January 14th at 11:00 AM UTC. Notice what our engine does: it strictly rejects any forecast published after 11:00 AM on the 14th. There is zero look-ahead leakage. The most up-to-date forecast vintage your traders had on their screens was published at 09:30 AM UTC.*
  >
  > *Here are the verified operational metrics for that 09:30 AM forecast against actual generation:
  > - Mean Absolute Error (MAE): 1,110.25 MW. On average across the 48 settlement periods, wind differed by about 1.1 gigawatts from forecast.
  > - Root Mean Square Error (RMSE): 1,228.54 MW, capturing the quadratic penalty of volatility during sudden ramp periods.
  > - Forecast Bias: +1,110.25 MW. The positive sign tells your traders immediately that the forecast over-predicted wind, meaning the desk faced short exposure into the balancing mechanism.
  > - Weighted Absolute Percentage Error (WAPE): 10.51%. Notice that instead of fragile MAPE which explodes when wind drops to zero, WAPE reflects total aggregate volume error.
  > - Coverage: Exactly 48 out of 48 half-hour settlement periods matched, with zero artificial data substitution."*

---

### [2:00 - 3:10] Time-Series & Error Distribution Walkthrough
- **Visual on Screen**:
  - Mouse hovers across the "Actual vs Forecast" chart:
    - Teal solid line represents actual generation (Elexon FUELHH WIND).
    - Purple dashed line represents the latest day-ahead forecast (WINDFOR).
  - Tooltips pop up showing delivery time, actual MW, forecast MW, and the delta.
  - Scroll down to the "Hourly Forecast Error Distribution" bar chart showing amber (over-forecast) bars.
- **Narration**:
  > *"Looking at our primary time-series chart: actual wind generation reached over 12,000 MW. The forecast tracked the general shape of the wind profile, but consistently over-estimated generation by roughly 1,000 to 2,000 MW throughout the day, peaking at an error of 2,386 MW in the evening.*
  >
  > *Down on our Error Distribution chart, the amber bars show positive error across settlement periods. In operational terms, this translates directly to a short position: your desk relied on clean wind that failed to materialize, requiring reserve dispatch or balancing mechanism settlement. Having this exact profile allows your traders to hedge with intra-day options or flexible gas peaking units."*

---

### [3:10 - 4:05] Vintage Evolution & Interval Ledger
- **Visual on Screen**:
  - Click on "Forecast Vintage Evolution" tab.
  - Multi-line chart displays different model runs published across January 13th and 14th.
  - Show the log table showing eligible vs rejected vintages.
  - Click on "Interval Ledger" tab, show search filter and "Export CSV" button.
- **Narration**:
  > *"Next, let's switch to the Forecast Vintage Evolution tab. Trading heads love this view because it shows how the meteorological forecast converged over the 36 hours leading up to the cutoff. You can compare the early model run from January 13th with the subsequent runs on the morning of the 14th to see whether forecast confidence was improving or drifting.*
  >
  > *Finally, our Interval Ledger gives dispatchers a granular 48-period settlement table. You can sort by error magnitude, filter by specific settlement periods, or click 'Export CSV' to download the verified ledger directly into your trading models."*

---

### [4:05 - 4:25] Client Wrap-Up & Transition
- **Visual on Screen**:
  - Click "Operational Guide" button, displaying the modal with operational context and limitations caveat.
- **Narration**:
  > *"In summary, this portal delivers exact, uncompromised decision-point clarity for your January 2026 power procurement desk. Next, I'll switch hats and walk through the engineering architecture, data pipeline, and automated test suite with our technical lead."*

---

## Part 2: Technical Lead Review & Architecture Deep-Dive (4:25 - 9:15)
**Target Audience**: Internal Technical Lead / Principal Software Architect  
**Core Objective**: Review codebase architecture, Elexon BMRS API integration, leakage prevention, test coverage, and design choices.

---

### [4:25 - 5:35] Architecture & Separation of Concerns
- **Visual on Screen**:
  - VS Code opened to project root.
  - Expand directory tree:
    - `backend/app/clients/` (`fuelhh_client.py`, `windfor_client.py`)
    - `backend/app/services/` (`cutoff_engine.py`, `alignment_engine.py`, `metrics.py`, `procurement_service.py`)
    - `backend/app/api/routes/` (`analysis.py`, `dates.py`, `vintages.py`)
    - `frontend/src/components/`, `frontend/src/services/api.js`
  - Open `docs/technical_design.md` architecture diagram.
- **Narration**:
  > *"Welcome to the technical review. Our system design prioritizes clean separation of concerns, zero look-ahead leakage, and defensive data access.
  >
  > We chose Python with FastAPI for the backend and React with Vite and Tailwind CSS for the frontend:
  > - In `backend/app/clients`, we built dedicated, decoupled HTTP clients for Elexon's `FUELHH/stream` and `WINDFOR/stream` endpoints. They incorporate bounded retries, exponential backoff, timeouts, and local fixture fallback for offline resilience.
  > - In `backend/app/services`, data access is completely isolated from business analytics. `CutoffEngine`, `AlignmentEngine`, and `MetricsCalculator` have zero dependency on HTTP routing or database models.
  > - The frontend is purely a presentation layer. All analytical calculations, metric aggregations, and cutoff logic execute deterministically on the backend."*

---

### [5:35 - 6:50] Data Ingestion & Leakage Prevention Logic
- **Visual on Screen**:
  - Open `backend/app/services/cutoff_engine.py` in editor.
  - Highlight method `filter_eligible_forecasts` and `select_latest_eligible_forecasts`.
  - Open `backend/app/utils/timezone.py` showing `get_cutoff_datetime`.
- **Narration**:
  > *"Let's look at the core analytical engine. The most critical requirement is preventing data leakage.
  >
  > For any delivery date D in January 2026, the auction cutoff is computed in `get_cutoff_datetime` as `(D - cutoff_day_offset) at cutoff_hour:00:00 UTC`. For January 1st, 2026, the cutoff seamlessly rolls over to December 31st, 2025 at 11:00 UTC.
  >
  > In `cutoff_engine.py`, the `filter_eligible_forecasts` method partitions records: any forecast where `publish_time <= cutoff` is eligible; any record published even one second after cutoff is rejected. 
  >
  > Then, `select_latest_eligible_forecasts` groups eligible records by delivery `startTime` and picks the record with the maximum `publish_time`. This guarantees that for every settlement interval, we evaluate the exact latest forecast that was available when traders submitted their bids."*

---

### [6:50 - 7:55] Interval Alignment & Zero-Safe Metrics
- **Visual on Screen**:
  - Open `backend/app/services/alignment_engine.py` and `metrics.py`.
  - Highlight WAPE calculation: `wape = (sum(abs_errors) / sum_actual) * 100`.
  - Highlight `duration_hours` volume conversion for MWh.
- **Narration**:
  > *"Next, let's examine interval alignment and metrics in `alignment_engine.py` and `metrics.py`.
  >
  > In Elexon, actual generation (`FUELHH`) is published at 30-minute settlement period resolution, while WINDFOR stream forecasts are published at hourly resolution. 
  >
  > In `alignment_engine.py`, we provide two modes:
  > - `half_hourly_expanded`: each hourly forecast applies to both 30-minute settlement periods in that hour, yielding all 48 settlement periods.
  > - `exact`: matches strictly on exact hourly `startTime`, yielding 24 intervals.
  >
  > In `metrics.py`, missing intervals are never silently replaced with zero. They are excluded from the denominator, and the exact matched count and coverage percentage are reported.
  >
  > For percentage error, we intentionally implement WAPE rather than MAPE. When wind generation drops to zero during calm weather, MAPE divides by zero and explodes to infinity. WAPE sums absolute errors over total actual volume, guaranteeing mathematical stability."*

---

### [7:55 - 8:40] Automated Test Suite Execution
- **Visual on Screen**:
  - Terminal in VS Code executing `cd backend; pytest -v`.
  - All 30 tests pass in green.
- **Narration**:
  > *"Quality is enforced through our automated test suite in `backend/tests/`. We have 30 comprehensive tests covering:
  > - Strict cutoff boundary conditions, December 31st rollover, and month-end closing.
  > - 1-second post-cutoff leakage rejection and vintage eligibility tagging.
  > - Deduplication and latest-vintage selection.
  > - FUELHH and WINDFOR client schema validation and fixture fallbacks.
  > - Zero actual generation, under-forecast negative bias, and partial interval coverage.
  > - FastAPI route validation with Pydantic schemas and exact-mode alignment.
  >
  > Running `pytest -v`, all 30 tests execute and pass in approximately one to two seconds."*

---

### [8:40 - 9:15] Codebase Walkthrough & Developer Handoff
- **Visual on Screen**:
  - Open `README.md` and show startup commands and architecture guide.
  - Open running browser displaying the dashboard in incognito mode.
- **Narration**:
  > *"To spin up the system locally:
  > - On the backend: `pip install -r requirements.txt` then `uvicorn app.main:app --reload`
  > - On the frontend: `npm install` then `npm run dev`
  >
  > All configuration is centralized in `.env.example`, and the frontend proxies `/api` calls directly to FastAPI on port 8000.
  >
  > This concludes our technical review. The platform is robust, verified against live Elexon data, and ready for containerization and deployment. Thank you."*
