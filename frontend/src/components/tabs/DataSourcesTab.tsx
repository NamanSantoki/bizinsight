import React, { useState, useEffect } from 'react';
import { Database, AlertTriangle, RefreshCw, Server } from 'lucide-react';
import { apiClient } from '../../services/api';
import type { DataSourceItem } from '../../services/api';

export const DataSourcesTab: React.FC = () => {
  const [sources, setSources] = useState<DataSourceItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const fetchSources = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<DataSourceItem[]>('/enterprise/sources');
      setSources(res.data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSources();
  }, []);

  const handleTestConnection = async (sourceId: string) => {
    setTestingId(sourceId);
    setActionMessage(null);
    try {
      const res = await apiClient.post(`/enterprise/sources/${sourceId}/test`);
      setActionMessage(`[${sourceId}] ${res.data.message || 'Connection verified successfully.'}`);
    } catch (err: any) {
      setActionMessage(`[${sourceId}] Connection test error: ${err.message}`);
    } finally {
      setTestingId(null);
    }
  };

  const handleTriggerSync = async (sourceId: string) => {
    setSyncingId(sourceId);
    setActionMessage(null);
    try {
      const res = await apiClient.post(`/enterprise/sources/${sourceId}/sync`);
      setActionMessage(`[${sourceId}] Sync completed! Processed ${res.data.records_processed?.toLocaleString()} records.`);
      fetchSources();
    } catch (err: any) {
      setActionMessage(`[${sourceId}] Sync error: ${err.message}`);
    } finally {
      setSyncingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-2 rounded-xl bg-cyan-50 text-cyan-700">
              <Database className="w-5 h-5" />
            </span>
            <h2 className="text-lg font-bold text-slate-900 m-0">Enterprise Data Source Manager</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Governed multi-source ingestion connectors (PostgreSQL, MySQL, SQLite, REST API, CSV, Parquet, S3 Lakehouse).
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchSources}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className="p-3.5 bg-blue-50 border border-blue-200 text-blue-800 rounded-xl text-xs flex items-center justify-between">
          <span>{actionMessage}</span>
          <button onClick={() => setActionMessage(null)} className="text-blue-500 hover:text-blue-800 font-bold ml-4">✕</button>
        </div>
      )}

      {/* Grid of Sources */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {sources.map((src) => {
          const isConnected = src.status.toLowerCase() === 'connected';
          return (
            <div
              key={src.id}
              className={`bg-white rounded-2xl p-5 border transition-all ${
                isConnected ? 'border-slate-200/90 hover:border-blue-300' : 'border-rose-200 bg-rose-50/20'
              } shadow-xs flex flex-col justify-between`}
            >
              <div>
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2.5">
                    <div className={`p-2 rounded-xl ${isConnected ? 'bg-blue-50 text-blue-600' : 'bg-rose-100 text-rose-600'}`}>
                      <Server className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 m-0">{src.name}</h3>
                      <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">{src.type}</span>
                    </div>
                  </div>
                  <span
                    className={`inline-flex items-center space-x-1 text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      isConnected ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-100 text-rose-700 border border-rose-300'
                    }`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-emerald-500' : 'bg-rose-500 animate-ping'}`}></span>
                    <span>{src.status}</span>
                  </span>
                </div>

                <div className="mt-4 p-2.5 rounded-xl bg-slate-50 border border-slate-100 text-[11px] font-mono text-slate-600 truncate">
                  {src.connection_url_masked}
                </div>

                {src.last_error && (
                  <div className="mt-2 text-[11px] text-rose-600 flex items-start space-x-1">
                    <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                    <span>{src.last_error}</span>
                  </div>
                )}

                <div className="mt-4 grid grid-cols-3 gap-2 border-t border-slate-100 pt-3 text-center">
                  <div>
                    <span className="text-[10px] text-slate-400 font-medium">Rows</span>
                    <p className="text-xs font-bold text-slate-800 m-0">{(src.rows_count / 1000).toFixed(1)}k</p>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 font-medium">Quality</span>
                    <p className="text-xs font-bold text-emerald-600 m-0">{src.quality_score}%</p>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 font-medium">Last Sync</span>
                    <p className="text-[10px] font-semibold text-slate-700 m-0 truncate">{src.last_sync.split(' ')[1] || 'Just now'}</p>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center space-x-2">
                <button
                  onClick={() => handleTestConnection(src.id)}
                  disabled={testingId === src.id}
                  className="flex-1 py-1.5 px-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition"
                >
                  {testingId === src.id ? 'Testing...' : 'Test Connection'}
                </button>
                <button
                  onClick={() => handleTriggerSync(src.id)}
                  disabled={syncingId === src.id}
                  className="flex-1 py-1.5 px-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold transition"
                >
                  {syncingId === src.id ? 'Syncing...' : 'Sync Now'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
