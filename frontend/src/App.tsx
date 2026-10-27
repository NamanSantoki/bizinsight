import { useState, useEffect } from 'react';
import type { FormEvent, ChangeEvent } from 'react';
import { 
  BarChart3, ShieldAlert, TrendingUp, Users, 
  HelpCircle, FileText, CheckCircle2, AlertTriangle, 
  RefreshCw, Upload, Activity, ChevronRight
} from 'lucide-react';
import { apiClient } from './services/api';
import type { 
  Dataset, DataQualityReport, KPIResult, 
  ForecastResponse, AnomalyResponse, SegmentationResponse, AskDataResponse 
} from './services/api';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, AreaChart, Area, Legend
} from 'recharts';

export default function App() {
  const [activeTab, setActiveTab] = useState<'overview' | 'quality' | 'analytics' | 'forecasting' | 'anomalies' | 'segmentation' | 'ask_data' | 'audit'>('overview');
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Module state
  const [qualityReport, setQualityReport] = useState<DataQualityReport | null>(null);
  const [kpiData, setKpiData] = useState<KPIResult | null>(null);
  const [forecastData, setForecastData] = useState<ForecastResponse | null>(null);
  const [anomalyData, setAnomalyData] = useState<AnomalyResponse | null>(null);
  const [segmentData, setSegmentData] = useState<SegmentationResponse | null>(null);
  const [askQuestion, setAskQuestion] = useState<string>('');
  const [askResponse, setAskResponse] = useState<AskDataResponse | null>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  // Load datasets on mount
  useEffect(() => {
    fetchDatasets();
  }, []);

  // When selected dataset changes, reload current tab data
  useEffect(() => {
    if (selectedDatasetId) {
      loadTabData(activeTab, selectedDatasetId);
    }
  }, [selectedDatasetId, activeTab]);

  const fetchDatasets = async () => {
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
  };

  const loadTabData = async (tab: string, datasetId: number) => {
    setErrorMsg(null);
    setLoading(true);
    try {
      if (tab === 'quality') {
        const res = await apiClient.get<DataQualityReport>(`/datasets/${datasetId}/quality`);
        setQualityReport(res.data);
      } else if (tab === 'analytics' || tab === 'overview') {
        const res = await apiClient.get<KPIResult>(`/datasets/${datasetId}/analytics`);
        setKpiData(res.data);
      } else if (tab === 'forecasting') {
        // Trigger auto-forecast on primary numeric and date columns
        const kpiRes = await apiClient.get<KPIResult>(`/datasets/${datasetId}/analytics`);
        const dateCol = kpiRes.data.date_metric || 'transaction_date';
        const targetCol = kpiRes.data.primary_metric || 'revenue';
        
        const fRes = await apiClient.post<ForecastResponse>(`/datasets/${datasetId}/forecast`, {
          date_column: dateCol,
          target_column: targetCol,
          forecast_horizon: 14,
          frequency: 'D'
        });
        setForecastData(fRes.data);
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
  };

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

  const selectedDataset = datasets.find(d => d.id === selectedDatasetId);

  return (
    <div className="flex h-screen w-full bg-[#090d16] text-slate-100 overflow-hidden font-sans">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-[#0d1322] border-r border-slate-800 flex flex-col justify-between shrink-0">
        <div>
          {/* Brand Header */}
          <div className="p-5 border-b border-slate-800 flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-indigo-700 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tight text-white m-0">BIZINSIGHT</h1>
              <span className="text-[11px] text-indigo-400 font-medium">Enterprise Analytics</span>
            </div>
          </div>

          {/* Dataset Selector */}
          <div className="p-4 border-b border-slate-800/60 bg-slate-900/40">
            <label className="text-[11px] uppercase tracking-wider font-semibold text-slate-400 block mb-1.5">
              Active Dataset
            </label>
            <select 
              className="w-full bg-[#131b2e] border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              value={selectedDatasetId || ''}
              onChange={(e) => setSelectedDatasetId(Number(e.target.value))}
            >
              {datasets.map(d => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.row_count.toLocaleString()} rows)
                </option>
              ))}
            </select>
            <div className="mt-3">
              <label className="flex items-center justify-center space-x-2 w-full py-1.5 px-3 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 rounded-lg text-xs cursor-pointer transition">
                <Upload className="w-3.5 h-3.5" />
                <span>Upload CSV / Excel</span>
                <input type="file" accept=".csv,.xlsx,.xls" className="hidden" onChange={handleFileUpload} />
              </label>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            {[
              { id: 'overview', label: 'Overview & KPIs', icon: BarChart3 },
              { id: 'quality', label: 'Data Quality Engine', icon: ShieldAlert },
              { id: 'analytics', label: 'Exploratory Trends', icon: TrendingUp },
              { id: 'forecasting', label: 'Chronological Forecast', icon: Activity },
              { id: 'anomalies', label: 'Anomaly Detection', icon: AlertTriangle },
              { id: 'segmentation', label: 'Customer Segments', icon: Users },
              { id: 'ask_data', label: 'Ask Your Data (NLP)', icon: HelpCircle },
              { id: 'audit', label: 'Audit Trail', icon: FileText },
            ].map(item => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id as any)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition ${
                    isActive 
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30' 
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-center space-x-2.5">
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </div>
                  {isActive && <ChevronRight className="w-3.5 h-3.5" />}
                </button>
              );
            })}
          </nav>
        </div>

        {/* System Status Footer */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-900/50 text-xs text-slate-400 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-[11px]">System Online</span>
          </div>
          <span className="text-[10px] text-slate-500">v1.0-prod</span>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <main className="flex-1 flex flex-col h-full overflow-hidden bg-[#0a0e17]">
        {/* Top App Bar */}
        <header className="h-14 border-b border-slate-800/80 px-6 flex items-center justify-between bg-[#0e1424]/80 backdrop-blur shrink-0">
          <div className="flex items-center space-x-4">
            <h2 className="text-sm font-semibold text-slate-100 uppercase tracking-wider m-0">
              {activeTab.replace('_', ' ')}
            </h2>
            {selectedDataset && (
              <span className="text-xs bg-slate-800 text-slate-300 px-2.5 py-0.5 rounded-full border border-slate-700">
                {selectedDataset.name} • {selectedDataset.row_count.toLocaleString()} rows • {selectedDataset.column_count} columns
              </span>
            )}
          </div>
          <div className="flex items-center space-x-3">
            <button 
              onClick={() => selectedDatasetId && loadTabData(activeTab, selectedDatasetId)}
              className="p-1.5 rounded-lg bg-slate-800/70 hover:bg-slate-800 text-slate-300 border border-slate-700 transition"
              title="Refresh Current View"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </header>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {errorMsg && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-center space-x-3">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <div>
                <p className="font-semibold">Notice / Limitation</p>
                <p className="text-slate-300 mt-0.5">{errorMsg}</p>
              </div>
            </div>
          )}

          {/* TAB: OVERVIEW & KPIS */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Metric Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {kpiData && Object.entries(kpiData.cards).map(([key, card]) => (
                  <div key={key} className="p-4 rounded-xl bg-[#0f172a] border border-slate-800 shadow-sm">
                    <span className="text-xs text-slate-400 font-medium">{card.label}</span>
                    <div className="text-2xl font-bold text-white mt-1">{card.formatted}</div>
                    <span className="text-[11px] text-emerald-400 mt-1 inline-block">Direct from data</span>
                  </div>
                ))}
              </div>

              {/* Temporal Revenue Trend */}
              {kpiData && kpiData.trends.length > 0 && (
                <div className="p-5 rounded-xl bg-[#0f172a] border border-slate-800">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-sm font-semibold text-white m-0">Historical Trend</h3>
                      <p className="text-xs text-slate-400 mt-0.5">Chronologically aggregated business metrics</p>
                    </div>
                  </div>
                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={kpiData.trends}>
                        <defs>
                          <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                            <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey="period" stroke="#64748b" fontSize={11} />
                        <YAxis stroke="#64748b" fontSize={11} />
                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                        <Area type="monotone" dataKey="value" stroke="#6366f1" fillOpacity={1} fill="url(#colorVal)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* Dimension Breakdowns */}
              {kpiData && kpiData.breakdowns.regions && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-5 rounded-xl bg-[#0f172a] border border-slate-800">
                    <h3 className="text-sm font-semibold text-white mb-3">Breakdown by Region</h3>
                    <div className="h-56">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={kpiData.breakdowns.regions}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                          <YAxis stroke="#64748b" fontSize={11} />
                          <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                          <Bar dataKey="value" fill="#818cf8" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="p-5 rounded-xl bg-[#0f172a] border border-slate-800">
                    <h3 className="text-sm font-semibold text-white mb-3">Breakdown by Category</h3>
                    <div className="h-56">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={kpiData.breakdowns.categories || []}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                          <YAxis stroke="#64748b" fontSize={11} />
                          <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                          <Bar dataKey="value" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB: DATA QUALITY ENGINE */}
          {activeTab === 'quality' && (
            <div className="space-y-6">
              {qualityReport && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Quality Score Hero */}
                    <div className="p-6 rounded-xl bg-[#0f172a] border border-slate-800 flex flex-col justify-between">
                      <div>
                        <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Quality Score</span>
                        <div className="flex items-baseline space-x-2 mt-2">
                          <span className={`text-5xl font-black ${qualityReport.quality_score >= 80 ? 'text-emerald-400' : 'text-amber-400'}`}>
                            {qualityReport.quality_score}%
                          </span>
                          <span className="text-xs text-slate-400">{qualityReport.summary.quality_rating}</span>
                        </div>
                      </div>
                      <div className="mt-4 pt-4 border-t border-slate-800/80">
                        <button
                          onClick={handleCleanDataset}
                          className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg transition"
                        >
                          Execute Auditable Cleaning Pipeline
                        </button>
                      </div>
                    </div>

                    {/* Quality Breakdown Metrics */}
                    <div className="md:col-span-2 p-6 rounded-xl bg-[#0f172a] border border-slate-800 space-y-3">
                      <h3 className="text-sm font-semibold text-white m-0">Transparent Formula Specification</h3>
                      <p className="text-xs text-slate-400 font-mono bg-slate-900/80 p-2.5 rounded border border-slate-800">
                        {qualityReport.formula_description}
                      </p>
                      <div className="grid grid-cols-3 gap-3 pt-2">
                        <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-800">
                          <span className="text-[11px] text-slate-400">Missing Cells</span>
                          <div className="text-lg font-bold text-slate-200 mt-0.5">
                            {qualityReport.summary.null_cells} ({qualityReport.summary.null_pct}%)
                          </div>
                        </div>
                        <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-800">
                          <span className="text-[11px] text-slate-400">Duplicate Rows</span>
                          <div className="text-lg font-bold text-slate-200 mt-0.5">
                            {qualityReport.summary.duplicate_rows} ({qualityReport.summary.duplicate_pct}%)
                          </div>
                        </div>
                        <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-800">
                          <span className="text-[11px] text-slate-400">Issues Flagged</span>
                          <div className="text-lg font-bold text-slate-200 mt-0.5">
                            {qualityReport.summary.total_issues_found}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Issues Table */}
                  <div className="p-5 rounded-xl bg-[#0f172a] border border-slate-800">
                    <h3 className="text-sm font-semibold text-white mb-3">Detected Integrity & Domain Issues</h3>
                    {qualityReport.column_issues.length === 0 ? (
                      <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-300 text-xs flex items-center space-x-2">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Zero schema or integrity issues detected. Dataset passed rigorous quality gates.</span>
                      </div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-xs text-left">
                          <thead className="bg-slate-900 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                            <tr>
                              <th className="p-2.5">Severity</th>
                              <th className="p-2.5">Target Column</th>
                              <th className="p-2.5">Issue Classification</th>
                              <th className="p-2.5">Diagnostic Finding</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/60">
                            {qualityReport.column_issues.map((iss, i) => (
                              <tr key={i} className="hover:bg-slate-900/40">
                                <td className="p-2.5">
                                  <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                    iss.severity === 'critical' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' :
                                    iss.severity === 'high' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                                    'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                                  }`}>
                                    {iss.severity.toUpperCase()}
                                  </span>
                                </td>
                                <td className="p-2.5 font-mono text-indigo-300">{iss.column || 'Dataset'}</td>
                                <td className="p-2.5 text-slate-300">{iss.issue_type}</td>
                                <td className="p-2.5 text-slate-400">{iss.message}</td>
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

          {/* TAB: FORECASTING ENGINE */}
          {activeTab === 'forecasting' && (
            <div className="space-y-6">
              {forecastData?.status === 'rejected' ? (
                <div className="p-6 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200">
                  <div className="flex items-center space-x-3 mb-2">
                    <ShieldAlert className="w-6 h-6 text-amber-400" />
                    <h3 className="text-sm font-bold text-white m-0">Forecasting Guard Active</h3>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">{forecastData.message}</p>
                </div>
              ) : forecastData && (
                <>
                  {/* Model Comparison Table */}
                  <div className="p-5 rounded-xl bg-[#0f172a] border border-slate-800">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h3 className="text-sm font-semibold text-white m-0">Chronological Model Benchmark</h3>
                        <p className="text-xs text-slate-400 mt-0.5">
                          Validation Strategy: {forecastData.validation_strategy} (Train: {forecastData.train_period} | Test: {forecastData.test_period})
                        </p>
                      </div>
                      <span className="text-xs px-2.5 py-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-lg">
                        Selected: {forecastData.best_model}
                      </span>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-xs text-left">
                        <thead className="bg-slate-900 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                          <tr>
                            <th className="p-2.5">Candidate Model</th>
                            <th className="p-2.5">MAE</th>
                            <th className="p-2.5">RMSE</th>
                            <th className="p-2.5">MAPE</th>
                            <th className="p-2.5">R²</th>
                            <th className="p-2.5">Improvement vs Baseline</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60">
                          {forecastData.model_comparison?.map((m, i) => (
                            <tr key={i} className={m.model === forecastData.best_model ? 'bg-indigo-950/30 font-semibold' : ''}>
                              <td className="p-2.5 text-slate-200">{m.model}</td>
                              <td className="p-2.5 font-mono">{m.mae.toLocaleString()}</td>
                              <td className="p-2.5 font-mono">{m.rmse.toLocaleString()}</td>
                              <td className="p-2.5 font-mono">{m.mape}%</td>
                              <td className="p-2.5 font-mono">{m.r2}</td>
                              <td className="p-2.5">
                                <span className={m.improvement_vs_baseline_pct > 0 ? 'text-emerald-400' : 'text-slate-400'}>
                                  {m.improvement_vs_baseline_pct > 0 ? `+${m.improvement_vs_baseline_pct}%` : `${m.improvement_vs_baseline_pct}%`}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Future Forecast Horizon with Uncertainty Bands */}
                  <div className="p-5 rounded-xl bg-[#0f172a] border border-slate-800">
                    <h3 className="text-sm font-semibold text-white mb-1">Future Projections with 95% Confidence Bounds</h3>
                    <p className="text-xs text-slate-400 mb-4">{forecastData.uncertainty_note}</p>
                    <div className="h-72">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={forecastData.future_predictions}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                          <YAxis stroke="#64748b" fontSize={11} />
                          <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                          <Legend />
                          <Line type="monotone" dataKey="upper_bound" stroke="#94a3b8" strokeDasharray="4 4" dot={false} name="Upper Bound (95%)" />
                          <Line type="monotone" dataKey="forecast" stroke="#6366f1" strokeWidth={2.5} name="Forecast Estimate" />
                          <Line type="monotone" dataKey="lower_bound" stroke="#94a3b8" strokeDasharray="4 4" dot={false} name="Lower Bound (95%)" />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* TAB: ANOMALY DETECTION */}
          {activeTab === 'anomalies' && (
            <div className="space-y-6">
              {anomalyData && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 rounded-xl bg-[#0f172a] border border-slate-800">
                      <span className="text-xs text-slate-400">Total Evaluated Records</span>
                      <div className="text-2xl font-bold text-white mt-1">{anomalyData.total_records_evaluated.toLocaleString()}</div>
                    </div>
                    <div className="p-4 rounded-xl bg-[#0f172a] border border-slate-800">
                      <span className="text-xs text-slate-400">Anomalies Detected</span>
                      <div className="text-2xl font-bold text-rose-400 mt-1">{anomalyData.anomalies_detected_count} ({anomalyData.anomaly_percentage}%)</div>
                    </div>
                    <div className="p-4 rounded-xl bg-[#0f172a] border border-slate-800">
                      <span className="text-xs text-slate-400">Algorithm</span>
                      <div className="text-2xl font-bold text-slate-200 mt-1">Isolation Forest</div>
                    </div>
                  </div>

                  <div className="p-5 rounded-xl bg-[#0f172a] border border-slate-800">
                    <h3 className="text-sm font-semibold text-white mb-3">Highest Ranked Multivariate Anomalies</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs text-left">
                        <thead className="bg-slate-900 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                          <tr>
                            <th className="p-2.5">Record Index</th>
                            <th className="p-2.5">Timestamp</th>
                            <th className="p-2.5">Score</th>
                            <th className="p-2.5">Deviating Dimensions</th>
                            <th className="p-2.5">Objective Explanation</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60">
                          {anomalyData.top_anomalies.map((anom, i) => (
                            <tr key={i} className="hover:bg-slate-900/40">
                              <td className="p-2.5 font-mono text-indigo-300">#{anom.record_index}</td>
                              <td className="p-2.5 text-slate-400">{anom.timestamp || 'N/A'}</td>
                              <td className="p-2.5 font-mono text-rose-400">{anom.anomaly_score}</td>
                              <td className="p-2.5">
                                <div className="flex flex-wrap gap-1">
                                  {anom.top_affected_fields.map((f, fi) => (
                                    <span key={fi} className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] border border-slate-700">
                                      {f}
                                    </span>
                                  ))}
                                </div>
                              </td>
                              <td className="p-2.5 text-slate-300">{anom.explanation}</td>
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

          {/* TAB: CUSTOMER SEGMENTATION */}
          {activeTab === 'segmentation' && (
            <div className="space-y-6">
              {segmentData && (
                <>
                  <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl text-xs text-slate-400">
                    <p className="font-semibold text-slate-200">Methodology & Framing:</p>
                    <p className="mt-1">{segmentData.methodology}</p>
                    <p className="mt-1 text-slate-500 italic">{segmentData.disclaimer}</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {segmentData.segments?.map(seg => (
                      <div key={seg.cluster_id} className="p-5 rounded-xl bg-[#0f172a] border border-slate-800">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="text-sm font-bold text-indigo-300 m-0">{seg.segment_label}</h4>
                          <span className="text-xs bg-slate-800 px-2.5 py-0.5 rounded border border-slate-700 text-slate-300">
                            Cluster #{seg.cluster_id} ({seg.customer_count} customers)
                          </span>
                        </div>
                        <div className="grid grid-cols-3 gap-2 mt-4 text-xs">
                          <div className="p-2.5 bg-slate-900 rounded border border-slate-800">
                            <span className="text-slate-500 text-[10px]">Median Recency</span>
                            <div className="font-bold text-slate-200 mt-0.5">{seg.median_recency_days} days</div>
                          </div>
                          <div className="p-2.5 bg-slate-900 rounded border border-slate-800">
                            <span className="text-slate-500 text-[10px]">Median Frequency</span>
                            <div className="font-bold text-slate-200 mt-0.5">{seg.median_frequency} orders</div>
                          </div>
                          <div className="p-2.5 bg-slate-900 rounded border border-slate-800">
                            <span className="text-slate-500 text-[10px]">Median Spend</span>
                            <div className="font-bold text-slate-200 mt-0.5">${seg.median_monetary.toLocaleString()}</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          {/* TAB: ASK YOUR DATA (NLP TO SQL) */}
          {activeTab === 'ask_data' && (
            <div className="space-y-6">
              <div className="p-5 rounded-xl bg-[#0f172a] border border-slate-800">
                <h3 className="text-sm font-semibold text-white mb-2">Natural-Language Business Query Interface</h3>
                <p className="text-xs text-slate-400 mb-4">
                  Translates natural language questions into safe, strictly read-only SQL executed with row-limit bounds and injection defenses.
                </p>
                <form onSubmit={handleAskData} className="flex gap-3">
                  <input
                    type="text"
                    value={askQuestion}
                    onChange={(e) => setAskQuestion(e.target.value)}
                    placeholder="e.g. Which region generated the highest revenue? Or What is the average order amount?"
                    className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg transition disabled:opacity-50"
                  >
                    Ask Data
                  </button>
                </form>
              </div>

              {askResponse && (
                <div className="p-5 rounded-xl bg-[#0f172a] border border-slate-800 space-y-4">
                  <div>
                    <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Grounded Answer</span>
                    <div className="p-3 bg-slate-900/90 rounded-lg border border-slate-800 text-xs text-slate-100 font-medium whitespace-pre-line mt-1.5">
                      {askResponse.answer}
                    </div>
                  </div>

                  <div>
                    <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Generated Read-Only SQL</span>
                    <div className="p-3 bg-slate-950 font-mono text-indigo-300 text-xs rounded-lg border border-slate-800 mt-1.5 flex items-center justify-between">
                      <code>{askResponse.sql_query}</code>
                      <span className="text-[10px] text-slate-500">{askResponse.execution_time_ms.toFixed(1)}ms</span>
                    </div>
                  </div>

                  {askResponse.results && askResponse.results.length > 0 && (
                    <div>
                      <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                        Underlying Database Records ({askResponse.row_count} rows)
                      </span>
                      <div className="mt-1.5 overflow-x-auto max-h-56">
                        <table className="w-full text-xs text-left">
                          <thead className="bg-slate-900 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                            <tr>
                              {Object.keys(askResponse.results[0]).map((k, i) => (
                                <th key={i} className="p-2 font-mono">{k}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/60">
                            {askResponse.results.map((row, ri) => (
                              <tr key={ri} className="hover:bg-slate-900/40">
                                {Object.values(row).map((v: any, vi) => (
                                  <td key={vi} className="p-2 font-mono text-slate-300">{String(v)}</td>
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

          {/* TAB: AUDIT LOGS */}
          {activeTab === 'audit' && (
            <div className="p-5 rounded-xl bg-[#0f172a] border border-slate-800">
              <h3 className="text-sm font-semibold text-white mb-3">Immutable Audit Trail</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-900 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="p-2.5">Timestamp</th>
                      <th className="p-2.5">User</th>
                      <th className="p-2.5">Action</th>
                      <th className="p-2.5">Resource</th>
                      <th className="p-2.5">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {auditLogs.map((log, i) => (
                      <tr key={i} className="hover:bg-slate-900/40">
                        <td className="p-2.5 text-slate-400 font-mono">{new Date(log.created_at).toLocaleString()}</td>
                        <td className="p-2.5 text-slate-200">{log.username}</td>
                        <td className="p-2.5 font-semibold text-indigo-300">{log.action}</td>
                        <td className="p-2.5 text-slate-400">{log.resource_type} ({log.resource_id})</td>
                        <td className="p-2.5 text-slate-400 font-mono text-[11px] truncate max-w-xs">
                          {JSON.stringify(log.details)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
