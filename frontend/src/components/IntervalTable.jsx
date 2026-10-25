import React, { useState } from 'react';
import { Download, Table as TableIcon, Search, ArrowUpDown } from 'lucide-react';

export default function IntervalTable({ intervals, deliveryDate }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('settlement_period');
  const [sortDesc, setSortDesc] = useState(false);

  if (!intervals || intervals.length === 0) return null;

  // Filter intervals by search
  const filtered = intervals.filter((it) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    const spMatch = it.settlement_period?.toString().includes(term);
    const timeMatch = it.start_time?.toLowerCase().includes(term);
    const statusMatch = it.status?.toLowerCase().includes(term);
    return spMatch || timeMatch || statusMatch;
  });

  // Sort intervals
  const sorted = [...filtered].sort((a, b) => {
    let aVal = a[sortBy];
    let bVal = b[sortBy];

    if (aVal === null || aVal === undefined) return 1;
    if (bVal === null || bVal === undefined) return -1;

    if (typeof aVal === 'string') {
      return sortDesc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
    }
    return sortDesc ? bVal - aVal : aVal - bVal;
  });

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortDesc(!sortDesc);
    } else {
      setSortBy(field);
      setSortDesc(false);
    }
  };

  const exportToCsv = () => {
    const headers = [
      'SettlementPeriod',
      'StartTimeUTC',
      'ActualGenerationMW',
      'ForecastGenerationMW',
      'ForecastPublishTimeUTC',
      'ErrorMW',
      'AbsoluteErrorMW',
      'PercentageError',
      'Status'
    ];

    const rows = intervals.map((it) => [
      it.settlement_period ?? '',
      it.start_time ?? '',
      it.actual_generation_mw ?? '',
      it.forecast_generation_mw ?? '',
      it.forecast_publish_time ?? '',
      it.error_mw ?? '',
      it.absolute_error_mw ?? '',
      it.percentage_error != null ? `${it.percentage_error}%` : 'N/A',
      it.status ?? ''
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `uk_wind_analysis_${deliveryDate}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="bg-white border border-[#DCE5DE] rounded-xl p-5 shadow-lg backdrop-blur-sm">
      {/* Table Header and Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h2 className="text-sm font-bold text-[#123B32] flex items-center space-x-2">
            <TableIcon className="w-4 h-4 text-emerald-400" />
            <span>Delivery Interval Verification Table</span>
          </h2>
          <p className="text-xs text-[#64756D]">
            Granular 30-minute settlement period ledger with exact outturn, forecast, delta, and status.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {/* Search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-[#64756D] absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter by SP / Time..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-[#F7F9F7] border border-[#C9D6CC] rounded-lg pl-8 pr-3 py-1.5 text-xs text-[#23483D] focus:outline-none focus:ring-1 focus:ring-emerald-500 w-36 sm:w-48 font-mono"
            />
          </div>

          {/* Export to CSV */}
          <button
            onClick={exportToCsv}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-[#EDF3EE] hover:bg-[#D9F0E3] text-[#23483D] border border-[#C9D6CC] rounded-lg text-xs font-medium transition"
          >
            <Download className="w-3.5 h-3.5 text-emerald-400" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto max-h-96 rounded-lg border border-[#DCE5DE] font-mono text-xs">
        <table className="w-full text-left divide-y divide-[#DCE5DE]">
          <thead className="bg-[#F7F9F7] text-[#64756D] sticky top-0 z-10 select-none">
            <tr>
              <th
                onClick={() => handleSort('settlement_period')}
                className="py-2.5 px-3 cursor-pointer hover:text-[#23483D]"
              >
                <div className="flex items-center space-x-1">
                  <span>SP</span>
                  <ArrowUpDown className="w-3 h-3 text-[#87958C]" />
                </div>
              </th>
              <th
                onClick={() => handleSort('start_time')}
                className="py-2.5 px-3 cursor-pointer hover:text-[#23483D]"
              >
                <div className="flex items-center space-x-1">
                  <span>Start Time (UTC)</span>
                  <ArrowUpDown className="w-3 h-3 text-[#87958C]" />
                </div>
              </th>
              <th
                onClick={() => handleSort('actual_generation_mw')}
                className="py-2.5 px-3 text-right cursor-pointer hover:text-[#23483D]"
              >
                <div className="flex items-center justify-end space-x-1">
                  <span>Actual (MW)</span>
                  <ArrowUpDown className="w-3 h-3 text-[#87958C]" />
                </div>
              </th>
              <th
                onClick={() => handleSort('forecast_generation_mw')}
                className="py-2.5 px-3 text-right cursor-pointer hover:text-[#23483D]"
              >
                <div className="flex items-center justify-end space-x-1">
                  <span>Forecast (MW)</span>
                  <ArrowUpDown className="w-3 h-3 text-[#87958C]" />
                </div>
              </th>
              <th
                onClick={() => handleSort('error_mw')}
                className="py-2.5 px-3 text-right cursor-pointer hover:text-[#23483D]"
              >
                <div className="flex items-center justify-end space-x-1">
                  <span>Error (MW)</span>
                  <ArrowUpDown className="w-3 h-3 text-[#87958C]" />
                </div>
              </th>
              <th
                onClick={() => handleSort('percentage_error')}
                className="py-2.5 px-3 text-right cursor-pointer hover:text-[#23483D]"
              >
                <div className="flex items-center justify-end space-x-1">
                  <span>Error (%)</span>
                  <ArrowUpDown className="w-3 h-3 text-[#87958C]" />
                </div>
              </th>
              <th className="py-2.5 px-3 text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#DCE5DE] bg-[#F7F9F7]">
            {sorted.map((it) => {
              const d = new Date(it.start_time);
              const timeStr = `${String(d.getUTCHours()).padStart(2, '0')}:${String(d.getUTCMinutes()).padStart(2, '0')}`;
              const isOver = (it.error_mw || 0) > 0;

              return (
                <tr key={it.start_time} className="hover:bg-[#EDF3EE] transition">
                  <td className="py-2 px-3 text-[#64756D] font-semibold">{it.settlement_period}</td>
                  <td className="py-2 px-3 text-[#23483D]">{timeStr} UTC</td>
                  <td className="py-2 px-3 text-right font-medium text-emerald-400">
                    {it.actual_generation_mw != null
                      ? it.actual_generation_mw.toLocaleString()
                      : <span className="text-[#738078] italic">None</span>}
                  </td>
                  <td className="py-2 px-3 text-right font-medium text-[#198754]">
                    {it.forecast_generation_mw != null
                      ? it.forecast_generation_mw.toLocaleString()
                      : <span className="text-[#738078] italic">None</span>}
                  </td>
                  <td
                    className={`py-2 px-3 text-right font-bold ${
                      it.error_mw == null
                        ? 'text-[#738078]'
                        : isOver
                        ? 'text-amber-400'
                        : 'text-cyan-400'
                    }`}
                  >
                    {it.error_mw != null
                      ? `${isOver ? '+' : ''}${it.error_mw.toLocaleString()}`
                      : '—'}
                  </td>
                  <td className="py-2 px-3 text-right text-[#35564D]">
                    {it.percentage_error != null ? `${it.percentage_error}%` : '—'}
                  </td>
                  <td className="py-2 px-3 text-center">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        it.status === 'MATCHED'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
                      }`}
                    >
                      {it.status}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
