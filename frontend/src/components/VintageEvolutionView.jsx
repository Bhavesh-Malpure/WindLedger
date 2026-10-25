import React, { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import { GitBranch, Clock, CheckCircle, XCircle } from 'lucide-react';
import { fetchVintageComparison } from '../services/api';

const VINTAGE_COLORS = [
  '#f59e0b', // amber
  '#3b82f6', // blue
  '#c2410c', // burnt orange
  '#10b981', // emerald
  '#0f766e', // teal
  '#14b8a6', // teal
  '#f97316', // orange
];

export default function VintageEvolutionView({
  deliveryDate,
  cutoffHour,
  availableVintages,
  actualIntervals,
  forceFixture
}) {
  const [vintageData, setVintageData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedVintages, setSelectedVintages] = useState([]);

  useEffect(() => {
    let isMounted = true;
    async function loadVintages() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchVintageComparison({
          deliveryDate,
          cutoffHour,
          forceFixture
        });
        if (isMounted) {
          setVintageData(res);
          const keys = Object.keys(res.vintages || {});
          // Default select the latest 3-4 vintages to avoid clutter
          setSelectedVintages(keys.slice(-4));
        }
      } catch (err) {
        if (isMounted) setError(err.message);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadVintages();
    return () => {
      isMounted = false;
    };
  }, [deliveryDate, cutoffHour, forceFixture]);

  // Combine actuals with selected vintages into single series for recharts
  const chartPoints = (actualIntervals || []).map((it) => {
    const d = new Date(it.start_time);
    const timeKey = `${String(d.getUTCHours()).padStart(2, '0')}:${String(d.getUTCMinutes()).padStart(2, '0')}`;
    const point = {
      formattedTime: timeKey,
      start_time: it.start_time,
      actual_generation_mw: it.actual_generation_mw
    };

    if (vintageData?.vintages) {
      selectedVintages.forEach((vKey) => {
        const series = vintageData.vintages[vKey] || [];
        const match = series.find(
          (s) => new Date(s.start_time).getTime() === new Date(it.start_time).getTime()
        );
        if (match) {
          point[vKey] = match.forecast_generation_mw;
        } else if (it.start_time.endsWith(':30:00Z')) {
          // If hourly forecast, map to half-hour
          const hourMatch = series.find(
            (s) => new Date(s.start_time).getTime() === new Date(it.start_time.replace(':30:00Z', ':00:00Z')).getTime()
          );
          if (hourMatch) point[vKey] = hourMatch.forecast_generation_mw;
        }
      });
    }

    return point;
  });

  return (
    <div className="bg-white border border-[#DCE5DE] rounded-xl p-5 shadow-lg backdrop-blur-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <h2 className="text-sm font-bold text-[#123B32] flex items-center space-x-2">
            <GitBranch className="w-4 h-4 text-[#198754]" />
            <span>Forecast Vintage Evolution Leading Up to Decision Cutoff</span>
          </h2>
          <p className="text-xs text-[#64756D]">
            Compare forecast model runs published across D-2 and D-1 to observe model convergence prior to auction gate closure.
          </p>
        </div>
      </div>

      {loading && (
        <div className="h-64 flex items-center justify-center text-xs text-[#64756D]">
          Loading forecast vintages...
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-xs">
          Failed to load vintage comparison: {error}
        </div>
      )}

      {!loading && !error && vintageData && (
        <div className="space-y-4">
          {/* Vintage Selection Pills */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-[#64756D] font-medium">Select Vintages:</span>
            {Object.keys(vintageData.vintages || {}).map((vKey, idx) => {
              const isSelected = selectedVintages.includes(vKey);
              const color = VINTAGE_COLORS[idx % VINTAGE_COLORS.length];
              return (
                <button
                  key={vKey}
                  type="button"
                  onClick={() => {
                    if (isSelected) {
                      setSelectedVintages(selectedVintages.filter((k) => k !== vKey));
                    } else {
                      setSelectedVintages([...selectedVintages, vKey]);
                    }
                  }}
                  className={`text-xs px-2.5 py-1 rounded-md font-mono border transition flex items-center space-x-1.5 ${
                    isSelected
                      ? 'bg-[#D9F0E3] text-[#123B32] border-[#AFC2B5] shadow'
                      : 'bg-[#F7F9F7] text-[#738078] border-[#DCE5DE] hover:text-[#35564D]'
                  }`}
                >
                  <span
                    className="w-2.5 h-2.5 rounded-full inline-block"
                    style={{ backgroundColor: isSelected ? color : '#475569' }}
                  />
                  <span>{vKey}</span>
                </button>
              );
            })}
          </div>

          {/* Chart */}
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartPoints} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#DCE5DE" />
                <XAxis
                  dataKey="formattedTime"
                  stroke="#738078"
                  tick={{ fontSize: 11, fill: '#64756D' }}
                />
                <YAxis
                  stroke="#738078"
                  tick={{ fontSize: 11, fill: '#64756D' }}
                  tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`}
                  unit=" MW"
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#C9D6CC', fontSize: '12px' }}
                />
                <Line
                  type="monotone"
                  dataKey="actual_generation_mw"
                  name="Actual Outturn"
                  stroke="#10b981"
                  strokeWidth={2.5}
                  dot={false}
                />
                {selectedVintages.map((vKey, idx) => (
                  <Line
                    key={vKey}
                    type="monotone"
                    dataKey={vKey}
                    name={vKey}
                    stroke={VINTAGE_COLORS[idx % VINTAGE_COLORS.length]}
                    strokeWidth={1.5}
                    strokeDasharray="3 3"
                    dot={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Metadata Table of All Vintages */}
          <div className="mt-4 pt-3 border-t border-[#DCE5DE]">
            <h3 className="text-xs font-semibold text-[#35564D] mb-2">
              Publication Vintages Log (Cutoff Gate Enforcement)
            </h3>
            <div className="max-h-40 overflow-y-auto rounded-lg border border-[#DCE5DE] text-xs font-mono">
              <table className="w-full text-left">
                <thead className="bg-[#F7F9F7] text-[#64756D] sticky top-0">
                  <tr>
                    <th className="py-2 px-3">Publication Time (UTC)</th>
                    <th className="py-2 px-3">Forecast Intervals</th>
                    <th className="py-2 px-3">Cutoff Status</th>
                    <th className="py-2 px-3">Role</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#DCE5DE] bg-[#F7F9F7]">
                  {(availableVintages || []).map((v) => (
                    <tr key={v.publish_time} className={v.is_selected ? 'bg-emerald-500/10' : ''}>
                      <td className="py-1.5 px-3 text-[#23483D]">
                        {new Date(v.publish_time).toISOString().replace('.000Z', ' UTC')}
                      </td>
                      <td className="py-1.5 px-3 text-[#64756D]">{v.intervals_count} intervals</td>
                      <td className="py-1.5 px-3">
                        {v.is_eligible ? (
                          <span className="text-emerald-400 inline-flex items-center space-x-1">
                            <CheckCircle className="w-3 h-3" />
                            <span>Eligible (Published &le; Cutoff)</span>
                          </span>
                        ) : (
                          <span className="text-red-400 inline-flex items-center space-x-1">
                            <XCircle className="w-3 h-3" />
                            <span>Rejected (Post-Cutoff Leakage)</span>
                          </span>
                        )}
                      </td>
                      <td className="py-1.5 px-3">
                        {v.is_selected ? (
                          <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-semibold text-[10px]">
                            Latest Decision Vintage
                          </span>
                        ) : (
                          <span className="text-[#738078]">Historical Run</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
