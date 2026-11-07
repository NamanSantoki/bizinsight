import React, { useState } from "react";
import { Terminal, Play, Loader2, Database, AlertCircle, CheckCircle } from "lucide-react";
import { apiClient } from "../../services/api";

interface NLQResponse {
  query: string;
  sql: string;
  result: any[];
  contract_id?: string;
}

export const NLQTab: React.FC = () => {
  const [query, setQuery] = useState("");
  const [datasetId, setDatasetId] = useState("8");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<NLQResponse | null>(null);
  const [error, setError] = useState<string>("");

  const runQuery = async () => {
    if (!query || !datasetId) {
      setError("Both query and dataset ID are required.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await apiClient.post<NLQResponse>("/enterprise/nlq/", {
        query,
        dataset_id: datasetId,
      });
      setResponse(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Unexpected query translation error.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-700">
            <Terminal className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900 m-0">Governed Natural-Language Query Studio</h2>
            <p className="text-xs text-slate-500 m-0">Deterministic text-to-SQL translation with zero-hallucination metric compliance</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">Dataset ID</label>
            <div className="relative">
              <Database className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Dataset ID (e.g. 8)"
                value={datasetId}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDatasetId(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
          <div className="md:col-span-3">
            <label className="block text-xs font-bold text-slate-700 mb-1.5">Business Question</label>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="e.g. What is the total passengers by month, or highest volume?"
                value={query}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && runQuery()}
                className="flex-1 px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
              />
              <button
                onClick={runQuery}
                disabled={loading}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-xl shadow-xs flex items-center space-x-1.5 transition-colors disabled:opacity-50"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                <span>Run</span>
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {response && (
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-emerald-600 text-xs font-bold">
              <CheckCircle className="w-4 h-4" />
              <span>Query Successfully Executed & Audited</span>
            </div>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600">
              {response.result.length} Records
            </span>
          </div>

          <div>
            <span className="block text-xs font-bold text-slate-500 mb-1">Generated AST-Validated SQL</span>
            <pre className="bg-slate-900 text-slate-100 font-mono text-xs p-3.5 rounded-xl overflow-x-auto border border-slate-800">
              {response.sql}
            </pre>
          </div>

          <div>
            <span className="block text-xs font-bold text-slate-500 mb-2">Query Results</span>
            <div className="overflow-x-auto border border-slate-100 rounded-xl">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-b border-slate-100">
                  <tr>
                    {response.result.length > 0 &&
                      Object.keys(response.result[0]).map((col) => (
                        <th key={col} className="px-4 py-2.5">{col}</th>
                      ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {response.result.slice(0, 10).map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50">
                      {Object.values(row).map((val: any, i) => (
                        <td key={i} className="px-4 py-2 text-slate-700">{String(val)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
