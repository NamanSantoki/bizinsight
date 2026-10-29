import React, { useState, useEffect } from 'react';
import { Cpu, AlertTriangle, RefreshCw } from 'lucide-react';
import { apiClient } from '../../services/api';
import type { ModelRegistryItem, MLMonitoringItem } from '../../services/api';

export const MLOpsRegistryTab: React.FC = () => {
  const [monitoring, setMonitoring] = useState<MLMonitoringItem[]>([]);
  const [selectedModel, setSelectedModel] = useState<ModelRegistryItem | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [mRes, monRes] = await Promise.all([
        apiClient.get<ModelRegistryItem[]>('/enterprise/mlops/models'),
        apiClient.get<MLMonitoringItem[]>('/enterprise/mlops/monitoring'),
      ]);
      setMonitoring(monRes.data);
      if (mRes.data.length > 0) {
        setSelectedModel(mRes.data[0]);
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handlePromoteStage = async (modelName: string, version: string, stage: string) => {
    try {
      setActionMsg(null);
      await apiClient.post('/enterprise/mlops/models/transition', {
        model_name: modelName,
        version: version,
        target_stage: stage,
      });
      setActionMsg(`Success: Promoted ${version} to ${stage}`);
      fetchData();
    } catch (err: any) {
      setActionMsg(`Error: ${err.message}`);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PRODUCTION': return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'STAGING': return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'APPROVED': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'ARCHIVED': return 'bg-slate-100 text-slate-500 border-slate-200';
      default: return 'bg-amber-100 text-amber-800 border-amber-300';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-2 rounded-xl bg-purple-50 text-purple-700">
              <Cpu className="w-5 h-5" />
            </span>
            <h2 className="text-lg font-bold text-slate-900 m-0">Enterprise MLOps Model Registry & Drift Observability</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Governed model lifecycle (v1..v7), production deployments, live latency percentiles, and PSI population stability drift monitoring.
          </p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      {actionMsg && (
        <div className="p-3 bg-blue-50 border border-blue-200 text-blue-800 rounded-xl text-xs flex justify-between">
          <span>{actionMsg}</span>
          <button onClick={() => setActionMsg(null)} className="font-bold">✕</button>
        </div>
      )}

      {/* Real-time Model Health & Drift Section */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900 m-0">Production Inference & Population Drift Telemetry</h3>
            <p className="text-xs text-slate-400">Live monitoring of deployed production endpoints</p>
          </div>
          <span className="text-xs font-mono text-slate-400 font-semibold">Updated 1 min ago</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {monitoring.map((m) => {
            const isWarning = m.drift_status === 'WARNING';
            return (
              <div
                key={m.model_id}
                className={`p-5 rounded-xl border ${
                  isWarning ? 'border-amber-300 bg-amber-50/20' : 'border-slate-200 bg-slate-50/30'
                } space-y-4`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900 m-0">{m.model_name}</h4>
                    <span className="text-[10px] font-mono text-slate-400 uppercase">ID: {m.model_id}</span>
                  </div>
                  <span
                    className={`inline-flex items-center space-x-1 text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                      isWarning ? 'bg-amber-100 text-amber-800 border-amber-300' : 'bg-emerald-100 text-emerald-800 border-emerald-300'
                    }`}
                  >
                    <span>{m.drift_status === 'WARNING' ? '⚠ DRIFT WARNING' : '● STABLE'}</span>
                  </span>
                </div>

                <div className="grid grid-cols-4 gap-2 text-center">
                  <div className="p-2 bg-white rounded-lg border border-slate-100">
                    <span className="text-[10px] text-slate-400">Pred. Volume</span>
                    <p className="text-xs font-bold text-slate-800 m-0">{(m.prediction_volume / 1000000).toFixed(2)}M</p>
                  </div>
                  <div className="p-2 bg-white rounded-lg border border-slate-100">
                    <span className="text-[10px] text-slate-400">P95 Latency</span>
                    <p className="text-xs font-bold text-slate-800 m-0">{m.latency_p95_ms}ms</p>
                  </div>
                  <div className="p-2 bg-white rounded-lg border border-slate-100">
                    <span className="text-[10px] text-slate-400">Error Rate</span>
                    <p className="text-xs font-bold text-slate-800 m-0">{m.error_rate_pct}%</p>
                  </div>
                  <div className="p-2 bg-white rounded-lg border border-slate-100">
                    <span className="text-[10px] text-slate-400">Feature Drift</span>
                    <p className={`text-xs font-bold m-0 ${isWarning ? 'text-amber-600' : 'text-emerald-600'}`}>
                      {m.feature_drift_pct}%
                    </p>
                  </div>
                </div>

                {m.retraining_recommendation.is_candidate && (
                  <div className="p-2.5 rounded-lg bg-amber-100/60 border border-amber-200 text-[11px] text-amber-900 space-y-1">
                    <div className="font-bold flex items-center space-x-1">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
                      <span>Retraining Candidate ({m.retraining_recommendation.priority} Priority)</span>
                    </div>
                    <p className="m-0 text-amber-800">{m.retraining_recommendation.reason}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Model Registry Version Stepper */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900 m-0">Governed Model Registry (v1..v7)</h3>
            <p className="text-xs text-slate-400">Formal lifecycle state machine: Evaluation → Staging → Production</p>
          </div>
          <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
            Current Production: {selectedModel?.current_production_version || 'v7'}
          </span>
        </div>

        {selectedModel && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-100">
                <tr>
                  <th className="py-2.5 px-3">Version</th>
                  <th className="py-2.5 px-3">Algorithm</th>
                  <th className="py-2.5 px-3">Dataset Lineage</th>
                  <th className="py-2.5 px-3">Features</th>
                  <th className="py-2.5 px-3">MAE</th>
                  <th className="py-2.5 px-3">RMSE</th>
                  <th className="py-2.5 px-3">Accuracy</th>
                  <th className="py-2.5 px-3">Lifecycle Stage</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {selectedModel.versions.map((ver: any) => {
                  const isProd = ver.status === 'PRODUCTION';
                  return (
                    <tr key={ver.version} className={isProd ? 'bg-emerald-50/30 font-semibold' : 'hover:bg-slate-50'}>
                      <td className="py-3 px-3 font-mono font-bold text-slate-900">{ver.version}</td>
                      <td className="py-3 px-3 text-slate-700">{ver.algorithm}</td>
                      <td className="py-3 px-3 font-mono text-[11px] text-slate-500">{ver.dataset}</td>
                      <td className="py-3 px-3 text-slate-700">{ver.features_count}</td>
                      <td className="py-3 px-3 font-mono text-slate-700">{ver.mae.toLocaleString()}</td>
                      <td className="py-3 px-3 font-mono text-slate-700">{ver.rmse.toLocaleString()}</td>
                      <td className="py-3 px-3 font-bold text-emerald-700">{ver.accuracy_score}%</td>
                      <td className="py-3 px-3">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getStatusBadge(ver.status)}`}>
                          {ver.status}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right">
                        {!isProd && ver.status !== 'ARCHIVED' && (
                          <button
                            onClick={() => handlePromoteStage(selectedModel.name, ver.version, 'PRODUCTION')}
                            className="px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[11px] font-semibold transition"
                          >
                            Promote to Prod
                          </button>
                        )}
                        {isProd && (
                          <span className="text-[11px] text-emerald-600 font-bold">Active in Cluster</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
