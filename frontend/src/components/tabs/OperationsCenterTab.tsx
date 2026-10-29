import React, { useState, useEffect } from 'react';
import { Radio, AlertTriangle, RefreshCw } from 'lucide-react';
import { apiClient } from '../../services/api';
import type { OperationsCenterData, CostData } from '../../services/api';

export const OperationsCenterTab: React.FC = () => {
  const [opsData, setOpsData] = useState<OperationsCenterData | null>(null);
  const [costData, setCostData] = useState<CostData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [probeResult, setProbeResult] = useState<any>(null);

  const fetchOperationsData = async () => {
    try {
      setLoading(true);
      const [opRes, costRes] = await Promise.all([
        apiClient.get<OperationsCenterData>('/enterprise/observability/operations'),
        apiClient.get<CostData>('/enterprise/observability/costs'),
      ]);
      setOpsData(opRes.data);
      setCostData(costRes.data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOperationsData();
  }, []);

  const runProbe = async (endpoint: string) => {
    try {
      const res = await apiClient.get(endpoint);
      setProbeResult({ endpoint, data: res.data });
    } catch (err: any) {
      setProbeResult({ endpoint, error: err.message });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-2 rounded-xl bg-cyan-50 text-cyan-700">
              <Radio className="w-5 h-5" />
            </span>
            <h2 className="text-lg font-bold text-slate-900 m-0">Operations Center, Observability & Cloud Cost Governance</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Real-time subsystem observability, Kubernetes health probes, active incident triage, and cost attribution.
          </p>
        </div>
        <button
          onClick={fetchOperationsData}
          className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Ops</span>
        </button>
      </div>

      {/* Subsystem Health Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {opsData?.services.map((svc) => {
          const isHealthy = svc.status === 'HEALTHY';
          return (
            <div
              key={svc.service}
              className={`p-4 rounded-2xl border ${
                isHealthy ? 'bg-white border-slate-200/80' : 'bg-amber-50/40 border-amber-300'
              } shadow-xs space-y-2`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-bold text-slate-400">Service</span>
                <span className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`}></span>
              </div>
              <h4 className="text-xs font-bold text-slate-900 m-0 leading-tight">{svc.service}</h4>
              <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-100">
                <span className="text-slate-400">Latency: {svc.latency_ms}ms</span>
                <span className="font-semibold text-slate-700">{svc.uptime}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Active Incidents & Kubernetes Probes Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Active Incidents */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900 m-0">Active Incident Management</h3>
              <p className="text-xs text-slate-400">Live operational events and remediation tracking</p>
            </div>
            <span className="text-xs font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
              {opsData?.active_incidents.length || 0} Open
            </span>
          </div>

          <div className="space-y-3">
            {opsData?.active_incidents.map((inc) => (
              <div key={inc.id} className="p-4 rounded-xl bg-amber-50/50 border border-amber-200 text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <span className="font-bold text-slate-900">{inc.id}: {inc.title}</span>
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-200 text-amber-900 uppercase">
                    {inc.severity}
                  </span>
                </div>
                <p className="text-slate-600 m-0">{inc.impact}</p>
                <div className="p-2 bg-white rounded-lg border border-amber-100 text-[11px] font-mono text-slate-700">
                  <span className="font-bold text-slate-900">Remediation: </span>{inc.remediation}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Kubernetes Probes Runner */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900 m-0">Standard Kubernetes Health Probes</h3>
              <p className="text-xs text-slate-400">Click to execute live microservice probes</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <button
              onClick={() => runProbe('/health/live')}
              className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-left transition"
            >
              GET /health/live
            </button>
            <button
              onClick={() => runProbe('/health/ready')}
              className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-left transition"
            >
              GET /health/ready
            </button>
            <button
              onClick={() => runProbe('/health/database')}
              className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-left transition"
            >
              GET /health/database
            </button>
            <button
              onClick={() => runProbe('/health/ml')}
              className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-left transition"
            >
              GET /health/ml
            </button>
          </div>

          {probeResult && (
            <div className="p-3 bg-slate-900 rounded-xl text-xs font-mono text-emerald-400 border border-slate-800 overflow-x-auto">
              <div className="text-[10px] text-slate-500 border-b border-slate-800 pb-1 mb-2">
                Probe Result: {probeResult.endpoint}
              </div>
              <pre className="m-0 leading-relaxed">{JSON.stringify(probeResult.data || probeResult.error, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>

      {/* Cloud Cost Observability */}
      {costData && (
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900 m-0">Granular Cloud & Infrastructure Cost Observability</h3>
              <p className="text-xs text-slate-400">Attribution across SQL queries, ML compute, GenAI embeddings, and curated storage</p>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-slate-400 uppercase font-bold">Total Spend ({costData.billing_cycle})</span>
              <p className="text-lg font-black text-slate-900 m-0">₹{costData.total_spend.toLocaleString()}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {costData.breakdown_by_category.map((cat) => (
              <div key={cat.category} className="p-4 bg-slate-50 rounded-xl border border-slate-100 text-xs space-y-1">
                <span className="text-slate-500 font-medium">{cat.category}</span>
                <p className="text-base font-bold text-slate-900 m-0">₹{cat.cost.toLocaleString()}</p>
                <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden mt-2">
                  <div className="bg-blue-600 h-full rounded-full" style={{ width: `${cat.pct}%` }}></div>
                </div>
                <span className="text-[10px] text-slate-400 font-semibold">{cat.pct}% of monthly cloud bill</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
