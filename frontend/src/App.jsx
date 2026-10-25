import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import ControlBar from './components/ControlBar';
import MetricCards from './components/MetricCards';
import ActualVsForecastChart from './components/ActualVsForecastChart';
import ErrorAnalysisChart from './components/ErrorAnalysisChart';
import VintageEvolutionView from './components/VintageEvolutionView';
import IntervalTable from './components/IntervalTable';
import OperationalContext from './components/OperationalContext';
import { fetchHealth, fetchAnalysis } from './services/api';
import { AlertCircle, RefreshCw, BarChart2, GitBranch, Table } from 'lucide-react';

export default function App() {
  const [deliveryDate, setDeliveryDate] = useState('2026-01-15');
  const [cutoffHour, setCutoffHour] = useState(11);
  const [alignmentMode, setAlignmentMode] = useState('half_hourly_expanded');
  const [forceFixture, setForceFixture] = useState(false);

  const [health, setHealth] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [viewTab, setViewTab] = useState('dashboard'); // 'dashboard', 'vintages', 'table'

  // Fetch health status
  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((err) => console.warn('Health check unreachable:', err));
  }, []);

  // Fetch analysis data
  const loadAnalysis = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAnalysis({
        deliveryDate,
        cutoffHour,
        alignmentMode,
        forceFixture
      });
      setAnalysisData(data);
    } catch (err) {
      console.error('Failed to load analysis:', err);
      setError(err.message || 'An unexpected error occurred while fetching analysis.');
    } finally {
      setLoading(false);
    }
  }, [deliveryDate, cutoffHour, alignmentMode, forceFixture]);

  useEffect(() => {
    loadAnalysis();
  }, [loadAnalysis]);

  return (
    <div className="min-h-screen bg-[#F7F9F7] text-[#123B32] flex flex-col font-sans selection:bg-[#D9F0E3]">
      {/* Top Navigation & Status */}
      <Header
        health={health}
        isFixtureData={analysisData?.is_fixture_data || forceFixture}
        onOpenExplanation={() => setShowExplanation(true)}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        
        {/* Controls */}
        <ControlBar
          deliveryDate={deliveryDate}
          onDateChange={setDeliveryDate}
          cutoffHour={cutoffHour}
          onCutoffHourChange={setCutoffHour}
          alignmentMode={alignmentMode}
          onAlignmentModeChange={setAlignmentMode}
          forceFixture={forceFixture}
          onForceFixtureChange={setForceFixture}
          onRefresh={loadAnalysis}
          loading={loading}
        />

        {/* Error Banner */}
        {error && (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-200 flex items-start justify-between shadow-lg">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-bold">Analysis Request Failed</h4>
                <p className="text-xs text-red-300 mt-1">{error}</p>
                <p className="text-xs text-[#64756D] mt-1">
                  Tip: Check whether the live Elexon API is reachable or toggle the "Fixture" option to test with verified offline cache.
                </p>
              </div>
            </div>
            <button
              onClick={loadAnalysis}
              className="px-3 py-1 bg-red-600/30 hover:bg-red-600/50 border border-red-500/40 rounded-lg text-xs font-semibold transition"
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading Skeleton */}
        {loading && !analysisData && (
          <div className="h-96 flex flex-col items-center justify-center space-y-3 bg-[#F7F9F7] border border-[#DCE5DE] rounded-xl">
            <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin" />
            <p className="text-sm text-[#64756D] font-mono">
              Fetching Elexon streams and evaluating cutoff...
            </p>
          </div>
        )}

        {/* Loaded Content */}
        {analysisData && (
          <div className="space-y-6 animate-fadeIn">
            {/* KPI Summary Cards */}
            <MetricCards data={analysisData} />

            {/* View Tabs */}
            <div className="flex border-b border-[#DCE5DE] space-x-2">
              <button
                onClick={() => setViewTab('dashboard')}
                className={`flex items-center space-x-2 py-2.5 px-4 text-xs font-semibold border-b-2 transition ${
                  viewTab === 'dashboard'
                    ? 'border-emerald-500 text-emerald-400 bg-emerald-500/5'
                    : 'border-transparent text-[#64756D] hover:text-[#23483D]'
                }`}
              >
                <BarChart2 className="w-4 h-4" />
                <span>Primary Forecast Analysis</span>
              </button>
              <button
                onClick={() => setViewTab('vintages')}
                className={`flex items-center space-x-2 py-2.5 px-4 text-xs font-semibold border-b-2 transition ${
                  viewTab === 'vintages'
                    ? 'border-emerald-500 text-emerald-400 bg-emerald-500/5'
                    : 'border-transparent text-[#64756D] hover:text-[#23483D]'
                }`}
              >
                <GitBranch className="w-4 h-4" />
                <span>Forecast Vintage Evolution</span>
              </button>
              <button
                onClick={() => setViewTab('table')}
                className={`flex items-center space-x-2 py-2.5 px-4 text-xs font-semibold border-b-2 transition ${
                  viewTab === 'table'
                    ? 'border-emerald-500 text-emerald-400 bg-emerald-500/5'
                    : 'border-transparent text-[#64756D] hover:text-[#23483D]'
                }`}
              >
                <Table className="w-4 h-4" />
                <span>Interval Ledger</span>
              </button>
            </div>

            {/* Tab 1: Primary Dashboard Charts */}
            {viewTab === 'dashboard' && (
              <div className="space-y-6">
                <ActualVsForecastChart intervals={analysisData.intervals} />
                <ErrorAnalysisChart intervals={analysisData.intervals} />
                <IntervalTable
                  intervals={analysisData.intervals}
                  deliveryDate={analysisData.delivery_date}
                />
              </div>
            )}

            {/* Tab 2: Vintage Evolution */}
            {viewTab === 'vintages' && (
              <div className="space-y-6">
                <VintageEvolutionView
                  deliveryDate={deliveryDate}
                  cutoffHour={cutoffHour}
                  availableVintages={analysisData.available_vintages}
                  actualIntervals={analysisData.intervals}
                  forceFixture={forceFixture}
                />
              </div>
            )}

            {/* Tab 3: Interval Ledger Table */}
            {viewTab === 'table' && (
              <div className="space-y-6">
                <IntervalTable
                  intervals={analysisData.intervals}
                  deliveryDate={analysisData.delivery_date}
                />
              </div>
            )}

            {/* Transparency & Limitations Banner */}
            <div className="p-4 rounded-xl bg-[#F7F9F7] border border-[#DCE5DE] text-xs text-[#64756D] space-y-1">
              <span className="font-semibold text-[#35564D]">Data Integrity & Assumptions:</span>
              <ul className="list-disc pl-5 space-y-0.5 text-[#64756D]">
                {analysisData.data_limitations?.map((lim, idx) => (
                  <li key={idx}>{lim}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </main>

      {/* Operational Explanation Modal */}
      <OperationalContext
        isOpen={showExplanation}
        onClose={() => setShowExplanation(false)}
      />

      {/* Footer */}
      <footer className="border-t border-[#DCE5DE] bg-[#F7F9F7] py-4 text-center text-xs text-[#738078]">
        <p>
          UK National Wind Generation Forecast & Day-Ahead Procurement Analysis Portal · Built with React & FastAPI · Data from Elexon BMRS
        </p>
      </footer>
    </div>
  );
}
