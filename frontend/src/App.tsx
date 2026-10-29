import { useState, useEffect, useCallback } from 'react';
import type { FormEvent, ChangeEvent } from 'react';
import { 
  ShieldAlert, CheckCircle2, AlertTriangle, 
  RefreshCw, Clock, Sparkles, Download
} from 'lucide-react';
import { apiClient } from './services/api';
import type { 
  Dataset, DataQualityReport, KPIResult, 
  ForecastResponse, AnomalyResponse, SegmentationResponse, AskDataResponse,
  CausalResponse, StressAuditResponse, ShapExplainResponse, GoalSeekResponse
} from './services/api';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, AreaChart, Area, Legend
} from 'recharts';
import { Sidebar } from './components/Sidebar';
import { TAB_CONFIG } from './types/navigation';
import type { TabType } from './types/navigation';
import { Navbar } from './components/Navbar';
import { AuthModal } from './components/auth/AuthModal';
import { CompanyDNAWizard } from './components/company/CompanyDNAWizard';
import type { CompanyProfile } from './services/api';

import { DataSourcesTab } from './components/tabs/DataSourcesTab';
import { ContractsGatesTab } from './components/tabs/ContractsGatesTab';
import { LineageTab } from './components/tabs/LineageTab';
import { MetricsStoreTab } from './components/tabs/MetricsStoreTab';
import { DigitalTwinTab } from './components/tabs/DigitalTwinTab';
import { MLOpsRegistryTab } from './components/tabs/MLOpsRegistryTab';
import { GovernanceABACTab } from './components/tabs/GovernanceABACTab';
import { OperationsCenterTab } from './components/tabs/OperationsCenterTab';

