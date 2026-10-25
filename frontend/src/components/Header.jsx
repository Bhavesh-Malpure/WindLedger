import React from 'react';
import { Wind, ShieldCheck, AlertCircle, Info, Database } from 'lucide-react';

export default function Header({ health, isFixtureData, onOpenExplanation }) {
  return (
    <header className="border-b border-[#DCE5DE] bg-white/95 backdrop-blur-md sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        {/* Title and Identity */}
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400">
            <Wind className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold text-[#123B32] tracking-tight">
                UK National Wind Forecast Portal
              </h1>
              <span className="px-2 py-0.5 text-xs font-semibold bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-full">
                January 2026
              </span>
            </div>
            <p className="text-xs text-[#64756D]">
              Day-Ahead Electricity Procurement Decision Evaluation Desk · Elexon BMRS Live Stream
            </p>
          </div>
        </div>

        {/* Status badges and Explanation trigger */}
        <div className="flex items-center space-x-3">
          {/* Health Status */}
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs bg-[#EDF3EE] border border-[#C9D6CC]/60 text-[#35564D]">
            <span className={`w-2 h-2 rounded-full ${health?.status === 'ok' ? 'bg-emerald-400' : 'bg-amber-400 animate-ping'}`} />
            <span>API: {health?.status === 'ok' ? 'Connected' : 'Connecting...'}</span>
          </div>

          {/* Fixture / Live Mode indicator */}
          <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs border ${
            isFixtureData 
              ? 'bg-amber-500/10 border-amber-500/30 text-amber-300' 
              : 'bg-blue-500/10 border-blue-500/30 text-blue-300'
          }`}>
            <Database className="w-3.5 h-3.5" />
            <span>{isFixtureData ? 'Verified Fixture Mode' : 'Live Elexon Stream'}</span>
          </div>

          {/* Transparency / Context Guide Button */}
          <button
            onClick={onOpenExplanation}
            className="flex items-center space-x-1.5 px-3 py-1 bg-[#EDF3EE] hover:bg-[#D9F0E3] text-[#23483D] hover:text-[#123B32] rounded-md text-xs font-medium border border-[#C9D6CC] transition"
          >
            <Info className="w-3.5 h-3.5 text-emerald-400" />
            <span>Operational Guide</span>
          </button>
        </div>
      </div>
    </header>
  );
}
