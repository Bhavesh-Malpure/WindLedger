import React from 'react';
import { X, BookOpen, ShieldAlert, Cpu, Award } from 'lucide-react';

export default function OperationalContext({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#123B32]/40 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white border border-[#C9D6CC] max-w-3xl w-full rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        {/* Modal Header */}
        <div className="p-4 sm:p-5 border-b border-[#DCE5DE] flex items-center justify-between bg-[#F7F9F7]">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#123B32]">
                Operational Procurement Guide & Domain Reference
              </h3>
              <p className="text-xs text-[#64756D]">
                UK Day-Ahead Power Wholesale Market · January 2026 Verification Framework
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-[#64756D] hover:text-[#123B32] hover:bg-[#EDF3EE] transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-5 sm:p-6 overflow-y-auto space-y-5 text-xs text-[#35564D] leading-relaxed font-sans">
          
          {/* Section 1: The Core Question */}
          <div className="bg-[#F7F9F7] p-4 rounded-xl border border-[#DCE5DE] space-y-2">
            <h4 className="text-sm font-semibold text-emerald-400 flex items-center space-x-2">
              <Award className="w-4 h-4" />
              <span>Core Operational Decision Question</span>
            </h4>
            <p>
              When a UK power utility's day-ahead desk submits purchase orders into wholesale power auctions (such as EPEX SPOT or Nord Pool) on the morning prior to delivery ($D-1$), they must commit capital and thermal generation contracts based on <strong>expected renewable generation</strong>.
            </p>
            <p className="text-[#64756D]">
              This portal answers the fundamental operational question: <em>"Using only information that was actually in the trader's hands at the day-ahead auction deadline, how well did the latest available wind forecast predict actual delivery?"</em>
            </p>
          </div>

          {/* Section 2: Zero Look-Ahead Bias & Cutoff Rules */}
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-[#123B32] flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-blue-400" />
              <span>Auction Cutoff Enforcement & Leakage Prevention</span>
            </h4>
            <p>
              In historical analysis, trading desks often suffer from <strong>look-ahead leakage</strong>: evaluating an outturn delivery against a forecast published <em>after</em> bids were submitted.
            </p>
            <ul className="list-disc pl-5 space-y-1 text-[#64756D]">
              <li><strong>Default Auction Cutoff:</strong> 11:00 UTC on $D-1$ (configurable to 12:00 or other hours).</li>
              <li><strong>Strict Leakage Filter:</strong> Any forecast record where <code className="text-emerald-300 font-mono">publishTime &gt; cutoff</code> is strictly excluded from decision analysis.</li>
              <li><strong>Latest Vintage Picking:</strong> Among all forecasts published prior to cutoff, the system selects the most recent vintage covering each interval.</li>
            </ul>
          </div>

          {/* Section 3: Metric Definitions & Zero-Safety */}
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-[#123B32] flex items-center space-x-2">
              <Cpu className="w-4 h-4 text-[#198754]" />
              <span>Statistical & Operational Metric Definitions</span>
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              <div className="bg-[#F7F9F7] p-3 rounded-lg border border-[#DCE5DE]">
                <span className="font-bold text-[#23483D]">MAE (Mean Absolute Error):</span>
                <p className="text-[#64756D] mt-1">Average absolute MW deviation per interval: <code>(1/N) * &Sigma; |F - A|</code>. Represents typical volume error.</p>
              </div>
              <div className="bg-[#F7F9F7] p-3 rounded-lg border border-[#DCE5DE]">
                <span className="font-bold text-[#23483D]">RMSE (Root Mean Square Error):</span>
                <p className="text-[#64756D] mt-1">Penalizes large errors quadratically: <code>&radic;[(1/N) * &Sigma; (F - A)&sup2;]</code>. Critical for assessing balancing cash-out risk during extreme weather events.</p>
              </div>
              <div className="bg-[#F7F9F7] p-3 rounded-lg border border-[#DCE5DE]">
                <span className="font-bold text-[#23483D]">Bias (Mean Error):</span>
                <p className="text-[#64756D] mt-1">Net error: <code>(1/N) * &Sigma; (F - A)</code>. Positive indicates over-forecast (short risk); negative indicates under-forecast (surplus).</p>
              </div>
              <div className="bg-[#F7F9F7] p-3 rounded-lg border border-[#DCE5DE]">
                <span className="font-bold text-[#23483D]">WAPE (Weighted Abs % Error):</span>
                <p className="text-[#64756D] mt-1"><code>(&Sigma; |F - A| / &Sigma; A) * 100%</code>. Avoids division-by-zero during wind calms (where standard MAPE explodes to infinity).</p>
              </div>
            </div>
          </div>

          {/* Section 4: Operational Limitations Caveat */}
          <div className="bg-amber-500/10 border border-amber-500/30 p-3.5 rounded-xl text-amber-200 space-y-1">
            <div className="font-bold flex items-center space-x-1.5">
              <span>Operational Scope Caveat</span>
            </div>
            <p className="text-[11px] leading-relaxed text-amber-300/90">
              This application is an energy-data forecast evaluation tool, not a full procurement or dispatch optimizer. Forecast error directly impacts imbalance exposure, but total purchase volume in wholesale markets also depends on consumer demand profiles, interconnector imports/exports, thermal generator minimum stable generation (MSG) levels, and Balancing Mechanism (BM) pricing rules.
            </p>
          </div>

        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-[#DCE5DE] bg-[#F7F9F7] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs rounded-lg transition"
          >
            Acknowledge & Close
          </button>
        </div>
      </div>
    </div>
  );
}