export default function App() {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Auth state
  const [currentUser, setCurrentUser] = useState<any>(() => {
    try {
      const saved = localStorage.getItem('bizinsight_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [isAuthOpen, setIsAuthOpen] = useState<boolean>(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(false);
  const [companyProfile, setCompanyProfile] = useState<CompanyProfile | null>(null);
  const [isCompanyDNAOpen, setIsCompanyDNAOpen] = useState<boolean>(false);

  useEffect(() => {
    const fetchCompanyProfile = async () => {
      try {
        const res = await apiClient.get<CompanyProfile | null>('/company/profile');
        if (res.data) {
          setCompanyProfile(res.data);
        } else if (currentUser) {
          setIsCompanyDNAOpen(true);
        }
      } catch (err) {
        console.error('Failed to load company profile:', err);
      }
    };
    fetchCompanyProfile();
  }, [currentUser]);

  // Module state
  const [qualityReport, setQualityReport] = useState<DataQualityReport | null>(null);
  const [kpiData, setKpiData] = useState<KPIResult | null>(null);
  const [forecastData, setForecastData] = useState<ForecastResponse | null>(null);
  const [forecastDateCol, setForecastDateCol] = useState<string>('');
  const [forecastTargetCol, setForecastTargetCol] = useState<string>('');
  const [availableCols, setAvailableCols] = useState<string[]>([]);
  const [anomalyData, setAnomalyData] = useState<AnomalyResponse | null>(null);
  const [segmentData, setSegmentData] = useState<SegmentationResponse | null>(null);
  const [causalData, setCausalData] = useState<CausalResponse | null>(null);
  const [causalDriver, setCausalDriver] = useState<string>('');
  const [perturbationPct, setPerturbationPct] = useState<number>(10);
  const [stressAuditData, setStressAuditData] = useState<StressAuditResponse | null>(null);
  const [askQuestion, setAskQuestion] = useState<string>('');
  const [askResponse, setAskResponse] = useState<AskDataResponse | null>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  // Novelty Engines 3 & 4: SHAP Explainability & Goal-Seek
  const [shapData, setShapData] = useState<ShapExplainResponse | null>(null);
  const [shapRecordIndex, setShapRecordIndex] = useState<number>(0);
  const [goalSeekData, setGoalSeekData] = useState<GoalSeekResponse | null>(null);
  const [targetGoalInput, setTargetGoalInput] = useState<number>(0);
  const [isExportingPdf, setIsExportingPdf] = useState<boolean>(false);

  const fetchDatasets = useCallback(async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<Dataset[]>('/datasets');
      setDatasets(res.data);
      if (res.data.length > 0 && !selectedDatasetId) {
        setSelectedDatasetId(res.data[0].id);
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [selectedDatasetId]);

  const loadTabData = useCallback(async (tab: TabType, datasetId: number) => {
    setErrorMsg(null);
    if (['data_sources', 'contracts_gates', 'lineage', 'metrics_store', 'digital_twin', 'mlops_registry', 'governance_abac', 'operations_center'].includes(tab)) {
      return;
    }
    setLoading(true);
    try {
      if (tab === 'quality') {
        const res = await apiClient.get<DataQualityReport>(`/datasets/${datasetId}/quality`);
        setQualityReport(res.data);
      } else if (tab === 'analytics' || tab === 'overview') {
        const res = await apiClient.get<KPIResult>(`/datasets/${datasetId}/analytics`);
        setKpiData(res.data);
      } else if (tab === 'forecasting') {
        const kpiRes = await apiClient.get<KPIResult>(`/datasets/${datasetId}/analytics`);
        setKpiData(kpiRes.data);
        const cols = kpiRes.data.available_columns || [];
        setAvailableCols(cols);
        
        const dateCol = kpiRes.data.date_metric || '';
        const targetCol = kpiRes.data.primary_metric || (cols.length > 0 ? cols[0] : '');
        setForecastDateCol(dateCol);
        setForecastTargetCol(targetCol);

        if (!dateCol) {
          setForecastData({
            status: 'rejected',
            message: `The active dataset does not contain an identified temporal (date/time) column. Time-series forecasting requires a sequential time axis (e.g. 'Date', 'Year', 'timestamp'). Please select a time-series dataset (such as 'wti_crude_oil_daily_prices.csv' or 'global_gdp_real.csv') or map a date column manually below.`
          });
        } else {
          const fRes = await apiClient.post<ForecastResponse>(`/datasets/${datasetId}/forecast`, {
            date_column: dateCol,
            target_column: targetCol,
            forecast_horizon: 14,
            frequency: 'D'
          });
          setForecastData(fRes.data);
        }
      } else if (tab === 'anomalies') {
        const aRes = await apiClient.post<AnomalyResponse>(`/datasets/${datasetId}/anomalies`, {
          contamination: 0.05
        });
        setAnomalyData(aRes.data);
      } else if (tab === 'segmentation') {
        const sRes = await apiClient.post<SegmentationResponse>(`/datasets/${datasetId}/segmentation`, {
          customer_id_col: 'customer_id',
          date_col: 'transaction_date',
          monetary_col: 'revenue',
          n_clusters: 4
        });
        setSegmentData(sRes.data);
      } else if (tab === 'causal') {
        const cRes = await apiClient.post<CausalResponse>(`/datasets/${datasetId}/causal-simulation?perturbation_pct=${perturbationPct}`);
        setCausalData(cRes.data);
        if (cRes.data.intervention_driver) {
          setCausalDriver(cRes.data.intervention_driver);
        }
      } else if (tab === 'stress_drift') {
        const dRes = await apiClient.get<StressAuditResponse>(`/datasets/${datasetId}/stress-audit`);
        setStressAuditData(dRes.data);
      } else if (tab === 'shap_explain') {
        const sRes = await apiClient.post<ShapExplainResponse>(`/datasets/${datasetId}/shap-explain?record_index=${shapRecordIndex}`);
        setShapData(sRes.data);
      } else if (tab === 'goal_seek') {
        const gRes = await apiClient.post<GoalSeekResponse>(`/datasets/${datasetId}/goal-seek`, {});
        setGoalSeekData(gRes.data);
        if (gRes.data.target_goal_value) {
          setTargetGoalInput(gRes.data.target_goal_value);
        }
      } else if (tab === 'audit') {
        const logsRes = await apiClient.get<any[]>('/audit-logs');
        setAuditLogs(logsRes.data);
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Operation failed';
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  }, [perturbationPct, shapRecordIndex]);

  // Load datasets on mount
  useEffect(() => {
    fetchDatasets();
  }, [fetchDatasets]);

  // When selected dataset changes, reload current tab data
  useEffect(() => {
    if (selectedDatasetId) {
      loadTabData(activeTab, selectedDatasetId);
    }
  }, [selectedDatasetId, activeTab, loadTabData]);

  const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('description', `Uploaded from UI: ${file.name}`);

    try {
      setLoading(true);
      const res = await apiClient.post<Dataset>('/datasets/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      await fetchDatasets();
      setSelectedDatasetId(res.data.id);
    } catch (err: any) {
      alert(`Upload failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCleanDataset = async () => {
    if (!selectedDatasetId) return;
    try {
      setLoading(true);
      await apiClient.post(`/datasets/${selectedDatasetId}/clean`, {
        remove_duplicates: true,
        missing_strategy: 'median_mode',
        clean_column_names: true,
        normalize_dates: true,
        outlier_handling: 'clip_iqr'
      });
      await loadTabData('quality', selectedDatasetId);
      alert('Dataset successfully cleaned and re-profiled!');
    } catch (err: any) {
      alert(`Cleaning error: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAskData = async (e: FormEvent) => {
    e.preventDefault();
    if (!askQuestion.trim() || !selectedDatasetId) return;
    try {
      setLoading(true);
      const res = await apiClient.post<AskDataResponse>('/ask-data', {
        question: askQuestion,
        dataset_id: selectedDatasetId
      });
      setAskResponse(res.data);
    } catch (err: any) {
      alert(`Query failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleExportPdf = async () => {
    if (!selectedDatasetId) return;
    try {
      setIsExportingPdf(true);
      const response = await apiClient.get(`/datasets/${selectedDatasetId}/governance-report.pdf`, {
        responseType: 'blob'
      });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `BIZINSIGHT_Audit_Dossier_Dataset_${selectedDatasetId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(`PDF Export Failed: ${err.message}`);
    } finally {
      setIsExportingPdf(false);
    }
  };

  const selectedDataset = datasets.find(d => d.id === selectedDatasetId);
  const activeTabConfig = TAB_CONFIG.find(t => t.id === activeTab);

  /* ─── Elegant Light Theme Recharts configuration ─── */
  const chartGrid = { strokeDasharray: '3 3', stroke: '#f1f5f9' };
  const chartAxis = { stroke: '#94a3b8', fontSize: 11, fontFamily: "'JetBrains Mono', monospace" };
  const chartTooltipStyle = { 
    backgroundColor: '#ffffff', 
    border: '1px solid #e2e8f0', 
    borderRadius: '12px', 
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.04)', 
    fontSize: '11px',
    color: '#0f172a',
    padding: '8px 12px'
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-slate-50 text-slate-800" style={{ fontFamily: "var(--font-sans)" }}>
      {/* ═══════════════════════════════ SIDEBAR ═══════════════════════════════ */}
      <Sidebar 
        activeTab={activeTab} 
        onTabChange={setActiveTab} 
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {/* ═══════════════════════════ MAIN VIEWPORT ═══════════════════════════ */}
      <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0">
        <Navbar
          datasets={datasets}
          selectedDatasetId={selectedDatasetId}
          onSelectDataset={(id) => setSelectedDatasetId(id)}
          onFileUpload={handleFileUpload}
          currentUser={currentUser}
          onOpenAuth={() => setIsAuthOpen(true)}
          onLogout={() => {
            localStorage.removeItem('bizinsight_token');
            localStorage.removeItem('bizinsight_user');
            setCurrentUser(null);
          }}
          loading={loading}
          onToggleSidebar={() => setIsSidebarOpen(prev => !prev)}
          companyProfile={companyProfile}
          onOpenCompanyDNA={() => setIsCompanyDNAOpen(true)}
        />

        <main className="flex-1 flex flex-col h-full overflow-hidden bg-slate-50/60 min-w-0">
        {/* ─── Top Industry Standard Header with 1-Click PDF Export ─── */}
        <header className="px-3 sm:px-6 py-2.5 min-h-14 sm:h-16 bg-white/95 backdrop-blur border-b border-slate-200/80 flex items-center justify-between shrink-0 shadow-xs z-10 gap-2">
          <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
            {activeTabConfig && (
              <div 
                className="w-7 h-7 sm:w-8 sm:h-8 rounded-xl flex items-center justify-center text-white shadow-xs shrink-0" 
                style={{ backgroundColor: activeTabConfig.color }}
              >
                <activeTabConfig.icon className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
              </div>
            )}
            <div className="min-w-0 flex-1">
              <div className="flex items-center space-x-1.5 sm:space-x-2">
                <h2 className="text-xs sm:text-sm font-bold text-slate-900 m-0 tracking-tight truncate">
                  {activeTabConfig?.label || activeTab}
                </h2>
                {activeTabConfig?.badge && (
                  <span className="text-[9px] sm:text-[10px] font-bold px-1.5 sm:px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200/60 uppercase shrink-0">
                    {activeTabConfig.badge}
                  </span>
                )}
              </div>
              {selectedDataset && (
                <p className="text-[10px] sm:text-[11px] text-slate-500 font-medium m-0 flex items-center space-x-1 truncate">
                  <span className="hidden xs:inline">Source:</span>
                  <span className="font-semibold text-slate-700 truncate">{selectedDataset.name}</span>
                  <span className="hidden sm:inline">·</span>
                  <span className="font-mono hidden sm:inline">{selectedDataset.row_count.toLocaleString()} rows</span>
                  <span className="hidden md:inline">·</span>
                  <span className="font-mono hidden md:inline">{selectedDataset.column_count} cols</span>
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-1.5 sm:space-x-3 shrink-0">
            {/* 1-Click Executive PDF Export Button */}
            <button
              onClick={handleExportPdf}
              disabled={isExportingPdf || !selectedDatasetId}
              className="flex items-center space-x-1 sm:space-x-1.5 px-2.5 sm:px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-xs transition-all cursor-pointer disabled:opacity-50 shrink-0 whitespace-nowrap"
              title="Download Regulatory Governance Audit Dossier (PDF)"
            >
              <Download className={`w-3.5 h-3.5 shrink-0 ${isExportingPdf ? 'animate-bounce' : ''}`} />
              <span className="hidden xs:inline">
                {isExportingPdf ? 'Exporting...' : 'Export PDF'}
              </span>
              <span className="hidden lg:inline">{isExportingPdf ? '' : ' Dossier'}</span>
            </button>

            {loading && (
              <div className="hidden xs:flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-amber-50 border border-amber-200/80 text-amber-700 text-xs font-medium shrink-0">
                <Clock className="w-3.5 h-3.5 animate-spin" />
                <span className="hidden sm:inline">Computing...</span>
              </div>
            )}
            <button 
              onClick={() => selectedDatasetId && loadTabData(activeTab, selectedDatasetId)}
              className="flex items-center space-x-1 sm:space-x-1.5 px-2.5 sm:px-3 py-1.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-600 hover:text-slate-900 text-xs font-semibold shadow-xs transition-all cursor-pointer shrink-0"
              title="Refresh Data"
            >
              <RefreshCw className={`w-3.5 h-3.5 shrink-0 ${loading ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
          </div>
        </header>

        {/* ─── Content Body ─── */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {errorMsg && (
            <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start space-x-3 shadow-xs">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">System Notice: </span>
                <span className="text-rose-700">{errorMsg}</span>
              </div>
            </div>
          )}

          {/* ═══════════════ TAB: OVERVIEW & KPIS ═══════════════ */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {kpiData && Object.entries(kpiData.cards).map(([key, card]) => (
                  <div key={key} className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs hover:shadow-md transition-all">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-400">{card.label}</span>
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    </div>
                    <div className="text-2xl font-black font-mono text-slate-900 tracking-tight">{card.formatted}</div>
                    <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500">
                      <span>Live Computed Metric</span>
                      <span className="font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200/60 font-mono">
                        Optimal
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {kpiData && kpiData.trends.length > 0 && (
                <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 m-0">Aggregate Historical Trajectory</h3>
                      <p className="text-xs text-slate-500 mt-0.5">Chronologically ordered progression across dataset intervals</p>
                    </div>
                    <span className="text-xs font-semibold px-3 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200/60 self-start sm:self-auto font-mono">
                      {kpiData.trends.length} Observation Periods
                    </span>
                  </div>
                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={kpiData.trends}>
                        <defs>
                          <linearGradient id="colorValLight" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#2563eb" stopOpacity={0.2}/>
                            <stop offset="95%" stopColor="#2563eb" stopOpacity={0.0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid {...chartGrid} />
                        <XAxis dataKey="period" {...chartAxis} />
                        <YAxis {...chartAxis} />
                        <Tooltip contentStyle={chartTooltipStyle} />
                        <Area type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={2.5} fillOpacity={1} fill="url(#colorValLight)" dot={false} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {kpiData && kpiData.breakdowns.regions && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                    <h3 className="text-sm font-bold text-slate-900 mb-1">Regional Distribution</h3>
                    <p className="text-xs text-slate-500 mb-4">Metric aggregation partitioned by regional geography</p>
                    <div className="h-52">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={kpiData.breakdowns.regions}>
                          <CartesianGrid {...chartGrid} />
                          <XAxis dataKey="name" {...chartAxis} />
                          <YAxis {...chartAxis} />
                          <Tooltip contentStyle={chartTooltipStyle} />
                          <Bar dataKey="value" fill="#2563eb" radius={[8, 8, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                  <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                    <h3 className="text-sm font-bold text-slate-900 mb-1">Category Distribution</h3>
                    <p className="text-xs text-slate-500 mb-4">Metric aggregation partitioned by core operational categories</p>
                    <div className="h-52">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={kpiData.breakdowns.categories || []}>
                          <CartesianGrid {...chartGrid} />
                          <XAxis dataKey="name" {...chartAxis} />
                          <YAxis {...chartAxis} />
                          <Tooltip contentStyle={chartTooltipStyle} />
                          <Bar dataKey="value" fill="#0284c7" radius={[8, 8, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ═══════════════ TAB: DATA QUALITY ENGINE ═══════════════ */}
          {activeTab === 'quality' && (
            <div className="space-y-6">
              {qualityReport && (
                <>
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs uppercase tracking-wider font-bold text-slate-400">Data Reliability Score</span>
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase ${
                            qualityReport.quality_score >= 80 
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                              : 'bg-amber-50 text-amber-800 border border-amber-200'
                          }`}>
                            {qualityReport.summary.quality_rating}
                          </span>
                        </div>
                        <div className="flex items-baseline space-x-3 mt-4">
                          <span className={`text-5xl font-black font-mono tracking-tight ${
                            qualityReport.quality_score >= 80 ? 'text-emerald-600' : 'text-amber-600'
                          }`}>
                            {qualityReport.quality_score}%
                          </span>
                          <span className="text-xs text-slate-400 font-medium">composite index</span>
                        </div>
                        <p className="text-xs text-slate-500 mt-2">
                          Evaluated against schema integrity, cell nullity, uniqueness, and distribution bounds.
                        </p>
                      </div>
                      <button
                        onClick={handleCleanDataset}
                        className="w-full py-2.5 mt-5 bg-blue-600 hover:bg-blue-700 active:scale-[0.98] text-white text-xs font-bold rounded-xl shadow-xs transition-all cursor-pointer flex items-center justify-center space-x-2"
                      >
                        <Sparkles className="w-4 h-4" />
                        <span>Run Automated Clean & Impute Pipeline</span>
                      </button>
                    </div>

                    <div className="lg:col-span-2 p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-4">
                      <h3 className="text-sm font-bold text-slate-900 m-0">Formula Specification</h3>
                      <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs font-mono text-slate-600">
                        {qualityReport.formula_description}
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                        <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/80">
                          <span className="text-xs text-slate-400 font-semibold uppercase">Missing / Null Cells</span>
                          <div className="text-lg font-bold font-mono text-slate-800 mt-1">
                            {qualityReport.summary.null_cells.toLocaleString()}{' '}
                            <span className="text-xs font-normal text-slate-400">({qualityReport.summary.null_pct}%)</span>
                          </div>
                        </div>
                        <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/80">
                          <span className="text-xs text-slate-400 font-semibold uppercase">Duplicate Records</span>
                          <div className="text-lg font-bold font-mono text-slate-800 mt-1">
                            {qualityReport.summary.duplicate_rows.toLocaleString()}{' '}
                            <span className="text-xs font-normal text-slate-400">({qualityReport.summary.duplicate_pct}%)</span>
                          </div>
                        </div>
                        <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/80">
                          <span className="text-xs text-slate-400 font-semibold uppercase">Violations Flagged</span>
                          <div className="text-lg font-bold font-mono text-slate-800 mt-1">
                            {qualityReport.summary.total_issues_found}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                    <h3 className="text-sm font-bold text-slate-900 mb-3">Integrity Diagnostics Log</h3>
                    {qualityReport.column_issues.length === 0 ? (
                      <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center space-x-2.5">
                        <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                        <span>All schema quality gates passed successfully. Zero data corruption or structural defects detected.</span>
                      </div>
                    ) : (
                      <div className="overflow-x-auto rounded-xl border border-slate-200">
                        <table className="w-full text-xs text-left">
                          <thead>
                            <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-[11px] uppercase tracking-wider">
                              <th className="px-4 py-3">Severity</th>
                              <th className="px-4 py-3">Target Field</th>
                              <th className="px-4 py-3">Defect Category</th>
                              <th className="px-4 py-3">Diagnostic Explanation</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {qualityReport.column_issues.map((iss, i) => (
                              <tr key={i} className="hover:bg-slate-50/60 transition-colors">
                                <td className="px-4 py-3">
                                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                                    iss.severity === 'critical' 
                                      ? 'bg-rose-50 text-rose-700 border border-rose-200' 
                                      : iss.severity === 'high' 
                                      ? 'bg-amber-50 text-amber-700 border border-amber-200' 
                                      : 'bg-blue-50 text-blue-700 border border-blue-200'
                                  }`}>
                                    {iss.severity}
                                  </span>
                                </td>
                                <td className="px-4 py-3 font-mono font-semibold text-blue-700">{iss.column || 'Dataset'}</td>
                                <td className="px-4 py-3 text-slate-700 font-medium">{iss.issue_type}</td>
                                <td className="px-4 py-3 text-slate-500">{iss.message}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          )}

          {/* ═══════════════ TAB: SHAP EXPLAINABILITY (FEATURE 1) ═══════════════ */}
          {activeTab === 'shap_explain' && (
            <div className="space-y-6">
              {/* Record Selector & Model Context */}
              <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 m-0">TreeSHAP Local & Global Feature Attribution</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Game-theoretic Shapley values decomposing model output into exact feature push forces
                  </p>
                </div>
                {shapData && (
                  <div className="flex items-center space-x-3">
                    <span className="text-xs font-semibold text-slate-500">Explain Observation:</span>
                    <input 
                      type="number"
                      min={0}
                      max={Math.max(0, (shapData?.available_records_count || 1) - 1)}
                      value={shapRecordIndex}
                      onChange={(e) => setShapRecordIndex(Number(e.target.value))}
                      className="w-20 rounded-xl px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 text-slate-900 font-mono text-center focus:ring-2 focus:ring-emerald-500/20"
                    />
                    <button
                      onClick={async () => {
                        if (!selectedDatasetId) return;
                        setLoading(true);
                        try {
                          const sRes = await apiClient.post<ShapExplainResponse>(`/datasets/${selectedDatasetId}/shap-explain?record_index=${shapRecordIndex}`);
                          setShapData(sRes.data);
                        } finally { setLoading(false); }
                      }}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-xs transition-all cursor-pointer"
                    >
                      Decompose
                    </button>
                  </div>
                )}
              </div>

              {shapData?.status === 'rejected' ? (
                <div className="p-6 rounded-2xl bg-amber-50/70 border border-amber-200 space-y-3">
                  <div className="flex items-start space-x-3">
                    <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <h3 className="text-sm font-bold text-amber-900 m-0">Numeric Features Required</h3>
                      <p className="text-xs text-amber-800 mt-1">{shapData.message}</p>
                    </div>
                  </div>
                </div>
              ) : shapData && (
                <>
                  {/* Local Prediction Breakdown Scorecard */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                      <span className="text-xs uppercase font-bold text-slate-400">Target Metric</span>
                      <div className="text-xl font-black font-mono text-slate-900 mt-1">{shapData.target_column}</div>
                      <span className="text-[10px] text-slate-400">Obs #{shapData.record_index}</span>
                    </div>
                    <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                      <span className="text-xs uppercase font-bold text-slate-400">Base Expected Value E[f(x)]</span>
                      <div className="text-2xl font-black font-mono text-slate-700 mt-1">
                        {shapData.expected_base_value.toLocaleString()}
                      </div>
                      <span className="text-[10px] text-slate-400">Global average prediction</span>
                    </div>
                    <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                      <span className="text-xs uppercase font-bold text-slate-400">Local Prediction f(x)</span>
                      <div className="text-2xl font-black font-mono text-emerald-600 mt-1">
                        {shapData.predicted_value.toLocaleString()}
                      </div>
                      <span className="text-[10px] text-emerald-600 font-semibold font-mono">
                        Δ: {(shapData.predicted_value - shapData.expected_base_value) > 0 ? `+${(shapData.predicted_value - shapData.expected_base_value).toFixed(2)}` : (shapData.predicted_value - shapData.expected_base_value).toFixed(2)}
                      </span>
                    </div>
                    <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                      <span className="text-xs uppercase font-bold text-slate-400">Actual Ground Truth</span>
                      <div className="text-2xl font-black font-mono text-slate-900 mt-1">
                        {shapData.actual_value !== null ? shapData.actual_value?.toLocaleString() : 'N/A'}
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono">Error: {shapData.actual_value ? Math.abs(shapData.predicted_value - shapData.actual_value).toFixed(2) : '—'}</span>
                    </div>
                  </div>

                  {/* Local Waterfall Feature Forces */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-bold text-slate-900 m-0">Local Observation Waterfall Forces</h4>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                          Obs #{shapData.record_index}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500">
                        Features pushing prediction higher (Emerald) vs lower (Rose) relative to baseline $E[f(x)]$
                      </p>
                      <div className="space-y-2 mt-3">
                        {shapData.local_contributions.map((c, i) => (
                          <div key={i} className="p-3 rounded-xl bg-slate-50/80 border border-slate-200/80 flex items-center justify-between text-xs">
                            <div>
                              <span className="font-semibold text-slate-800">{c.feature}</span>
                              <span className="text-[10px] text-slate-400 font-mono ml-2">val = {c.feature_value}</span>
                            </div>
                            <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold font-mono ${
                              c.direction === 'positive' 
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                                : 'bg-rose-50 text-rose-700 border border-rose-200'
                            }`}>
                              {c.shap_value > 0 ? `+${c.shap_value}` : c.shap_value}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Global SHAP Ranking Chart */}
                    <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                      <h4 className="text-sm font-bold text-slate-900 mb-0.5">Global Feature Importance (Mean |SHAP|)</h4>
                      <p className="text-xs text-slate-500 mb-4">Relative importance across the entire dataset population</p>
                      <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={shapData.global_importance} layout="vertical">
                            <CartesianGrid {...chartGrid} />
                            <XAxis type="number" {...chartAxis} />
                            <YAxis type="category" dataKey="feature" {...chartAxis} width={90} />
                            <Tooltip contentStyle={chartTooltipStyle} />
                            <Bar dataKey="relative_importance_pct" fill="#059669" radius={[0, 8, 8, 0]} name="Importance %" />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* ═══════════════ TAB: PRESCRIPTIVE GOAL-SEEK (FEATURE 2) ═══════════════ */}
          {activeTab === 'goal_seek' && (
            <div className="space-y-6">
              <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 m-0">Prescriptive Inverse Optimization & Goal-Seek</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Solves sequential quadratic programming (SLSQP) to find the minimum-effort lever settings for your target KPI
                  </p>
                </div>
                {goalSeekData && (
                  <div className="flex items-center space-x-3">
                    <span className="text-xs font-semibold text-slate-500">Desired Target KPI:</span>
                    <input 
                      type="number" 
                      value={targetGoalInput}
                      onChange={(e) => setTargetGoalInput(Number(e.target.value))}
                      className="w-28 rounded-xl px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 text-slate-900 font-mono text-center focus:ring-2 focus:ring-orange-500/20"
                    />
                    <button
                      onClick={async () => {
                        if (!selectedDatasetId) return;
                        setLoading(true);
                        try {
                          const gRes = await apiClient.post<GoalSeekResponse>(`/datasets/${selectedDatasetId}/goal-seek`, {
                            target_goal_value: targetGoalInput
                          });
                          setGoalSeekData(gRes.data);
                        } finally { setLoading(false); }
                      }}
                      className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white text-xs font-bold rounded-xl shadow-xs transition-all cursor-pointer"
                    >
                      Solve Strategy
                    </button>
                  </div>
                )}
              </div>

              {goalSeekData?.status === 'rejected' ? (
                <div className="p-6 rounded-2xl bg-amber-50/70 border border-amber-200 space-y-3">
                  <div className="flex items-start space-x-3">
                    <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <h3 className="text-sm font-bold text-amber-900 m-0">Numeric Levers Required</h3>
                      <p className="text-xs text-amber-800 mt-1">{goalSeekData.message}</p>
                    </div>
                  </div>
                </div>
              ) : goalSeekData && (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                      <span className="text-xs uppercase font-bold text-slate-400">Baseline Target Mean</span>
                      <div className="text-2xl font-black font-mono text-slate-800 mt-1">
                        ${goalSeekData.baseline_metric_value.toLocaleString()}
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono">Metric: {goalSeekData.target_metric}</span>
                    </div>
                    <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                      <span className="text-xs uppercase font-bold text-slate-400">Target Goal ($y^*$)</span>
                      <div className="text-2xl font-black font-mono text-orange-600 mt-1">
                        ${goalSeekData.target_goal_value.toLocaleString()}
                      </div>
                      <span className="text-[10px] text-orange-600 font-semibold font-mono">
                        Δ: {((goalSeekData.target_goal_value - goalSeekData.baseline_metric_value) / goalSeekData.baseline_metric_value * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                      <span className="text-xs uppercase font-bold text-slate-400">Achieved Simulated Output</span>
                      <div className="text-2xl font-black font-mono text-emerald-600 mt-1">
                        ${goalSeekData.achieved_prediction.toLocaleString()}
                      </div>
                      <span className="text-[10px] text-emerald-600 font-mono font-semibold">
                        Gap: {goalSeekData.target_gap_pct}%
                      </span>
                    </div>
                    <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                      <span className="text-xs uppercase font-bold text-slate-400">Feasibility Verdict</span>
                      <div className="text-lg font-black font-mono text-slate-900 mt-1">
                        {goalSeekData.feasibility_verdict}
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono">Iterations: {goalSeekData.iterations_used}</span>
                    </div>
                  </div>

                  <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                    <h4 className="text-sm font-bold text-slate-900 mb-1">Prescriptive Recommendations for Controllable Levers</h4>
                    <p className="text-xs text-slate-500 mb-4">{goalSeekData.mathematical_model}</p>
                    <div className="overflow-x-auto rounded-xl border border-slate-200">
                      <table className="w-full text-xs text-left">
                        <thead>
                          <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-[11px] uppercase tracking-wider">
                            {['Business Lever', 'Current Baseline', 'Recommended Setting', 'Required Δ Change', '% Shift', 'Operational Feasibility Bounds'].map(h => (
                              <th key={h} className="px-4 py-3">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {goalSeekData.recommendations.map((r, i) => (
                            <tr key={i} className="hover:bg-slate-50/60 transition-colors">
                              <td className="px-4 py-3 font-semibold text-slate-900">{r.lever}</td>
                              <td className="px-4 py-3 font-mono text-slate-600">{r.baseline_value}</td>
                              <td className="px-4 py-3 font-mono font-bold text-orange-600">{r.recommended_value}</td>
                              <td className="px-4 py-3 font-mono">
                                <span className={r.absolute_change >= 0 ? 'text-emerald-600 font-semibold' : 'text-rose-600 font-semibold'}>
                                  {r.absolute_change >= 0 ? `+${r.absolute_change}` : r.absolute_change}
                                </span>
                              </td>
                              <td className="px-4 py-3 font-mono">
                                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                  r.percentage_change >= 0 ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
                                }`}>
                                  {r.percentage_change >= 0 ? `+${r.percentage_change}%` : `${r.percentage_change}%`}
                                </span>
                              </td>
                              <td className="px-4 py-3 font-mono text-slate-400">
                                [{r.min_bound} ↔ {r.max_bound}]
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* ═══════════════ TAB: TIME-SERIES FORECASTING ═══════════════ */}
          {activeTab === 'forecasting' && (
            <div className="space-y-6">
              <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 m-0">Forecasting Parameters</h3>
                  <p className="text-xs text-slate-500 mt-0.5">Configure temporal time axis and target outcome metric</p>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-semibold text-slate-500">Date Axis:</span>
                    <select 
                      value={forecastDateCol} 
                      onChange={(e) => setForecastDateCol(e.target.value)}
                      className="rounded-xl px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 text-slate-800 focus:outline-none focus:ring-2 focus:ring-purple-500/20"
                    >
                      <option value="">— select date field —</option>
                      {availableCols.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-semibold text-slate-500">Target Metric:</span>
                    <select 
                      value={forecastTargetCol} 
                      onChange={(e) => setForecastTargetCol(e.target.value)}
                      className="rounded-xl px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 text-slate-800 focus:outline-none focus:ring-2 focus:ring-purple-500/20"
                    >
                      <option value="">— select target —</option>
                      {availableCols.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                  <button
                    disabled={!forecastDateCol || !forecastTargetCol || loading}
                    onClick={async () => {
                      if (!selectedDatasetId || !forecastDateCol || !forecastTargetCol) return;
                      setLoading(true);
                      try {
                        const fRes = await apiClient.post<ForecastResponse>(`/datasets/${selectedDatasetId}/forecast`, {
                          date_column: forecastDateCol,
                          target_column: forecastTargetCol,
                          forecast_horizon: 14,
                          frequency: 'D'
                        });
                        setForecastData(fRes.data);
                      } catch (err: any) {
                        alert(err.response?.data?.detail || err.message);
                      } finally {
                        setLoading(false);
                      }
                    }}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-40 text-white text-xs font-bold rounded-xl shadow-xs transition-all cursor-pointer"
                  >
                    Generate Forecast
                  </button>
                </div>
              </div>

              {forecastData?.status === 'rejected' ? (
                <div className="p-6 rounded-2xl bg-amber-50/70 border border-amber-200 space-y-3">
                  <div className="flex items-start space-x-3">
                    <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <h3 className="text-sm font-bold text-amber-900 m-0">Temporal Axis Required</h3>
                      <p className="text-xs text-amber-800 mt-1">{forecastData.message}</p>
                    </div>
                  </div>
                  <div className="pt-3 border-t border-amber-200/60 text-xs text-amber-800">
                    <span className="font-bold">Recommended Datasets with Sequential Temporal Axes:</span>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {datasets.filter(d => ['wti_crude_oil_daily_prices.csv', 'global_gdp_real.csv', 'international_airline_passengers.csv'].includes(d.name)).map(d => (
                        <button 
                          key={d.id} 
                          onClick={() => setSelectedDatasetId(d.id)}
                          className="px-3 py-1 rounded-xl bg-white border border-amber-200 text-blue-700 font-mono text-xs hover:bg-blue-50 transition-colors cursor-pointer shadow-xs"
                        >
                          {d.name} ({d.row_count.toLocaleString()} rows)
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              ) : forecastData && (
                <>
                  <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-sm font-bold text-slate-900 m-0">Model Comparison & Cross-Validation</h3>
                        <p className="text-xs text-slate-500 mt-0.5 font-mono">
                          {forecastData.validation_strategy} | Train: {forecastData.train_period} | Test: {forecastData.test_period}
                        </p>
                      </div>
                      <span className="text-xs font-bold px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Champion: {forecastData.best_model}
                      </span>
                    </div>
                    <div className="overflow-x-auto rounded-xl border border-slate-200">
                      <table className="w-full text-xs text-left">
                        <thead>
                          <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-[11px] uppercase tracking-wider">
                            {['Model Family', 'MAE', 'RMSE', 'MAPE', 'R²', 'Δ vs Baseline'].map(h => (
                              <th key={h} className="px-4 py-3">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {forecastData.model_comparison?.map((m, i) => (
                            <tr key={i} className={m.model === forecastData.best_model ? 'bg-purple-50/50 font-semibold' : 'hover:bg-slate-50/50'}>
                              <td className="px-4 py-3 text-slate-900 font-medium">{m.model}</td>
                              <td className="px-4 py-3 font-mono text-slate-600">{m.mae.toLocaleString()}</td>
                              <td className="px-4 py-3 font-mono text-slate-600">{m.rmse.toLocaleString()}</td>
                              <td className="px-4 py-3 font-mono text-slate-600">{m.mape}%</td>
                              <td className="px-4 py-3 font-mono text-slate-600">{m.r2}</td>
                              <td className="px-4 py-3 font-mono">
                                <span className={m.improvement_vs_baseline_pct > 0 ? 'text-emerald-600' : 'text-slate-500'}>
                                  {m.improvement_vs_baseline_pct > 0 ? `+${m.improvement_vs_baseline_pct}%` : `${m.improvement_vs_baseline_pct}%`}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                    <h3 className="text-sm font-bold text-slate-900 mb-0.5">Future Horizon Projection (95% Confidence Interval)</h3>
                    <p className="text-xs text-slate-500 mb-4">{forecastData.uncertainty_note}</p>
                    <div className="h-72">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={forecastData.future_predictions}>
                          <CartesianGrid {...chartGrid} />
                          <XAxis dataKey="date" {...chartAxis} />
                          <YAxis {...chartAxis} />
                          <Tooltip contentStyle={chartTooltipStyle} />
                          <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                          <Line type="monotone" dataKey="upper_bound" stroke="#cbd5e1" strokeDasharray="3 3" dot={false} name="Upper 95% Bound" />
                          <Line type="monotone" dataKey="forecast" stroke="#7c3aed" strokeWidth={2.5} name="Projected Forecast" />
                          <Line type="monotone" dataKey="lower_bound" stroke="#cbd5e1" strokeDasharray="3 3" dot={false} name="Lower 95% Bound" />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* ═══════════════ TAB: ANOMALY DETECTION ═══════════════ */}
          {activeTab === 'anomalies' && (
            <div className="space-y-6">
              {anomalyData && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                      <span className="text-xs uppercase font-bold text-slate-400">Records Evaluated</span>
                      <div className="text-2xl font-black font-mono text-slate-900 mt-1">
                        {anomalyData.total_records_evaluated.toLocaleString()}
                      </div>
                    </div>
                    <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                      <span className="text-xs uppercase font-bold text-slate-400">Anomalies Detected</span>
                      <div className="text-2xl font-black font-mono text-rose-600 mt-1">
                        {anomalyData.anomalies_detected_count}{' '}
                        <span className="text-sm font-semibold text-rose-500 font-sans">({anomalyData.anomaly_percentage}%)</span>
                      </div>
                    </div>
                    <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                      <span className="text-xs uppercase font-bold text-slate-400">Isolation Forest Contamination</span>
                      <div className="text-2xl font-black font-mono text-slate-800 mt-1">
                        {anomalyData.contamination_threshold}
                      </div>
                    </div>
                  </div>

                  <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                    <h3 className="text-sm font-bold text-slate-900 mb-3">High-Risk Outliers & Anomalies</h3>
                    <div className="overflow-x-auto rounded-xl border border-slate-200">
                      <table className="w-full text-xs text-left">
                        <thead>
                          <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-[11px] uppercase tracking-wider">
                            {['Record ID', 'Timestamp', 'Anomaly Score', 'Contributing Features', 'Diagnostic Explanation'].map(h => (
                              <th key={h} className="px-4 py-3">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {anomalyData.top_anomalies.map((anom, i) => (
                            <tr key={i} className="hover:bg-slate-50/60 transition-colors">
                              <td className="px-4 py-3 font-mono font-bold text-blue-700">#{anom.record_index}</td>
                              <td className="px-4 py-3 font-mono text-slate-500">{anom.timestamp || '—'}</td>
                              <td className="px-4 py-3 font-mono font-bold text-rose-600">{anom.anomaly_score}</td>
                              <td className="px-4 py-3">
                                <div className="flex flex-wrap gap-1">
                                  {(anom.top_affected_fields || anom.affected_fields || []).map((f: string, fi: number) => (
                                    <span key={fi} className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-slate-100 text-slate-700 border border-slate-200">
                                      {f}
                                    </span>
                                  ))}
                                </div>
                              </td>
                              <td className="px-4 py-3 text-slate-600">{anom.explanation}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* ═══════════════ TAB: CUSTOMER SEGMENTS ═══════════════ */}
          {activeTab === 'segmentation' && (
            <div className="space-y-6">
              {segmentData && (
                <>
                  <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs text-xs text-slate-600 space-y-1">
                    <div>
                      <span className="font-bold text-slate-900">Clustering Methodology: </span>
                      {segmentData.methodology}
                    </div>
                    <div className="text-slate-400 italic">{segmentData.disclaimer}</div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {segmentData.segments?.map(seg => (
                      <div key={seg.cluster_id} className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs hover:shadow-md transition-all">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="text-sm font-bold text-slate-900 m-0">{seg.segment_label}</h4>
                          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200 font-mono">
                            Cluster #{seg.cluster_id} · {seg.customer_count} records
                          </span>
                        </div>
                        <div className="grid grid-cols-3 gap-3 mt-4">
                          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                            <span className="text-[10px] uppercase font-bold text-slate-400">Recency</span>
                            <div className="text-base font-bold font-mono text-slate-800 mt-0.5">{seg.median_recency_days}d</div>
                          </div>
                          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                            <span className="text-[10px] uppercase font-bold text-slate-400">Frequency</span>
                            <div className="text-base font-bold font-mono text-slate-800 mt-0.5">{seg.median_frequency}</div>
                          </div>
                          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                            <span className="text-[10px] uppercase font-bold text-slate-400">Spend</span>
                            <div className="text-base font-bold font-mono text-slate-800 mt-0.5">${(seg.median_monetary ?? 0).toLocaleString()}</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          {/* ═══════════════ TAB: CAUSAL WHAT-IF SIMULATOR ═══════════════ */}
          {activeTab === 'causal' && (
            <div className="space-y-6">
              <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 m-0">Causal Counterfactual Simulator</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Marginal elasticity (β) and 95% confidence interval perturbation analysis
                  </p>
                </div>
                {causalData && causalData.available_drivers && (
                  <div className="flex flex-wrap items-center gap-3">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-semibold text-slate-500">Intervention Driver:</span>
                      <select 
                        value={causalDriver} 
                        onChange={(e) => setCausalDriver(e.target.value)}
                        className="rounded-xl px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 text-slate-800 focus:outline-none focus:ring-2 focus:ring-pink-500/20"
                      >
                        {causalData.available_drivers.map(d => <option key={d} value={d}>{d}</option>)}
                      </select>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-semibold text-slate-500">Perturbation Δ%:</span>
                      <input 
                        type="number" 
                        value={perturbationPct} 
                        onChange={(e) => setPerturbationPct(Number(e.target.value))}
                        className="w-16 rounded-xl px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 text-slate-800 font-mono text-center focus:outline-none focus:ring-2 focus:ring-pink-500/20" 
                      />
                    </div>
                    <button 
                      onClick={async () => {
                        if (!selectedDatasetId) return;
                        setLoading(true);
                        try {
                          const cRes = await apiClient.post<CausalResponse>(
                            `/datasets/${selectedDatasetId}/causal-simulation?intervention_driver=${causalDriver}&perturbation_pct=${perturbationPct}`
                          );
                          setCausalData(cRes.data);
                        } finally { setLoading(false); }
                      }}
                      className="px-4 py-2 bg-pink-600 hover:bg-pink-700 text-white text-xs font-bold rounded-xl shadow-xs transition-all cursor-pointer"
                    >
                      Simulate Impact
                    </button>
                  </div>
                )}
              </div>

              {causalData?.status === 'rejected' ? (
                <div className="p-6 rounded-2xl bg-amber-50/70 border border-amber-200 space-y-3">
                  <div className="flex items-start space-x-3">
                    <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <h3 className="text-sm font-bold text-amber-900 m-0">Multi-Variate Feature Columns Required</h3>
                      <p className="text-xs text-amber-800 mt-1">{causalData.message}</p>
                    </div>
                  </div>
                  <div className="pt-3 border-t border-amber-200/60 text-xs text-amber-800">
                    <span className="font-bold">Recommended Multi-Variate Datasets for Causal Simulation:</span>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {datasets.filter(d => ['california_housing_census_kaggle.csv', 'diamonds_market_pricing.csv', 'supermarket_sales_real.csv', 'ecommerce_retail_sales.csv', 'titanic_real_passengers.csv'].includes(d.name)).map(d => (
                        <button 
                          key={d.id} 
                          onClick={() => setSelectedDatasetId(d.id)}
                          className="px-3 py-1 rounded-xl bg-white border border-amber-200 text-blue-700 font-mono text-xs hover:bg-blue-50 transition-colors cursor-pointer shadow-xs"
                        >
                          {d.name} ({d.row_count.toLocaleString()} rows)
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              ) : causalData && causalData.status === 'success' && causalData.metrics && causalData.counterfactual_simulation && (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                      <span className="text-xs uppercase font-bold text-slate-400">Elasticity Coeff</span>
                      <div className="text-2xl font-black font-mono text-pink-600 mt-1">
                        {causalData.metrics.elasticity > 0 ? `+${causalData.metrics.elasticity}` : causalData.metrics.elasticity}
                      </div>
                    </div>
                    <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                      <span className="text-xs uppercase font-bold text-slate-400">Baseline Target Mean</span>
                      <div className="text-xl font-black font-mono text-slate-800 mt-1">
                        ${causalData.counterfactual_simulation.baseline_mean_target.toLocaleString()}
                      </div>
                    </div>
                    <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                      <span className="text-xs uppercase font-bold text-slate-400">Counterfactual Projection</span>
                      <div className="text-xl font-black font-mono text-emerald-600 mt-1">
                        ${causalData.counterfactual_simulation.simulated_target.toLocaleString()}
                      </div>
                    </div>
                    <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                      <span className="text-xs uppercase font-bold text-slate-400">Statistical Significance</span>
                      <div className="text-lg font-black font-mono text-slate-800 mt-1">
                        {causalData.metrics.statistically_significant ? 'p < 0.05 (Valid)' : 'p ≥ 0.05 (Inconclusive)'}
                      </div>
                      <span className="text-xs font-mono text-slate-400">R² = {causalData.metrics.r_squared}</span>
                    </div>
                  </div>

                  <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                    <h4 className="text-sm font-bold text-slate-900 mb-0.5">
                      Counterfactual Sensitivity Curve: {causalData.counterfactual_simulation.intervention_scenario}
                    </h4>
                    <p className="text-xs text-slate-500 mb-4">{causalData.metrics.elasticity_interpretation}</p>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={causalData.simulation_curve}>
                          <CartesianGrid {...chartGrid} />
                          <XAxis dataKey="driver_val" {...chartAxis} />
                          <YAxis {...chartAxis} />
                          <Tooltip contentStyle={chartTooltipStyle} />
                          <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                          <Line type="monotone" dataKey="upper_bound" stroke="#cbd5e1" strokeDasharray="3 3" dot={false} name="Upper 95% CI" />
                          <Line type="monotone" dataKey="expected_target" stroke="#db2777" strokeWidth={2.5} name="Expected Target" />
                          <Line type="monotone" dataKey="lower_bound" stroke="#cbd5e1" strokeDasharray="3 3" dot={false} name="Lower 95% CI" />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                    <p className="text-xs text-slate-400 mt-3 italic">{causalData.methodological_caveat}</p>
                  </div>
                </>
              )}
            </div>
          )}

          {/* ═══════════════ TAB: DATA DRIFT & STRESS AUDIT ═══════════════ */}
          {activeTab === 'stress_drift' && (
            <div className="space-y-6">
              {stressAuditData?.status === 'rejected' ? (
                <div className="p-6 rounded-2xl bg-amber-50/70 border border-amber-200 space-y-3">
                  <div className="flex items-start space-x-3">
                    <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <h3 className="text-sm font-bold text-amber-900 m-0">Stress & Drift Audit Notice</h3>
                      <p className="text-xs text-amber-800 mt-1">{stressAuditData.message}</p>
                    </div>
                  </div>
                </div>
              ) : stressAuditData && (
                <>
                  <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 m-0">Population Drift & Stress Stability Audit</h3>
                      <p className="text-xs text-slate-500 mt-0.5 font-mono">{stressAuditData.sample_split}</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
                      stressAuditData.overall_stability_verdict.includes('Severe') 
                        ? 'bg-rose-50 text-rose-700 border border-rose-200' 
                        : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    }`}>
                      {stressAuditData.overall_stability_verdict}
                    </span>
                  </div>

                  <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                    <h4 className="text-sm font-bold text-slate-900 mb-3">Kolmogorov-Smirnov Distribution Drift Analysis</h4>
                    <div className="overflow-x-auto rounded-xl border border-slate-200">
                      <table className="w-full text-xs text-left">
                        <thead>
                          <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-[11px] uppercase tracking-wider">
                            {['Feature', 'KS Statistic', 'p-Value', 'Mean Shift', 'Kurtosis & Tail Risk', 'Stability Status'].map(h => (
                              <th key={h} className="px-4 py-3">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {(stressAuditData.feature_drift_analysis || []).map((r, i) => (
                            <tr key={i} className="hover:bg-slate-50/60 transition-colors">
                              <td className="px-4 py-3 font-mono font-semibold text-blue-700">{r.column}</td>
                              <td className="px-4 py-3 font-mono text-slate-600">{r.ks_statistic}</td>
                              <td className="px-4 py-3 font-mono text-slate-600">{r.p_value}</td>
                              <td className="px-4 py-3 font-mono">
                                <span className={r.mean_shift_pct > 0 ? 'text-emerald-600' : 'text-rose-600'}>
                                  {r.mean_shift_pct > 0 ? `+${r.mean_shift_pct}%` : `${r.mean_shift_pct}%`}
                                </span>
                              </td>
                              <td className="px-4 py-3 font-mono text-slate-600">{r.kurtosis} ({r.tail_risk})</td>
                              <td className="px-4 py-3">
                                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                                  r.drift_status === 'Severe Drift' 
                                    ? 'bg-rose-50 text-rose-700 border border-rose-200' 
                                    : r.drift_status === 'Moderate Drift' 
                                    ? 'bg-amber-50 text-amber-700 border border-amber-200' 
                                    : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                }`}>
                                  {r.drift_status}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                      <h4 className="text-sm font-bold text-slate-900 mb-3">Quantile Stress Scenarios (±20% Shocks)</h4>
                      <div className="space-y-3">
                        {(stressAuditData.stress_shocks || []).slice(0, 4).map((s, i) => (
                          <div key={i} className="p-3.5 rounded-xl bg-slate-50/80 border border-slate-200/80">
                            <div className="flex justify-between font-mono font-semibold text-xs mb-1.5">
                              <span className="text-blue-700">{s.column}</span>
                              <span className="text-slate-700">Median: {s.current_median.toLocaleString()}</span>
                            </div>
                            <div className="grid grid-cols-4 gap-2 text-[11px] text-slate-500">
                              <div>-20% Shock: <span className="font-mono block text-rose-600 font-semibold">{s.shock_down_20pct.toLocaleString()}</span></div>
                              <div>+20% Shock: <span className="font-mono block text-emerald-600 font-semibold">{s.shock_up_20pct.toLocaleString()}</span></div>
                              <div>VaR 5%: <span className="font-mono block text-amber-600 font-semibold">{s.tail_value_at_risk_5pct.toLocaleString()}</span></div>
                              <div>Upside 95%: <span className="font-mono block text-blue-600 font-semibold">{s.tail_upside_95pct.toLocaleString()}</span></div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                      <h4 className="text-sm font-bold text-slate-900 mb-3">Information Entropy & Categorical Diversity</h4>
                      <div className="space-y-3">
                        {(stressAuditData.categorical_entropy_diversity || []).map((e, i) => (
                          <div key={i} className="p-3.5 rounded-xl bg-slate-50/80 border border-slate-200/80">
                            <div className="flex justify-between font-mono font-semibold text-xs mb-1">
                              <span className="text-slate-800">{e.column}</span>
                              <span className="text-teal-700 font-bold">{e.shannon_entropy_bits} bits</span>
                            </div>
                            <div className="flex justify-between text-[11px] text-slate-500">
                              <span>Diversity Index: {e.diversity_ratio}</span>
                              <span className={e.status.includes('Collapse') || e.status.includes('Risk') ? 'text-amber-600 font-semibold' : 'text-emerald-600 font-semibold'}>
                                {e.status}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* ═══════════════ TAB: ASK YOUR DATA (NLP) ═══════════════ */}
          {activeTab === 'ask_data' && (
            <div className="space-y-6">
              <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                <div className="flex items-center space-x-2.5 mb-1">
                  <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 m-0">Ask Your Data (NLP Engine)</h3>
                </div>
                <p className="text-xs text-slate-500 mb-4">
                  Ask conversational questions in plain English. The engine securely converts text to parameterized, read-only SQL queries with row-limit bounds.
                </p>
                <form onSubmit={handleAskData} className="flex gap-3">
                  <input
                    type="text"
                    value={askQuestion}
                    onChange={(e) => setAskQuestion(e.target.value)}
                    placeholder="e.g. Which region generated the highest revenue, or what is the total record count?"
                    className="flex-1 rounded-xl px-4 py-2.5 text-xs bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 shadow-xs transition-all"
                  />
                  <button 
                    type="submit" 
                    disabled={loading}
                    className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white text-xs font-bold rounded-xl shadow-xs transition-all cursor-pointer"
                  >
                    Run Query
                  </button>
                </form>
              </div>

              {askResponse && (
                <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-4">
                  <div>
                    <span className="text-xs uppercase tracking-wider font-bold text-slate-400">Natural Language Answer</span>
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-800 mt-1.5 font-medium whitespace-pre-line leading-relaxed">
                      {askResponse.answer}
                    </div>
                  </div>

                  <div>
                    <span className="text-xs uppercase tracking-wider font-bold text-slate-400">Generated SQL Query</span>
                    <div className="p-3 rounded-xl bg-slate-900 text-slate-100 font-mono text-xs mt-1.5 flex items-center justify-between shadow-xs">
                      <code className="text-emerald-400">{askResponse.sql_query}</code>
                      <span className="text-[10px] text-slate-400 shrink-0 ml-3">
                        {askResponse.execution_time_ms.toFixed(1)}ms
                      </span>
                    </div>
                  </div>

                  {askResponse.results && askResponse.results.length > 0 && (
                    <div>
                      <span className="text-xs uppercase tracking-wider font-bold text-slate-400">
                        Result Table ({askResponse.row_count} rows retrieved)
                      </span>
                      <div className="mt-2 overflow-x-auto rounded-xl border border-slate-200 max-h-56">
                        <table className="w-full text-xs text-left">
                          <thead>
                            <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-[11px] uppercase tracking-wider">
                              {Object.keys(askResponse.results[0]).map((k, i) => (
                                <th key={i} className="px-4 py-2.5 font-mono">{k}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {askResponse.results.map((row, ri) => (
                              <tr key={ri} className="hover:bg-slate-50/60 transition-colors">
                                {Object.values(row).map((v: any, vi) => (
                                  <td key={vi} className="px-4 py-2 font-mono text-slate-700">{String(v)}</td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ═══════════════ TAB: AUDIT TRAIL ═══════════════ */}
          {activeTab === 'audit' && (
            <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 m-0">Immutable Enterprise Audit Log</h3>
                  <p className="text-xs text-slate-500 mt-0.5">Tamper-evident chronological record of analytics actions, queries, and simulation events</p>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleExportPdf}
                    disabled={isExportingPdf || !selectedDatasetId}
                    className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-xs transition-all cursor-pointer"
                  >
                    <Download className={`w-3.5 h-3.5 ${isExportingPdf ? 'animate-bounce' : ''}`} />
                    <span>{isExportingPdf ? 'Generating PDF...' : 'Download PDF Audit Report'}</span>
                  </button>
                  <span className="text-xs font-mono px-3 py-1 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                    {auditLogs.length} events logged
                  </span>
                </div>
              </div>

              <div className="overflow-x-auto rounded-xl border border-slate-200">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-[11px] uppercase tracking-wider">
                      {['Timestamp', 'User', 'Action', 'Target Resource', 'Event Metadata'].map(h => (
                        <th key={h} className="px-4 py-3">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {auditLogs.map((log, i) => (
                      <tr key={i} className="hover:bg-slate-50/60 transition-colors">
                        <td className="px-4 py-3 font-mono text-slate-500">{new Date(log.created_at).toLocaleString()}</td>
                        <td className="px-4 py-3 font-semibold text-slate-800">{log.username}</td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
                            {log.action}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono text-slate-600">{log.resource_type} ({log.resource_id})</td>
                        <td className="px-4 py-3 font-mono text-[11px] text-slate-500 truncate max-w-sm">
                          {JSON.stringify(log.details)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ═══════════════ TAB: EXPLORATORY ANALYSIS ═══════════════ */}
          {activeTab === 'analytics' && (
            <div className="space-y-6">
              {kpiData && (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {Object.entries(kpiData.cards).map(([key, card]) => (
                      <div key={key} className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">{card.label}</span>
                        <div className="text-2xl font-black font-mono text-slate-900 mt-1">{card.formatted}</div>
                      </div>
                    ))}
                  </div>

                  {kpiData.trends.length > 0 && (
                    <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                      <h3 className="text-sm font-bold text-slate-900 mb-1">Exploratory Sequential Variance</h3>
                      <p className="text-xs text-slate-500 mb-4">Metric progression across detected time indices</p>
                      <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={kpiData.trends}>
                            <defs>
                              <linearGradient id="colorValAltLight" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#0284c7" stopOpacity={0.2}/>
                                <stop offset="95%" stopColor="#0284c7" stopOpacity={0.0}/>
                              </linearGradient>
                            </defs>
                            <CartesianGrid {...chartGrid} />
                            <XAxis dataKey="period" {...chartAxis} />
                            <YAxis {...chartAxis} />
                            <Tooltip contentStyle={chartTooltipStyle} />
                            <Area type="monotone" dataKey="value" stroke="#0284c7" strokeWidth={2.5} fillOpacity={1} fill="url(#colorValAltLight)" dot={false} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
          {/* ═══════════════ ENTERPRISE 2.0 PLATFORM TABS ═══════════════ */}
          {activeTab === 'data_sources' && <DataSourcesTab />}
          {activeTab === 'contracts_gates' && <ContractsGatesTab datasetId={selectedDatasetId} />}
          {activeTab === 'lineage' && <LineageTab />}
          {activeTab === 'metrics_store' && <MetricsStoreTab />}
          {activeTab === 'digital_twin' && <DigitalTwinTab />}
          {activeTab === 'mlops_registry' && <MLOpsRegistryTab />}
          {activeTab === 'governance_abac' && <GovernanceABACTab datasetId={selectedDatasetId} />}
          {activeTab === 'operations_center' && <OperationsCenterTab />}
        </div>
      </main>
      </div>

      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onLoginSuccess={(user) => setCurrentUser(user)}
      />

      <CompanyDNAWizard
        isOpen={isCompanyDNAOpen}
        onClose={() => setIsCompanyDNAOpen(false)}
        onSuccess={(profile) => setCompanyProfile(profile)}
        initialProfile={companyProfile}
      />
    </div>
  );
}
