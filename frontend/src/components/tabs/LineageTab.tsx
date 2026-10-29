import React, { useState, useEffect } from 'react';
import { GitBranch, UserCheck, Clock, Database, BarChart3, Cpu } from 'lucide-react';
import { apiClient } from '../../services/api';
import type { LineageGraphData, LineageNodeData } from '../../services/api';

export const LineageTab: React.FC = () => {
  const [lineage, setLineage] = useState<LineageGraphData | null>(null);
  const [selectedNode, setSelectedNode] = useState<LineageNodeData | null>(null);

  useEffect(() => {
    const fetchLineage = async () => {
      try {
        const res = await apiClient.get<LineageGraphData>('/enterprise/lineage');
        setLineage(res.data);
        if (res.data.nodes.length > 0) {
          // Default to Curated fact table
          const curated = res.data.nodes.find(n => n.id === 'lake_curated_sales') || res.data.nodes[0];
          setSelectedNode(curated);
        }
      } catch (err: any) {
        console.error(err);
      }
    };
    fetchLineage();
  }, []);

  const getLayerBadge = (layer: string) => {
    switch (layer) {
      case 'source': return 'bg-cyan-100 text-cyan-800 border-cyan-200';
      case 'raw': return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'clean': return 'bg-slate-200 text-slate-800 border-slate-300';
      case 'curated': return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'metric': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'model': return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'dashboard': return 'bg-rose-100 text-rose-800 border-rose-200';
      default: return 'bg-slate-100 text-slate-700';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-2 rounded-xl bg-indigo-50 text-indigo-700">
              <GitBranch className="w-5 h-5" />
            </span>
            <h2 className="text-lg font-bold text-slate-900 m-0">End-to-End Enterprise Data Lineage</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Complete DAG tracking: Transactional Sources → Bronze/Silver/Gold Lakehouse → KPIs → Models → Executive Dashboards.
          </p>
        </div>
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-600">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
          <span>{lineage?.nodes.length || 0} Lineage Nodes Active</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: DAG Pipeline Flow */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
          <h3 className="text-sm font-bold text-slate-900 m-0">Interactive Lineage Graph (DAG)</h3>
          <p className="text-xs text-slate-400">Click any pipeline node to inspect transformation logic, schemas, and consumers.</p>

          <div className="space-y-4 pt-2">
            {lineage?.nodes.map((node) => {
              const isSelected = selectedNode?.id === node.id;
              return (
                <div
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50/40 shadow-sm ring-2 ring-blue-500/20'
                      : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50/60'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-lg ${isSelected ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600'}`}>
                        {node.layer === 'metric' ? <BarChart3 className="w-4 h-4" /> : node.layer === 'model' ? <Cpu className="w-4 h-4" /> : <Database className="w-4 h-4" />}
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-slate-900 m-0">{node.name}</h4>
                        <span className="text-[10px] text-slate-400 font-mono">{node.id}</span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase border ${getLayerBadge(node.layer)}`}>
                        {node.layer}
                      </span>
                      <span className="text-xs font-bold text-emerald-600">{node.quality_score}% DQ</span>
                    </div>
                  </div>

                  <div className="mt-2.5 text-[11px] text-slate-600 line-clamp-1">
                    <span className="text-slate-400 font-medium">Transform: </span>
                    <span className="font-mono text-slate-700">{node.transformation}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Selected Node Detail Inspector */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-5">
          {selectedNode ? (
            <div className="space-y-4">
              <div className="border-b border-slate-100 pb-3">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase border ${getLayerBadge(selectedNode.layer)}`}>
                  {selectedNode.layer} Layer
                </span>
                <h3 className="text-base font-bold text-slate-900 mt-2 m-0">{selectedNode.name}</h3>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">{selectedNode.id}</p>
              </div>

              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Source Provenance</span>
                  <p className="font-mono text-[11px] text-slate-700 bg-slate-50 p-2 rounded-lg border border-slate-100 mt-1 break-all">
                    {selectedNode.source}
                  </p>
                </div>

                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Transformation Logic</span>
                  <p className="font-mono text-[11px] text-blue-900 bg-blue-50/60 p-2.5 rounded-lg border border-blue-100 mt-1">
                    {selectedNode.transformation}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-1">
                  <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="text-[10px] text-slate-400 font-medium">Records Processed</span>
                    <p className="text-xs font-bold text-slate-900 m-0">{selectedNode.records?.toLocaleString()}</p>
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="text-[10px] text-slate-400 font-medium">Data Quality</span>
                    <p className="text-xs font-bold text-emerald-600 m-0">{selectedNode.quality_score}%</p>
                  </div>
                </div>

                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Upstream Datasets</span>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {selectedNode.upstream_datasets?.length > 0 ? (
                      selectedNode.upstream_datasets.map((u) => (
                        <span key={u} className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-[10px] font-mono">
                          {u}
                        </span>
                      ))
                    ) : (
                      <span className="text-[11px] text-slate-400 italic">None (Root Origin)</span>
                    )}
                  </div>
                </div>

                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Downstream Consumers</span>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {selectedNode.downstream_consumers?.length > 0 ? (
                      selectedNode.downstream_consumers.map((d) => (
                        <span key={d} className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded text-[10px] font-mono font-semibold">
                          {d}
                        </span>
                      ))
                    ) : (
                      <span className="text-[11px] text-slate-400 italic">None (Terminal Consumer)</span>
                    )}
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 text-[11px] text-slate-500 space-y-1">
                  <div className="flex items-center space-x-1.5">
                    <UserCheck className="w-3.5 h-3.5 text-slate-400" />
                    <span>Owner: {selectedNode.owner}</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <span>Last Updated: {selectedNode.last_updated}</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center text-slate-400 py-12 text-xs">
              Select a node from the DAG to inspect metadata.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
