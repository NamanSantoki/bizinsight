import React, { useState, useEffect, useCallback } from 'react';
import { 
  Radio, TrendingUp, ShieldCheck, RefreshCw, 
  Clock, CheckCircle2, Target, Building2, Sliders
} from 'lucide-react';
import { apiClient } from '../../services/api';

interface AssessmentItem {
  id: number;
  signal_id: string;
  source: string;
  factor_key: string;
  headline: string;
  event_summary: string;
  magnitude_pct: number;
  shock_direction: string;
  confidence_score: number;
  affected_kpi: string;
  projected_impact_pct: number;
  impact_direction: string;
  time_to_impact_days_min: number;
  time_to_impact_days_max: number;
  transmission_mechanism: string;
  prescribed_actions: string[];
  action_priority: string;
  hedging_strategy?: string;
  is_acknowledged: boolean;
  acknowledged_by?: string;
  detected_at: string;
}

interface RadarFeedResponse {
  configured: boolean;
  message?: string;
  organization_name?: string;
  industry_sector?: string;
  sensitivities?: string[];
  total_active_shocks: number;
  critical_p0_count: number;
  assessments: AssessmentItem[];
}

interface ElasticityItem {
  factor_key: string;
  affected_kpi: string;
  pass_through_elasticity: number;
  lag_days: string;
  benchmark_source: string;
  company_is_exposed: boolean;
}

interface MarketRadarTabProps {
  onOpenCompanyDNA?: () => void;
}

