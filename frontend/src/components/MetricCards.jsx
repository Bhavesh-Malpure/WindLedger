import React from 'react';
import { Target, TrendingUp, AlertTriangle, Activity, CheckCircle2, Zap } from 'lucide-react';

export default function MetricCards({ data }) {
  if (!data) return null;

  const { metrics, decision_cutoff_utc, selected_vintage_publish_time, delivery_date } = data;

  // Format UTC dates
  const formatUtcTime = (isoStr) => {
    if (!isoStr) return 'N/A';
    const d = new Date(isoStr);
    return d.toUTCString().replace('GMT', 'UTC');
  };

  const isOverforecast = (metrics?.bias_mw || 0) > 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      
      {/* 1. Decision Cutoff & Vintage Card */}
      <div className="bg-white border border-[#DCE5DE] rounded-xl p-4 flex flex-col justify-between shadow-sm hover:border-[#C9D6CC] transition">
        <div>
          <div className="flex items-center justify-between text-[#64756D] text-xs font-semibold mb-2">
            <span className="flex items-center space-x-1.5">
              <Target className="w-3.5 h-3.5 text-blue-400" />
              <span>Decision Cutoff Gate</span>
            </span>
            <span className="px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 text-[10px] font-mono">
              Zero Leakage
            </span>
          </div>
          <div className="text-sm font-bold text-[#123B32] font-mono">
            {decision_cutoff_utc ? new Date(decision_cutoff_utc).toISOString().replace('.000Z', ' UTC') : 'N/A'}
          </div>
          <div className="mt-2 text-xs text-[#64756D]">
            <span className="text-[#738078]">Latest Eligible Vintage:</span>
            <div className="text-emerald-400 font-mono font-medium mt-0.5">
              {selected_vintage_publish_time
                ? new Date(selected_vintage_publish_time).toISOString().replace('.000Z', ' UTC')
                : 'No eligible vintage'}
            </div>
          </div>
        </div>
        <div className="mt-3 pt-2.5 border-t border-[#DCE5DE] text-[11px] text-[#64756D]">
          Delivery Date: <span className="text-[#23483D] font-mono">{delivery_date}</span>
        </div>
      </div>

      {/* 2. MAE Card */}
      <div className="bg-white border border-[#DCE5DE] rounded-xl p-4 flex flex-col justify-between shadow-sm hover:border-[#C9D6CC] transition">
        <div>
          <div className="flex items-center justify-between text-[#64756D] text-xs font-semibold mb-2">
            <span className="flex items-center space-x-1.5">
              <Activity className="w-3.5 h-3.5 text-emerald-400" />
              <span>Mean Absolute Error (MAE)</span>
            </span>
            <span className="text-xs text-[#738078]">MW</span>
          </div>
          <div className="flex items-baseline space-x-1.5">
            <span className="text-2xl font-bold font-mono text-[#123B32]">
              {metrics?.mae_mw != null ? metrics.mae_mw.toLocaleString() : 'N/A'}
            </span>
            <span className="text-xs text-[#64756D] font-mono">MW</span>
          </div>
          <div className="mt-2 text-xs text-[#64756D]">
            Average deviation per settlement interval between day-ahead forecast and outturn generation.
          </div>
        </div>
        <div className="mt-3 pt-2.5 border-t border-[#DCE5DE] flex justify-between text-[11px] text-[#64756D] font-mono">
          <span>Peak Error:</span>
          <span className="text-[#23483D]">{metrics?.peak_absolute_error_mw != null ? `${metrics.peak_absolute_error_mw.toLocaleString()} MW` : 'N/A'}</span>
        </div>
      </div>

      {/* 3. Bias / Mean Error Card */}
      <div className="bg-white border border-[#DCE5DE] rounded-xl p-4 flex flex-col justify-between shadow-sm hover:border-[#C9D6CC] transition">
        <div>
          <div className="flex items-center justify-between text-[#64756D] text-xs font-semibold mb-2">
            <span className="flex items-center space-x-1.5">
              <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
              <span>Forecast Bias (Mean Error)</span>
            </span>
            <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
              isOverforecast ? 'bg-amber-500/10 text-amber-300' : 'bg-cyan-500/10 text-cyan-300'
            }`}>
              {isOverforecast ? 'Over-Forecast' : 'Under-Forecast'}
            </span>
          </div>
          <div className="flex items-baseline space-x-1.5">
            <span className={`text-2xl font-bold font-mono ${
              isOverforecast ? 'text-amber-400' : 'text-cyan-400'
            }`}>
              {metrics?.bias_mw != null ? `${metrics.bias_mw > 0 ? '+' : ''}${metrics.bias_mw.toLocaleString()}` : 'N/A'}
            </span>
            <span className="text-xs text-[#64756D] font-mono">MW</span>
          </div>
          <div className="mt-2 text-xs text-[#64756D]">
            {isOverforecast 
              ? 'Wind generation came in lower than forecast; trading desk faced short exposure into balancing.' 
              : 'Wind generation came in higher than forecast; excess renewable power displaced thermal.'}
          </div>
        </div>
        <div className="mt-3 pt-2.5 border-t border-[#DCE5DE] flex justify-between text-[11px] text-[#64756D] font-mono">
          <span>RMSE:</span>
          <span className="text-[#23483D]">{metrics?.rmse_mw != null ? `${metrics.rmse_mw.toLocaleString()} MW` : 'N/A'}</span>
        </div>
      </div>

      {/* 4. WAPE & Coverage Card */}
      <div className="bg-white border border-[#DCE5DE] rounded-xl p-4 flex flex-col justify-between shadow-sm hover:border-[#C9D6CC] transition">
        <div>
          <div className="flex items-center justify-between text-[#64756D] text-xs font-semibold mb-2">
            <span className="flex items-center space-x-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#198754]" />
              <span>Aggregate WAPE & Coverage</span>
            </span>
            <span className="text-xs text-[#198754] font-mono">
              {metrics?.coverage_percent}% Match
            </span>
          </div>
          <div className="flex items-baseline space-x-1.5">
            <span className="text-2xl font-bold font-mono text-[#123B32]">
              {metrics?.wape_percent != null ? `${metrics.wape_percent}%` : 'N/A'}
            </span>
            <span className="text-xs text-[#64756D] font-mono">WAPE</span>
          </div>
          <div className="mt-2 text-xs text-[#64756D]">
            Weighted Absolute Percentage Error avoids zero-calm explosion and expresses total day error.
          </div>
        </div>
        <div className="mt-3 pt-2.5 border-t border-[#DCE5DE] flex justify-between text-[11px] text-[#64756D] font-mono">
          <span>Matched Intervals:</span>
          <span className="text-[#23483D]">
            {metrics?.matched_intervals} / {metrics?.total_expected_intervals}
          </span>
        </div>
      </div>

    </div>
  );
}
