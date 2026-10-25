import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Cell
} from 'recharts';
import { BarChart3 } from 'lucide-react';

const CustomErrorTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const dataPoint = payload[0].payload;
    const error = dataPoint.error_mw;
    const isOver = error > 0;

    return (
      <div className="bg-white border border-[#C9D6CC] p-3 rounded-lg shadow-xl text-xs font-mono space-y-1">
        <div className="font-bold text-[#23483D] border-b border-[#DCE5DE] pb-1 flex justify-between">
          <span>SP {dataPoint.settlement_period}</span>
          <span>{dataPoint.formattedTime} UTC</span>
        </div>
        <div className={`flex justify-between space-x-4 ${isOver ? 'text-amber-400' : 'text-cyan-400'}`}>
          <span>Forecast Error (F - A):</span>
          <span className="font-bold">{error > 0 ? `+${error.toLocaleString()}` : error.toLocaleString()} MW</span>
        </div>
        <div className="text-[#64756D] text-[11px] pt-1 border-t border-[#DCE5DE]">
          {isOver 
            ? 'Short Position Risk: Actual wind fell short of procurement expectation.' 
            : 'Long Position: Wind exceeded forecast; excess energy delivered.'}
        </div>
      </div>
    );
  }
  return null;
};

export default function ErrorAnalysisChart({ intervals }) {
  if (!intervals || intervals.length === 0) return null;

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
            <BarChart3 className="w-4 h-4 text-amber-400" />
            <span>Hourly Forecast Error Distribution (Delta = Forecast - Actual)</span>
          </h2>
          <p className="text-xs text-[#64756D]">
            Amber bars indicate over-forecast (deficit volume); Cyan bars indicate under-forecast (surplus volume).
          </p>
        </div>
        <div className="flex items-center space-x-4 text-xs font-mono">
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 bg-amber-500/80 inline-block rounded-sm"></span>
            <span className="text-[#35564D]">Over-Forecast (+MW)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 bg-cyan-500/80 inline-block rounded-sm"></span>
            <span className="text-[#35564D]">Under-Forecast (-MW)</span>
          </div>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
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
            <Tooltip content={<CustomErrorTooltip />} />
            <ReferenceLine y={0} stroke="#738078" strokeWidth={1} />
            <Bar dataKey="error_mw" name="Forecast Error">
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={(entry.error_mw || 0) >= 0 ? '#f59e0b' : '#06b6d4'}
                  opacity={0.85}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