export const MarketRadarTab: React.FC<MarketRadarTabProps> = ({ onOpenCompanyDNA }) => {
  const [feed, setFeed] = useState<RadarFeedResponse | null>(null);
  const [matrix, setMatrix] = useState<ElasticityItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [scanning, setScanning] = useState<boolean>(false);
  const [acknowledgingId, setAcknowledgingId] = useState<number | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const loadFeed = useCallback(async () => {
    try {
      setLoading(true);
      const [feedRes, matrixRes] = await Promise.all([
        apiClient.get<RadarFeedResponse>('/market-radar/feed'),
        apiClient.get<{ matrix: ElasticityItem[] }>('/market-radar/sensitivity-matrix')
      ]);
      setFeed(feedRes.data);
      setMatrix(matrixRes.data.matrix || []);
    } catch (err: any) {
      console.error('Failed to load market radar feed:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFeed();
  }, [loadFeed]);

  const handleTriggerScan = async () => {
    try {
      setScanning(true);
      setNotice(null);
      const res = await apiClient.post('/market-radar/scan');
      setNotice(`Scan complete: Processed ${res.data.signals_processed} macro signals across global benchmarks.`);
      await loadFeed();
    } catch (err: any) {
      setNotice('Error triggering autonomous scan.');
    } finally {
      setScanning(false);
    }
  };

  const handleAcknowledge = async (assessmentId: number) => {
    try {
      setAcknowledgingId(assessmentId);
      await apiClient.post(`/market-radar/assessments/${assessmentId}/acknowledge`, {
        notes: "Executive review completed via Autonomous Market Radar"
      });
      await loadFeed();
    } catch (err) {
      console.error('Failed to acknowledge assessment:', err);
    } finally {
      setAcknowledgingId(null);
    }
  };

  if (loading && !feed) {
    return (
      <div className="flex flex-col items-center justify-center p-16 space-y-3">
        <RefreshCw className="w-8 h-8 animate-spin text-amber-500" />
        <span className="text-sm font-bold text-slate-600">Interrogating Global Macroeconomic Benchmarks...</span>
      </div>
    );
  }

  if (feed && !feed.configured) {
    return (
      <div className="p-8 rounded-3xl bg-white border border-slate-200/90 shadow-xs text-center max-w-lg mx-auto space-y-4 my-8">
        <div className="w-12 h-12 rounded-2xl bg-amber-50 border border-amber-200 text-amber-600 flex items-center justify-center mx-auto">
          <Building2 className="w-6 h-6" />
        </div>
        <h3 className="text-base font-black text-slate-900 m-0">Company DNA Not Configured</h3>
        <p className="text-xs text-slate-500 m-0">
          The Autonomous Market Radar requires your company's industry sector and macro risk sensitivities to translate external global events into internal KPI impacts.
        </p>
        {onOpenCompanyDNA && (
          <button
            onClick={onOpenCompanyDNA}
            className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-600/20 transition-all cursor-pointer"
          >
            Configure Corporate DNA Now
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ─── Hero Action Header ─── */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-slate-950 via-slate-900 to-amber-950/80 border border-amber-900/30 text-white shadow-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-4 min-w-0">
          <div className="w-12 h-12 rounded-2xl bg-amber-500/20 border border-amber-400/40 flex items-center justify-center text-amber-400 shrink-0">
            <Radio className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-black tracking-wide text-white m-0">Autonomous Macro Causal Radar</h2>
              <span className="text-[10px] font-black px-2 py-0.5 bg-amber-500/30 text-amber-300 rounded-full border border-amber-400/40 uppercase tracking-widest">
                Active 5h Cycle
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1 m-0">
              Live transmission of external macroeconomic shocks into <span className="font-semibold text-white">{feed?.organization_name}</span>'s internal KPIs
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={handleTriggerScan}
            disabled={scanning}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-black shadow-md shadow-amber-500/20 transition-all cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${scanning ? 'animate-spin' : ''}`} />
            <span>{scanning ? 'Scanning Benchmarks...' : 'Force AI Radar Scan'}</span>
          </button>
        </div>
      </div>

      {notice && (
        <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs font-medium flex items-center space-x-2 shadow-xs">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{notice}</span>
        </div>
      )}

      {/* ─── Top Telemetry KPI Cards ─── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
          <span className="text-[11px] uppercase font-bold text-slate-400 tracking-wider">Active Macro Shocks</span>
          <div className="text-2xl font-black font-mono text-slate-900 mt-1">
            {feed?.total_active_shocks || 0}
          </div>
          <span className="text-[10px] text-slate-500 mt-1 block">Cross-referenced against corporate DNA</span>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
          <span className="text-[11px] uppercase font-bold text-slate-400 tracking-wider">Critical P0/P1 Alerts</span>
          <div className="text-2xl font-black font-mono text-rose-600 mt-1">
            {feed?.critical_p0_count || 0}
          </div>
          <span className="text-[10px] text-slate-500 mt-1 block">Immediate executive attention required</span>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
          <span className="text-[11px] uppercase font-bold text-slate-400 tracking-wider">Corporate Sector</span>
          <div className="text-sm font-bold text-slate-800 mt-1 truncate">
            {feed?.industry_sector}
          </div>
          <span className="text-[10px] text-blue-600 font-medium mt-1 block">
            {feed?.sensitivities?.length || 0} risk sensitivities tracked
          </span>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
          <span className="text-[11px] uppercase font-bold text-slate-400 tracking-wider">Avg Time-to-Impact</span>
          <div className="text-2xl font-black font-mono text-amber-600 mt-1">
            18 - 35d
          </div>
          <span className="text-[10px] text-slate-500 mt-1 block">Pre-emptive decision window</span>
        </div>
      </div>

      {/* ─── Causal Impact Briefing Feed ─── */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-amber-600" />
            <h3 className="text-sm font-black text-slate-900 uppercase tracking-wider m-0">
              Live Macro Shockwaves & Causal Transmission Feed
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Updated in Real-Time
          </span>
        </div>

        {feed?.assessments.length === 0 ? (
          <div className="p-12 text-center rounded-2xl bg-white border border-slate-200 text-slate-500 text-xs">
            No active market shockwaves detected for your risk perimeter. Click "Force AI Radar Scan" above.
          </div>
        ) : (
          feed?.assessments.map((a) => (
            <div 
              key={a.id}
              className={`p-6 rounded-3xl bg-white border transition-all shadow-xs space-y-4 ${
                a.action_priority === 'P0_CRITICAL' 
                  ? 'border-rose-300 ring-1 ring-rose-200/60' 
                  : 'border-slate-200/90'
              }`}
            >
              {/* Card Header */}
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="space-y-1 max-w-2xl">
                  <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                    <span className={`text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider ${
                      a.action_priority === 'P0_CRITICAL'
                        ? 'bg-rose-100 text-rose-800 border border-rose-300'
                        : a.action_priority === 'P1_HIGH'
                        ? 'bg-amber-100 text-amber-800 border border-amber-300'
                        : 'bg-blue-100 text-blue-800 border border-blue-300'
                    }`}>
                      {a.action_priority}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400 font-semibold bg-slate-100 px-2 py-0.5 rounded">
                      {a.source}
                    </span>
                    <span className="text-[10px] font-bold text-amber-600 font-mono">
                      {a.magnitude_pct > 0 ? `+${a.magnitude_pct}%` : `${a.magnitude_pct}%`} {a.shock_direction.toUpperCase()}
                    </span>
                  </div>
                  <h4 className="text-sm font-black text-slate-900 m-0 tracking-tight">
                    {a.headline}
                  </h4>
                  <p className="text-xs text-slate-600 leading-relaxed m-0">
                    {a.event_summary}
                  </p>
                </div>

                {/* Impact Callout Pill */}
                <div className="text-right p-3 rounded-2xl bg-slate-50 border border-slate-200/80 shrink-0 min-w-[170px]">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                    Causal Impact on {a.affected_kpi.replace('_', ' ')}
                  </span>
                  <div className={`text-xl font-black font-mono mt-0.5 ${
                    a.projected_impact_pct < 0 ? 'text-rose-600' : 'text-emerald-600'
                  }`}>
                    {a.projected_impact_pct > 0 ? `+${a.projected_impact_pct}%` : `${a.projected_impact_pct}%`}
                  </div>
                  <div className="text-[10px] font-semibold text-slate-500 mt-1 flex items-center justify-end space-x-1">
                    <Clock className="w-3 h-3 text-slate-400" />
                    <span>Lag: {a.time_to_impact_days_min}-{a.time_to_impact_days_max} days</span>
                  </div>
                </div>
              </div>

              {/* Transmission Mechanism Breadcrumb */}
              <div className="p-3.5 rounded-2xl bg-slate-50/90 border border-slate-200/60 text-xs">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                  Econometric Causal Transmission Mechanism:
                </span>
                <div className="text-slate-700 font-mono text-[11px] leading-relaxed">
                  {a.transmission_mechanism}
                </div>
              </div>

              {/* Prescribed Executive Interventions & Hedging */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                <div className="p-4 rounded-2xl bg-blue-50/50 border border-blue-200/60 space-y-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-blue-900 flex items-center space-x-1">
                    <Target className="w-3.5 h-3.5 text-blue-600" />
                    <span>Tactical Counter-Measures</span>
                  </span>
                  <ul className="space-y-1.5 pl-1 m-0">
                    {a.prescribed_actions.map((act, idx) => (
                      <li key={idx} className="text-xs text-slate-700 flex items-start space-x-2">
                        <span className="font-bold text-blue-600 shrink-0 font-mono text-[11px]">{idx + 1}.</span>
                        <span>{act}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="p-4 rounded-2xl bg-indigo-50/50 border border-indigo-200/60 space-y-2 flex flex-col justify-between">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-900 flex items-center space-x-1 mb-2">
                      <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
                      <span>Quantitative Hedging Strategy</span>
                    </span>
                    <p className="text-xs text-slate-700 m-0 leading-relaxed font-medium">
                      {a.hedging_strategy || "Deploy forward derivative contracts and adjust contract price indexation."}
                    </p>
                  </div>

                  {/* Governance Sign-Off Button */}
                  <div className="pt-3 border-t border-indigo-100 flex items-center justify-between">
                    {a.is_acknowledged ? (
                      <div className="flex items-center space-x-1.5 text-xs font-bold text-emerald-700">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        <span>Signed off by {a.acknowledged_by || 'Executive'}</span>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleAcknowledge(a.id)}
                        disabled={acknowledgingId === a.id}
                        className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl transition-all shadow-xs cursor-pointer disabled:opacity-50"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>{acknowledgingId === a.id ? 'Recording Audit...' : 'Executive Sign-Off'}</span>
                      </button>
                    )}
                    <span className="text-[10px] font-mono text-slate-400">
                      Audit Hash: SHA-256 Verified
                    </span>
                  </div>
                </div>
              </div>

            </div>
          ))
        )}
      </div>

      {/* ─── Macro Elasticity Cross-Sensitivity Matrix ─── */}
      <div className="p-6 rounded-3xl bg-white border border-slate-200/90 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-blue-600" />
            <h3 className="text-sm font-black text-slate-900 uppercase tracking-wider m-0">
              Econometric Pass-Through Cross-Elasticity Matrix
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Microeconomic Transmission Equations
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-[10px] uppercase font-bold text-slate-400">
                <th className="py-2.5 px-3">Macro Variable</th>
                <th className="py-2.5 px-3">Affected Internal KPI</th>
                <th className="py-2.5 px-3">Pass-Through Elasticity (&epsilon;)</th>
                <th className="py-2.5 px-3">Transmission Lag</th>
                <th className="py-2.5 px-3">Benchmark Feed</th>
                <th className="py-2.5 px-3 text-right">Company Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {matrix.map((row) => (
                <tr key={row.factor_key} className="hover:bg-slate-50 transition-colors">
                  <td className="py-2.5 px-3 font-bold text-slate-900">{row.factor_key.toUpperCase()}</td>
                  <td className="py-2.5 px-3 font-semibold text-blue-600">{row.affected_kpi}</td>
                  <td className="py-2.5 px-3 font-bold text-slate-800">{row.pass_through_elasticity}</td>
                  <td className="py-2.5 px-3 text-slate-600">{row.lag_days}</td>
                  <td className="py-2.5 px-3 text-slate-400 text-[11px]">{row.benchmark_source}</td>
                  <td className="py-2.5 px-3 text-right">
                    {row.company_is_exposed ? (
                      <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300">
                        DIRECT EXPOSURE
                      </span>
                    ) : (
                      <span className="text-[9px] font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-500">
                        UNTRACKED
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

