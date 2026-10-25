from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

from app.core.config import settings
from app.models.schemas import HealthResponse
from app.api.routes.analysis import router as analysis_router
from app.api.routes.dates import router as dates_router
from app.api.routes.vintages import router as vintages_router

app = FastAPI(
    title="UK Wind Forecast & Day-Ahead Procurement API",
    description="Operational API for analyzing UK national wind generation forecasts vs actuals from Elexon BMRS for January 2026 day-ahead power procurement.",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(analysis_router, prefix="/api")
app.include_router(dates_router, prefix="/api")
app.include_router(vintages_router, prefix="/api")

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
def get_health():
    """Health check endpoint providing status and upstream connectivity flag."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc),
        environment=settings.environment,
        # This endpoint checks the application process only; it does not make a
        # network request to Elexon, so upstream reachability must not be asserted.
        upstream_elexon_status="not_checked",
        is_fixture_mode=settings.force_fixture_mode,
        note="Application health only. Elexon connectivity and live/fixture source are reported by analysis responses."
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
