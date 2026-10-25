import logging
from datetime import datetime, date, timezone
from typing import List, Dict, Optional, Tuple, Literal

from app.core.config import settings
from app.core.errors import InvalidDateRangeError, DataNotFoundError
from app.clients.fuelhh_client import FuelHHClient
from app.clients.windfor_client import WindforClient
from app.services.cutoff_engine import CutoffEngine
from app.services.alignment_engine import AlignmentEngine, AlignmentMode
from app.services.metrics import MetricsCalculator
from app.models.schemas import (
    AnalysisResponse,
    VintageComparisonResponse,
    VintageSeriesItem,
    DeliveryDateStatus
)
from app.utils.timezone import is_in_january_2026, parse_utc_iso

logger = logging.getLogger(__name__)

class ProcurementAnalysisService:
    """
    High-level orchestrator coordinating data clients, cutoff filtering,
    time-series alignment, and accuracy metrics computation.
    """

    def __init__(
        self,
        fuel_client: Optional[FuelHHClient] = None,
        wind_client: Optional[WindforClient] = None,
        cutoff_engine: Optional[CutoffEngine] = None,
        alignment_engine: Optional[AlignmentEngine] = None
    ):
        self.fuel_client = fuel_client or FuelHHClient()
        self.wind_client = wind_client or WindforClient()
        self.cutoff_engine = cutoff_engine or CutoffEngine(
            default_cutoff_hour=settings.default_cutoff_hour_utc,
            default_cutoff_day_offset=settings.default_cutoff_day_offset
        )
        self.alignment_engine = alignment_engine or AlignmentEngine()

    def analyze_delivery_date(
        self,
        delivery_date: date,
        cutoff_hour: Optional[int] = None,
        cutoff_day_offset: Optional[int] = None,
        alignment_mode: AlignmentMode = "half_hourly_expanded",
        force_fixture: Optional[bool] = None
    ) -> AnalysisResponse:
        """
        Run end-to-end analysis for a delivery date in January 2026.
        """
        # 1. Enforce January 2026 scope
        if not is_in_january_2026(delivery_date):
            raise InvalidDateRangeError(
                f"Requested delivery date '{delivery_date}' is outside January 2026. "
                "Per assignment specification, all analysis is strictly scoped to January 2026."
            )

        # 2. Compute decision cutoff
        hour = settings.default_cutoff_hour_utc if cutoff_hour is None else cutoff_hour
        offset = settings.default_cutoff_day_offset if cutoff_day_offset is None else cutoff_day_offset
        cutoff_dt = self.cutoff_engine.compute_cutoff(
            delivery_date,
            cutoff_hour=hour,
            cutoff_day_offset=offset
        )

        # 3. Retrieve actual wind generation
        actuals, fuel_is_fixture = self.fuel_client.fetch_actuals(delivery_date, force_fixture=force_fixture)

        # 4. Retrieve forecasts published leading up to cutoff
        # (Look back 2 days before cutoff to capture all relevant candidate vintages)
        forecasts, wind_is_fixture = self.wind_client.fetch_forecasts_for_delivery_date(
            delivery_date=delivery_date,
            cutoff_datetime=cutoff_dt,
            lookback_days=2,
            force_fixture=force_fixture
        )

        # 5. Strictly enforce cutoff: separate eligible from rejected
        eligible_forecasts, rejected_forecasts = self.cutoff_engine.filter_eligible_forecasts(
            forecasts,
            cutoff_datetime=cutoff_dt
        )

        # 6. Select latest eligible forecast per delivery interval
        latest_forecast_by_start = self.cutoff_engine.select_latest_eligible_forecasts(eligible_forecasts)

        # Identify the latest publication timestamp among selected records
        selected_pub_times = [r.publish_time for r in latest_forecast_by_start.values()]
        selected_latest_pub = max(selected_pub_times) if selected_pub_times else None

        # 7. Extract vintage summaries for user transparency and comparison
        vintage_summaries = self.cutoff_engine.extract_vintage_summaries(
            all_records=forecasts,
            cutoff_datetime=cutoff_dt,
            selected_latest_vintage_time=selected_latest_pub
        )

        # 8. Align actuals and forecast by delivery interval
        aligned_intervals = self.alignment_engine.align(
            actuals=actuals,
            forecast_by_start=latest_forecast_by_start,
            delivery_date=delivery_date,
            mode=alignment_mode
        )

        # 9. Calculate accuracy metrics
        total_expected = 48 if alignment_mode == "half_hourly_expanded" else 24
        metrics = MetricsCalculator.calculate(
            intervals=aligned_intervals,
            total_expected_intervals=total_expected
        )

        # 10. Document data limitations
        limitations: List[str] = [
            f"Day-ahead decision cutoff applied: {cutoff_dt.strftime('%Y-%m-%d %H:%M:%S UTC')} (D-{offset} {hour}:00 UTC).",
            "Any forecast published after the decision cutoff was excluded from analysis to prevent look-ahead bias.",
            "Actuals from Elexon FUELHH filtered to fuelType == 'WIND' (MW).",
            "WINDFOR forecasts are published in periodic runs covering future delivery intervals."
        ]
        if alignment_mode == "half_hourly_expanded":
            limitations.append(
                "Alignment mode: Half-Hourly Expanded (hourly forecast applied to both 30-min settlement periods in that hour)."
            )
        else:
            limitations.append(
                "Alignment mode: Exact StartTime Match (24 hourly delivery intervals matched)."
            )

        is_fixture_mode = fuel_is_fixture or wind_is_fixture
        if fuel_is_fixture:
            limitations.append("Actual-generation source: local fixture data. Fixture provenance has not been independently verified; do not present these values as verified live Elexon observations.")
        if wind_is_fixture:
            limitations.append("Forecast source: local fixture data. Fixture provenance and publication timestamps have not been independently verified; do not present these values as verified live Elexon forecasts.")

        return AnalysisResponse(
            delivery_date=delivery_date.isoformat(),
            decision_cutoff_utc=cutoff_dt,
            cutoff_hour_utc=hour,
            selected_vintage_publish_time=selected_latest_pub,
            data_source="Elexon BMRS (FUELHH & WINDFOR)",
            freshness_timestamp=datetime.now(timezone.utc),
            metrics=metrics,
            intervals=aligned_intervals,
            available_vintages=vintage_summaries,
            data_limitations=limitations,
            is_fixture_data=is_fixture_mode,
            actuals_source="fixture" if fuel_is_fixture else "live",
            forecast_source="fixture" if wind_is_fixture else "live",
            source_warning=(
                "One or more data sources used local fallback fixtures. Treat the analysis as illustrative until fixture provenance is verified."
                if is_fixture_mode else None
            )
        )

    def compare_vintages(
        self,
        delivery_date: date,
        cutoff_hour: Optional[int] = None,
        cutoff_day_offset: Optional[int] = None,
        force_fixture: Optional[bool] = None
    ) -> VintageComparisonResponse:
        """
        Extract time series for all available forecast vintages published prior to cutoff
        to visualize forecast evolution leading up to the decision.
        """
        if not is_in_january_2026(delivery_date):
            raise InvalidDateRangeError()

        hour = settings.default_cutoff_hour_utc if cutoff_hour is None else cutoff_hour
        offset = settings.default_cutoff_day_offset if cutoff_day_offset is None else cutoff_day_offset
        cutoff_dt = self.cutoff_engine.compute_cutoff(delivery_date, cutoff_hour=hour, cutoff_day_offset=offset)

        forecasts, _ = self.wind_client.fetch_forecasts_for_delivery_date(
            delivery_date=delivery_date,
            cutoff_datetime=cutoff_dt,
            lookback_days=2,
            force_fixture=force_fixture
        )

        eligible, _ = self.cutoff_engine.filter_eligible_forecasts(forecasts, cutoff_dt)

        # Group by publish_time
        by_pub: Dict[str, List[VintageSeriesItem]] = {}
        for r in eligible:
            pub_key = r.publish_time.strftime("%Y-%m-%d %H:%M UTC")
            if pub_key not in by_pub:
                by_pub[pub_key] = []
            by_pub[pub_key].append(
                VintageSeriesItem(
                    start_time=r.start_time,
                    forecast_generation_mw=r.generation
                )
            )

        # Sort each series by start_time
        for key in by_pub:
            by_pub[key] = sorted(by_pub[key], key=lambda x: x.start_time)

        return VintageComparisonResponse(
            delivery_date=delivery_date.isoformat(),
            vintages=by_pub
        )

    def get_january_2026_dates(self) -> List[DeliveryDateStatus]:
        """Return list of all 31 days in January 2026 with metadata."""
        dates: List[DeliveryDateStatus] = []
        for day in range(1, 32):
            d_str = f"2026-01-{day:02d}"
            dates.append(
                DeliveryDateStatus(
                    date_str=d_str,
                    has_actuals=True,
                    has_forecasts=True,
                    is_valid_january_2026=True
                )
            )
        return dates
