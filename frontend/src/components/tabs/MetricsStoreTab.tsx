import React, { useState, useEffect } from 'react';
import { Layers, CheckCircle2, Code2 } from 'lucide-react';
import { apiClient } from '../../services/api';
import type { SemanticMetricItem } from '../../services/api';

export const MetricsStoreTab: React.FC = () => {
  const [metrics, setMetrics] = useState<SemanticMetricItem[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<SemanticMetricItem | null>(null);
  const [selectedDim, setSelectedDim] = useState<string>('region');
  const [compiledResult, setCompiledResult] = useState<any>(null);

  const compileQuery = async (metricId: string, dim: string) => {
    try {
      const res = await apiClient.post('/enterprise/semantic/query', {
        metric_id: metricId,
        dimension: dim,
      });
      setCompiledResult(res.data);
    } catch (err: any) {
      console.error(err);
    }
  };

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await apiClient.get<SemanticMetricItem[]>('/enterprise/semantic/metrics');
        setMetrics(res.data);
        if (res.data.length > 0) {
          setSelectedMetric(res.data[0]);
          compileQuery(res.data[0].id, 'region');
        }
      } catch (err: any) {
        console.error(err);
      }
    };
    fetchMetrics();
  }, []);

  const handleSelectMetric = (m: SemanticMetricItem) => {
    setSelectedMetric(m);
    const defaultDim = m.dimensions[0] || 'region';
    setSelectedDim(defaultDim);
    compileQuery(m.id, defaultDim);
  };

  const handleDimChange = (dim: string) => {
    setSelectedDim(dim);
    if (selectedMetric) {
      compileQuery(selectedMetric.id, dim);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-2 rounded-xl bg-purple-50 text-purple-700">
              <Layers className="w-5 h-5" />
            </span>
            <h2 className="text-lg font-bold text-slate-900 m-0">Semantic Layer & Metrics Store</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Centrally governed metric formulas preventing SQL drift across BI dashboards and AI querying agents.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>Zero Metric Hallucination Guarantee</span>
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Metric Definitions List */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-3">
          <h3 className="text-sm font-bold text-slate-900 m-0">Certified Metric Definitions</h3>
          <p className="text-xs text-slate-400">Single source of truth certified by Finance FP&A.</p>

          <div className="space-y-2.5 pt-2">
            {metrics.map((m) => {
              const isSelected = selectedMetric?.id === m.id;
              return (
                <div
                  key={m.id}
                  onClick={() => handleSelectMetric(m)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'border-purple-500 bg-purple-50/50 shadow-xs ring-2 ring-purple-500/20'
                      : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50/60'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-slate-900 m-0">{m.name}</h4>
                    <span className="text-[10px] font-mono text-purple-700 bg-purple-100 px-1.5 py-0.5 rounded">
                      {m.unit}
                    </span>
                  </div>
                  <div className="mt-2 text-[11px] font-mono text-slate-700 bg-slate-50 px-2 py-1 rounded border border-slate-100 truncate">
                    {m.formula}
                  </div>
                  <div className="mt-2 text-[10px] text-slate-400 flex items-center justify-between">
                    <span>{m.category}</span>
                    <span className="font-semibold text-slate-500">By {m.owner}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Interactive Query Compiler & Dimension Drilldown */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-5">
          {selectedMetric ? (
            <div className="space-y-4">
              <div className="border-b border-slate-100 pb-3 flex items-start justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900 m-0">{selectedMetric.name}</h3>
                  <p className="text-xs text-slate-500 mt-0.5">{selectedMetric.description}</p>
                </div>
                <span className="text-xs font-bold text-purple-700 bg-purple-50 px-2.5 py-1 rounded-lg border border-purple-200">
                  ID: {selectedMetric.id}
                </span>
              </div>

              {/* Dimension Selector */}
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-2">
                  Slice by Governed Dimension:
                </label>
                <div className="flex flex-wrap gap-2">
                  {selectedMetric.dimensions.map((dim) => (
                    <button
                      key={dim}
                      onClick={() => handleDimChange(dim)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                        selectedDim === dim
                          ? 'bg-purple-600 text-white shadow-xs'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                    >
                      {dim}
                    </button>
                  ))}
                </div>
              </div>

              {/* Governed SQL Compiler View */}
              <div className="space-y-2 pt-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-slate-700 flex items-center space-x-1.5">
                    <Code2 className="w-4 h-4 text-purple-600" />
                    <span>Compiled Governed SQL Statement</span>
                  </span>
                  <span className="text-[10px] font-mono text-emerald-600 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    AST Safe & Certified
                  </span>
                </div>
                <pre className="p-4 bg-slate-900 text-emerald-400 rounded-xl font-mono text-xs overflow-x-auto border border-slate-800 leading-relaxed">
                  {compiledResult?.compiled_sql || selectedMetric.sql_expression}
                </pre>
              </div>

              {/* Execution Guarantee Checklist */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                <div className="flex items-center space-x-2 text-slate-700">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Central Definition Enforced</span>
                </div>
                <div className="flex items-center space-x-2 text-slate-700">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>No Ad-Hoc SQL Divergence</span>
                </div>
                <div className="flex items-center space-x-2 text-slate-700">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Citable Evidence In NLQ</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center text-slate-400 py-12 text-xs">
              Select a metric definition to inspect the semantic compiler.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
