import React from 'react';
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
import { Zap } from 'lucide-react';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const dataPoint = payload[0].payload;
    const actual = dataPoint.actual_generation_mw;
    const forecast = dataPoint.forecast_generation_mw;
    const error = dataPoint.error_mw;

    return (
      <div className="bg-white border border-[#C9D6CC] p-3 rounded-lg shadow-xl text-xs font-mono space-y-1">
        <div className="font-bold text-[#23483D] border-b border-[#DCE5DE] pb-1 flex justify-between">
          <span>SP {dataPoint.settlement_period}</span>
          <span>{dataPoint.formattedTime} UTC</span>
        </div>
        <div className="text-emerald-400 flex justify-between space-x-4">
          <span>Actual Wind:</span>
          <span className="font-bold">{actual != null ? `${actual.toLocaleString()} MW` : 'Missing'}</span>
        </div>
        <div className="text-[#198754] flex justify-between space-x-4">
          <span>Forecast Wind:</span>
          <span className="font-bold">{forecast != null ? `${forecast.toLocaleString()} MW` : 'Missing'}</span>
        </div>
        {error != null && (
          <div className={`flex justify-between space-x-4 pt-1 border-t border-[#DCE5DE] ${
            error > 0 ? 'text-amber-400' : 'text-cyan-400'
          }`}>
            <span>Delta (F - A):</span>
            <span className="font-bold">{error > 0 ? `+${error.toLocaleString()}` : error.toLocaleString()} MW</span>
          </div>
        )}
      </div>
    );
  }
  return null;
};

export default function ActualVsForecastChart({ intervals }) {
  if (!intervals || intervals.length === 0) {
    return (
      <div className="h-72 flex items-center justify-center bg-[#F7F9F7] border border-[#DCE5DE] rounded-xl text-[#738078] text-sm">
        No interval data available for the selected parameters.
      </div>
    );
  }

  // Format data for chart
  const chartData = intervals.map((it) => {
    const d = new Date(it.start_time);
    const hours = String(d.getUTCHours()).padStart(2, '0');
    const mins = String(d.getUTCMinutes()).padStart(2, '0');
    return {
      ...it,
      formattedTime: `${hours}:${mins}`
    };
  });

  return (
    <div className="bg-white border border-[#DCE5DE] rounded-xl p-5 shadow-lg backdrop-blur-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <h2 className="text-sm font-bold text-[#123B32] flex items-center space-x-2">
            <Zap className="w-4 h-4 text-emerald-400" />
            <span>Actual Wind Generation vs Latest Day-Ahead Forecast</span>
          </h2>
          <p className="text-xs text-[#64756D]">
            Outturn Elexon FUELHH (WIND) aligned with WINDFOR forecast published prior to day-ahead auction cutoff.
          </p>
        </div>
        <div className="flex items-center space-x-4 text-xs font-mono">
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-0.5 bg-emerald-400 inline-block rounded-full"></span>
            <span className="text-[#35564D]">Actual (MW)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-0.5 bg-[#198754] border-dashed border-b-2 border-[#198754] inline-block"></span>
            <span className="text-[#35564D]">Day-Ahead Forecast (MW)</span>
          </div>
        </div>
      </div>

      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#DCE5DE" />
            <XAxis
              dataKey="formattedTime"
              stroke="#738078"
              tick={{ fontSize: 11, fill: '#64756D' }}
              tickLine={{ stroke: '#334155' }}
            />
            <YAxis
              stroke="#738078"
              tick={{ fontSize: 11, fill: '#64756D' }}
              tickLine={{ stroke: '#334155' }}
              tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`}
              unit=" MW"
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="actual_generation_mw"
              name="Actual Generation"
              stroke="#10b981"
              strokeWidth={2.5}
              dot={{ r: 2, fill: '#10b981' }}
              activeDot={{ r: 5 }}
            />
            <Line
              type="monotone"
              dataKey="forecast_generation_mw"
              name="Forecast Generation"
              stroke="#123B32"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={{ r: 2, fill: '#123B32' }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
