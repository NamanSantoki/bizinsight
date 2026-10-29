import React, { useState, useMemo } from 'react';
import { 
  BarChart3, Sliders, Table, Download, Search, 
  Layers, ArrowDownUp, RefreshCw, Eye
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import type { KPIResult } from '../../services/api';

interface ExploratoryAnalyticsTabProps {
  kpiData: KPIResult | null;
  datasetName?: string;
  onRefresh?: () => void;
}

export const ExploratoryAnalyticsTab: React.FC<ExploratoryAnalyticsTabProps> = ({
  kpiData,
  datasetName,
  onRefresh
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatColumn, setSelectedStatColumn] = useState<string>('');

  // Extract available columns
  const numericColumns = useMemo(() => {
    if (!kpiData?.column_metadata) {
      return kpiData?.primary_metric ? [kpiData.primary_metric] : [];
    }
    return kpiData.column_metadata
      .filter(c => c.semantic_type === 'numeric')
      .map(c => c.name);
  }, [kpiData]);

  const activeMetric = selectedStatColumn || kpiData?.primary_metric || numericColumns[0] || 'Value';

  // Filter sample records
  const filteredRecords = useMemo(() => {
    if (!kpiData?.sample_records) return [];
    if (!searchTerm.trim()) return kpiData.sample_records;
    const term = searchTerm.toLowerCase();
    return kpiData.sample_records.filter(row => 
      Object.values(row).some(v => v !== null && v !== undefined && String(v).toLowerCase().includes(term))
    );
  }, [kpiData?.sample_records, searchTerm]);

  // Download raw sample data as CSV
  const handleExportCSV = () => {
    if (!kpiData?.sample_records || kpiData.sample_records.length === 0) return;
    const headers = Object.keys(kpiData.sample_records[0]);
    const csvRows = [
      headers.join(','),
      ...kpiData.sample_records.map(r => 
        headers.map(h => {
          const val = r[h];
          if (val === null || val === undefined) return '';
          const str = String(val).replace(/"/g, '""');
          return `"${str}"`;
        }).join(',')
      )
    ];
    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${datasetName || 'dataset'}_exploratory_sample.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!kpiData) {
    return (
      <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
        <Layers className="w-10 h-10 text-slate-300 mx-auto mb-3 animate-spin" />
        <h3 className="text-sm font-bold text-slate-700">Loading Exploratory Analytics...</h3>
        <p className="text-xs text-slate-400 mt-1">Extracting multidimensional column distributions and summary statistics.</p>
      </div>
    );
  }

  const statEntries = Object.entries(kpiData.summary_stats || {});
  const regionsList = kpiData.breakdowns?.regions || [];
  const categoriesList = kpiData.breakdowns?.categories || [];
  const distributionBins = kpiData.distribution || [];

  return (
    <div className="space-y-6">
      {/* ── Top Header Controls ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-white rounded-2xl border border-slate-200/80 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600 border border-indigo-200">
              <Sliders className="w-4 h-4" />
            </span>
            <h2 className="text-sm font-bold text-slate-900 m-0">Exploratory Profiler & Slice Engine</h2>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-mono">
              {kpiData.dataset_rows.toLocaleString()} Records
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Statistical distribution, dimensional aggregations, and variable profiling for {datasetName || 'active dataset'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-600 bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
          )}
          <button
            onClick={handleExportCSV}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 transition-colors shadow-xs"
          >
            <Download className="w-3.5 h-3.5" />
            Export Sample CSV
          </button>
        </div>
      </div>

      {/* ── High-Level Distribution & Breakdown Grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Dimension Aggregation Chart */}
        <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-indigo-600" />
                <h3 className="text-sm font-bold text-slate-900 m-0">
                  {regionsList.length > 0 ? 'Top Geographical / Regional Aggregates' : 'Categorical Aggregates'}
                </h3>
              </div>
              <span className="text-[11px] font-semibold text-slate-400 font-mono">
                {activeMetric}
              </span>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Ranked distribution across detected categorical dimensions
            </p>
          </div>

          <div className="h-64 w-full">
            {(regionsList.length > 0 || categoriesList.length > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={regionsList.length > 0 ? regionsList : categoriesList}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis 
                    dataKey="name" 
                    tick={{ fontSize: 10, fill: '#64748b' }} 
                    axisLine={{ stroke: '#e2e8f0' }} 
                    tickLine={false}
                    interval={0}
                    angle={-25}
                    textAnchor="end"
                    height={55}
                  />
                  <YAxis 
                    tick={{ fontSize: 10, fill: '#64748b' }} 
                    axisLine={{ stroke: '#e2e8f0' }} 
                    tickLine={false}
                    tickFormatter={(v) => v >= 1e9 ? `${(v/1e9).toFixed(1)}B` : v >= 1e6 ? `${(v/1e6).toFixed(1)}M` : v >= 1e3 ? `${(v/1e3).toFixed(1)}K` : String(v)}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      borderRadius: 12, 
                      border: '1px solid #e2e8f0', 
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
                      fontSize: 12 
                    }}
                    formatter={(val: any) => [typeof val === 'number' ? val.toLocaleString() : val, activeMetric]}
                  />
                  <Bar dataKey="value" fill="#4f46e5" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                No categorical dimensions identified for breakdown
              </div>
            )}
          </div>
        </div>

        {/* Right: Distribution Histogram */}
        <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <ArrowDownUp className="w-4 h-4 text-emerald-600" />
                <h3 className="text-sm font-bold text-slate-900 m-0">Metric Density & Frequency Distribution</h3>
              </div>
              <span className="text-[11px] font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 font-mono">
                10 Density Bins
              </span>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Binned observation spread and value dispersion for {activeMetric}
            </p>
          </div>

          <div className="h-64 w-full">
            {distributionBins.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={distributionBins}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis 
                    dataKey="bin" 
                    tick={{ fontSize: 9, fill: '#64748b' }} 
                    axisLine={{ stroke: '#e2e8f0' }} 
                    tickLine={false}
                    angle={-20}
                    textAnchor="end"
                    height={50}
                  />
                  <YAxis 
                    tick={{ fontSize: 10, fill: '#64748b' }} 
                    axisLine={{ stroke: '#e2e8f0' }} 
                    tickLine={false} 
                  />
                  <Tooltip 
                    contentStyle={{ 
                      borderRadius: 12, 
                      border: '1px solid #e2e8f0', 
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
                      fontSize: 12 
                    }}
                    formatter={(val: any, _name, props: any) => [
                      `${val.toLocaleString()} records (${props?.payload?.pct || 0}%)`,
                      'Frequency'
                    ]}
                  />
                  <Bar dataKey="count" fill="#10b981" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                Insufficient continuous numeric data to generate histogram
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Summary Statistics Matrix Table ── */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <Table className="w-4 h-4 text-slate-700" />
              <h3 className="text-sm font-bold text-slate-900 m-0">Descriptive Statistical Profile</h3>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Mean, standard deviation, quartiles, and range metrics for continuous numeric variables
            </p>
          </div>
          {numericColumns.length > 1 && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Highlight:</span>
              <select
                value={selectedStatColumn}
                onChange={(e) => setSelectedStatColumn(e.target.value)}
                className="text-xs border border-slate-200 rounded-lg px-2.5 py-1 bg-slate-50 text-slate-700 font-semibold focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
              >
                {numericColumns.map(col => (
                  <option key={col} value={col}>{col}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-2.5 px-3">Column Variable</th>
                <th className="py-2.5 px-3 text-right">Sum / Total</th>
                <th className="py-2.5 px-3 text-right">Mean</th>
                <th className="py-2.5 px-3 text-right">Std Dev</th>
                <th className="py-2.5 px-3 text-right">Min</th>
                <th className="py-2.5 px-3 text-right">Q25 (25%)</th>
                <th className="py-2.5 px-3 text-right">Median (50%)</th>
                <th className="py-2.5 px-3 text-right">Q75 (75%)</th>
                <th className="py-2.5 px-3 text-right">Max</th>
                <th className="py-2.5 px-3 text-right">Null (%)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {statEntries.length > 0 ? (
                statEntries.map(([colName, stat]) => {
                  const isSelected = colName === activeMetric;
                  return (
                    <tr key={colName} className={`hover:bg-slate-50/80 transition-colors ${isSelected ? 'bg-indigo-50/40' : ''}`}>
                      <td className="py-3 px-3 font-sans font-bold text-slate-800 flex items-center gap-2">
                        {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-indigo-600" />}
                        {colName}
                      </td>
                      <td className="py-3 px-3 text-right text-slate-900 font-bold">{stat.formatted_total}</td>
                      <td className="py-3 px-3 text-right text-slate-700">{stat.formatted_mean}</td>
                      <td className="py-3 px-3 text-right text-slate-500">{stat.std.toLocaleString()}</td>
                      <td className="py-3 px-3 text-right text-slate-500">{stat.min.toLocaleString()}</td>
                      <td className="py-3 px-3 text-right text-slate-500">{stat.q25.toLocaleString()}</td>
                      <td className="py-3 px-3 text-right text-emerald-600 font-bold">{stat.median.toLocaleString()}</td>
                      <td className="py-3 px-3 text-right text-slate-500">{stat.q75.toLocaleString()}</td>
                      <td className="py-3 px-3 text-right text-slate-900 font-bold">{stat.max.toLocaleString()}</td>
                      <td className="py-3 px-3 text-right">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] ${stat.missing_pct > 0 ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'}`}>
                          {stat.missing_pct}%
                        </span>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={10} className="py-4 text-center text-slate-400">
                    No continuous numerical attributes available in this dataset.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Raw Dataset Sample Inspector ── */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-slate-700" />
              <h3 className="text-sm font-bold text-slate-900 m-0">Dataset Physical Sample Grid</h3>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Live inspection of verified record instances (showing first {filteredRecords.length} records)
            </p>
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search sample rows..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full text-xs pl-8 pr-3 py-1.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        <div className="overflow-x-auto border border-slate-200 rounded-xl">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-2 px-3 w-12 text-slate-400">#</th>
                {(kpiData.available_columns || []).map(col => (
                  <th key={col} className="py-2 px-3 whitespace-nowrap">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredRecords.length > 0 ? (
                filteredRecords.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/80 transition-colors font-mono">
                    <td className="py-2 px-3 text-slate-400 text-[10px]">{idx + 1}</td>
                    {(kpiData.available_columns || []).map(col => {
                      const val = row[col];
                      const isNull = val === null || val === undefined;
                      return (
                        <td key={col} className="py-2 px-3 whitespace-nowrap text-slate-700">
                          {isNull ? (
                            <span className="text-[10px] text-slate-300 italic font-sans">null</span>
                          ) : typeof val === 'number' ? (
                            val.toLocaleString()
                          ) : (
                            String(val)
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={(kpiData.available_columns?.length || 0) + 1} className="py-6 text-center text-slate-400">
                    {searchTerm ? 'No matching records found in preview.' : 'No preview records available.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
