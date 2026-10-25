import React from 'react';
import { Calendar, Clock, Sliders, RefreshCw, Layers } from 'lucide-react';

export default function ControlBar({
  deliveryDate,
  onDateChange,
  cutoffHour,
  onCutoffHourChange,
  alignmentMode,
  onAlignmentModeChange,
  forceFixture,
  onForceFixtureChange,
  onRefresh,
  loading
}) {
  const dates = Array.from({ length: 31 }, (_, i) => {
    const day = String(i + 1).padStart(2, '0');
    return `2026-01-${day}`;
  });

  return (
    <div className="bg-white border border-[#DCE5DE] rounded-xl p-4 shadow-lg backdrop-blur-sm">
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
        
        {/* Date Selector */}
        <div className="md:col-span-4 flex flex-col space-y-1.5">
          <label className="text-xs font-semibold text-[#35564D] flex items-center space-x-1.5">
            <Calendar className="w-3.5 h-3.5 text-emerald-400" />
            <span>January 2026 Delivery Date</span>
          </label>
          <div className="flex space-x-2">
            <select
              value={deliveryDate}
              onChange={(e) => onDateChange(e.target.value)}
              className="w-full bg-[#F7F9F7] border border-[#C9D6CC] rounded-lg px-3 py-2 text-sm text-[#123B32] font-mono focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            >
              {dates.map((d) => (
                <option key={d} value={d}>
                  {d} {d === '2026-01-01' ? '(Boundary)' : d === '2026-01-15' ? '(Benchmark)' : ''}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Day-Ahead Decision Cutoff Hour */}
        <div className="md:col-span-3 flex flex-col space-y-1.5">
          <label className="text-xs font-semibold text-[#35564D] flex items-center space-x-1.5">
            <Clock className="w-3.5 h-3.5 text-blue-400" />
            <span>Auction Cutoff (D-1 UTC)</span>
          </label>
          <select
            value={cutoffHour}
            onChange={(e) => onCutoffHourChange(Number(e.target.value))}
            className="w-full bg-[#F7F9F7] border border-[#C9D6CC] rounded-lg px-3 py-2 text-sm text-[#123B32] font-mono focus:ring-2 focus:ring-emerald-500 focus:outline-none"
          >
            {[9, 10, 11, 12, 13, 14, 15, 16, 17].map((h) => (
              <option key={h} value={h}>
                {String(h).padStart(2, '0')}:00 UTC {h === 11 ? '(UK Day-Ahead Standard)' : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Alignment Mode */}
        <div className="md:col-span-3 flex flex-col space-y-1.5">
          <label className="text-xs font-semibold text-[#35564D] flex items-center space-x-1.5">
            <Layers className="w-3.5 h-3.5 text-[#198754]" />
            <span>Interval Resolution</span>
          </label>
          <div className="flex bg-[#F7F9F7] p-1 rounded-lg border border-[#C9D6CC]">
            <button
              type="button"
              onClick={() => onAlignmentModeChange('half_hourly_expanded')}
              className={`flex-1 py-1 px-2 text-xs font-medium rounded-md transition ${
                alignmentMode === 'half_hourly_expanded'
                  ? 'bg-emerald-600 text-white shadow'
                  : 'text-[#64756D] hover:text-[#23483D]'
              }`}
            >
              30-min (48 HH)
            </button>
            <button
              type="button"
              onClick={() => onAlignmentModeChange('exact')}
              className={`flex-1 py-1 px-2 text-xs font-medium rounded-md transition ${
                alignmentMode === 'exact'
                  ? 'bg-emerald-600 text-white shadow'
                  : 'text-[#64756D] hover:text-[#23483D]'
              }`}
            >
              Hourly (24)
            </button>
          </div>
        </div>

        {/* Action Controls */}
        <div className="md:col-span-2 flex items-end justify-between md:justify-end space-x-2 pt-2 md:pt-0">
          <label className="flex items-center space-x-1.5 text-xs text-[#64756D] cursor-pointer select-none">
            <input
              type="checkbox"
              checked={forceFixture}
              onChange={(e) => onForceFixtureChange(e.target.checked)}
              className="rounded bg-[#F7F9F7] border-[#C9D6CC] text-emerald-500 focus:ring-0"
            />
            <span>Fixture</span>
          </label>

          <button
            onClick={onRefresh}
            disabled={loading}
            className="flex items-center space-x-1.5 px-3 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-md transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Evaluating...' : 'Recalculate'}</span>
          </button>
        </div>
      </div>

      {/* Preset Pills */}
      <div className="mt-3 pt-3 border-t border-[#DCE5DE]/60 flex flex-wrap items-center gap-2">
        <span className="text-xs text-[#738078]">Quick Presets:</span>
        <button
          onClick={() => onDateChange('2026-01-01')}
          className="text-xs px-2.5 py-0.5 rounded bg-[#EDF3EE] hover:bg-[#D9F0E3] text-[#35564D] border border-[#C9D6CC]/60 transition"
        >
          Jan 1st (Month Rollover)
        </button>
        <button
          onClick={() => onDateChange('2026-01-15')}
          className="text-xs px-2.5 py-0.5 rounded bg-[#EDF3EE] hover:bg-[#D9F0E3] text-[#35564D] border border-[#C9D6CC]/60 transition"
        >
          Jan 15th (Mid-Month Benchmark)
        </button>
        <button
          onClick={() => onDateChange('2026-01-31')}
          className="text-xs px-2.5 py-0.5 rounded bg-[#EDF3EE] hover:bg-[#D9F0E3] text-[#35564D] border border-[#C9D6CC]/60 transition"
        >
          Jan 31st (Month Close)
        </button>
      </div>
    </div>
  );
}
