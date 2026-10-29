import React, { useState, useEffect } from 'react';
import { Sliders, Target, CheckCircle2, Sparkles, RefreshCw } from 'lucide-react';
import { apiClient } from '../../services/api';
import type { DigitalTwinResponse, PrescriptiveResponse } from '../../services/api';

export const DigitalTwinTab: React.FC = () => {
  // Scenario Levers
  const [marketingDelta, setMarketingDelta] = useState<number>(15);
  const [priceDelta, setPriceDelta] = useState<number>(3);
  const [salesStaffDelta, setSalesStaffDelta] = useState<number>(8);
  const [scenarioRes, setScenarioRes] = useState<DigitalTwinResponse | null>(null);
  const [simLoading, setSimLoading] = useState<boolean>(false);

  // Prescriptive Optimizer state
  const [targetRevenue, setTargetRevenue] = useState<number>(25.0);
  const [minMargin, setMinMargin] = useState<number>(20.0);
  const [maxBudget, setMaxBudget] = useState<number>(4.0);
  const [prescriptiveRes, setPrescriptiveRes] = useState<PrescriptiveResponse | null>(null);
  const [optLoading, setOptLoading] = useState<boolean>(false);

  const runSimulation = async (mkt = marketingDelta, prc = priceDelta, stf = salesStaffDelta) => {
    try {
      setSimLoading(true);
      const res = await apiClient.post<DigitalTwinResponse>('/enterprise/decision/scenario', {
        marketing_delta_pct: mkt,
        price_delta_pct: prc,
        sales_staff_delta_pct: stf,
      });
      setScenarioRes(res.data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setSimLoading(false);
    }
  };

  const runOptimization = async () => {
    try {
      setOptLoading(true);
      const res = await apiClient.post<PrescriptiveResponse>('/enterprise/decision/prescriptive', {
        target_revenue_cr: targetRevenue,
        min_margin_pct: minMargin,
        max_marketing_budget_cr: maxBudget,
      });
      setPrescriptiveRes(res.data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setOptLoading(false);
    }
  };

  useEffect(() => {
    runSimulation(15, 3, 8);
    runOptimization();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-2 rounded-xl bg-pink-50 text-pink-700">
              <Sliders className="w-5 h-5" />
            </span>
            <h2 className="text-lg font-bold text-slate-900 m-0">Enterprise Digital Twin & Prescriptive Decision Intelligence</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Simulate macroeconomic scenarios with elasticity-driven prediction intervals or solve inverse goal-seek optimization problems.
          </p>
        </div>
      </div>

      {/* Top Section: Digital Twin Scenario Simulator */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900 m-0">What-If Multi-Lever Simulation</h3>
            <p className="text-xs text-slate-400">Microeconomic production frontier with empirical cross-elasticity</p>
          </div>
          <button
            onClick={() => runSimulation()}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-pink-600 hover:bg-pink-700 rounded-lg transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${simLoading ? 'animate-spin' : ''}`} />
            <span>Re-simulate</span>
          </button>
        </div>

        {/* Sliders Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Lever 1 */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 space-y-2">
            <div className="flex justify-between text-xs">
              <span className="font-bold text-slate-700">Marketing Budget Shift</span>
              <span className="font-mono font-bold text-pink-600">{marketingDelta > 0 ? `+${marketingDelta}%` : `${marketingDelta}%`}</span>
            </div>
            <input
              type="range"
              min="-20"
              max="50"
              value={marketingDelta}
              onChange={(e) => {
                const val = Number(e.target.value);
                setMarketingDelta(val);
                runSimulation(val, priceDelta, salesStaffDelta);
              }}
              className="w-full accent-pink-600 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>-20%</span>
              <span>Baseline (0%)</span>
              <span>+50%</span>
            </div>
          </div>

          {/* Lever 2 */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 space-y-2">
            <div className="flex justify-between text-xs">
              <span className="font-bold text-slate-700">Average Price Adjustment</span>
              <span className="font-mono font-bold text-pink-600">{priceDelta > 0 ? `+${priceDelta}%` : `${priceDelta}%`}</span>
            </div>
            <input
              type="range"
              min="-10"
              max="20"
              value={priceDelta}
              onChange={(e) => {
                const val = Number(e.target.value);
                setPriceDelta(val);
                runSimulation(marketingDelta, val, salesStaffDelta);
              }}
              className="w-full accent-pink-600 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>-10%</span>
              <span>Baseline (0%)</span>
              <span>+20%</span>
            </div>
          </div>

          {/* Lever 3 */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 space-y-2">
            <div className="flex justify-between text-xs">
              <span className="font-bold text-slate-700">Sales Headcount Shift</span>
              <span className="font-mono font-bold text-pink-600">{salesStaffDelta > 0 ? `+${salesStaffDelta}%` : `${salesStaffDelta}%`}</span>
            </div>
            <input
              type="range"
              min="-20"
              max="40"
              value={salesStaffDelta}
              onChange={(e) => {
                const val = Number(e.target.value);
                setSalesStaffDelta(val);
                runSimulation(marketingDelta, priceDelta, val);
              }}
              className="w-full accent-pink-600 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>-20%</span>
              <span>Baseline (0%)</span>
              <span>+40%</span>
            </div>
          </div>
        </div>

        {/* Projected Cards */}
        {scenarioRes && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2">
            <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-200">
              <span className="text-[11px] font-semibold text-blue-700">Projected Revenue</span>
              <p className="text-xl font-black text-slate-900 mt-1 m-0">₹{scenarioRes.projected.revenue_cr} Cr</p>
              <span className="text-[10px] text-blue-600 font-semibold">
                (Baseline: ₹{scenarioRes.baseline.revenue_cr} Cr, Δ +₹{scenarioRes.projected.revenue_delta_cr} Cr)
              </span>
              <div className="mt-2 text-[10px] font-mono text-slate-500">
                80% Pred. Interval: ₹{scenarioRes.projected.prediction_interval_80[0]} - ₹{scenarioRes.projected.prediction_interval_80[1]} Cr
              </div>
            </div>

            <div className="p-4 rounded-xl bg-emerald-50/60 border border-emerald-200">
              <span className="text-[11px] font-semibold text-emerald-700">Projected Margin</span>
              <p className="text-xl font-black text-slate-900 mt-1 m-0">{scenarioRes.projected.margin_pct}%</p>
              <span className="text-[10px] text-emerald-600 font-semibold">
                (Baseline: {scenarioRes.baseline.margin_pct}%, Δ {scenarioRes.projected.margin_delta_pts > 0 ? `+${scenarioRes.projected.margin_delta_pts}` : scenarioRes.projected.margin_delta_pts} pts)
              </span>
              <div className="mt-2 text-[10px] font-mono text-slate-500">
                Operating bounds: 5.0% - 60.0%
              </div>
            </div>

            <div className="p-4 rounded-xl bg-purple-50/60 border border-purple-200">
              <span className="text-[11px] font-semibold text-purple-700">Expected Customer Base</span>
              <p className="text-xl font-black text-slate-900 mt-1 m-0">{scenarioRes.projected.customers_count.toLocaleString()}</p>
              <span className="text-[10px] text-purple-600 font-semibold">
                (Δ {scenarioRes.projected.customer_delta > 0 ? `+${scenarioRes.projected.customer_delta.toLocaleString()}` : scenarioRes.projected.customer_delta.toLocaleString()} accounts)
              </span>
              <div className="mt-2 text-[10px] font-mono text-slate-500">
                Elastic churn adjusted
              </div>
            </div>

            <div className="p-4 rounded-xl bg-amber-50/60 border border-amber-200">
              <span className="text-[11px] font-semibold text-amber-700">Simulation Confidence</span>
              <p className="text-xl font-black text-slate-900 mt-1 m-0">{scenarioRes.projected.confidence_score}%</p>
              <span className="text-[10px] text-amber-600 font-semibold">
                Econometric Fit: High
              </span>
              <div className="mt-2 text-[10px] font-mono text-slate-500">
                {scenarioRes.evidence[0]}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Section: Prescriptive Goal-Seek Optimizer */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <div className="flex items-center space-x-2">
              <Target className="w-4 h-4 text-orange-600" />
              <h3 className="text-sm font-bold text-slate-900 m-0">Prescriptive Goal-Seek Optimizer</h3>
            </div>
            <p className="text-xs text-slate-400">Specify business objectives and guardrails to solve for optimal lever allocations.</p>
          </div>
          <button
            onClick={runOptimization}
            disabled={optLoading}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-orange-600 hover:bg-orange-700 rounded-lg transition"
          >
            <Sparkles className={`w-3.5 h-3.5 ${optLoading ? 'animate-spin' : ''}`} />
            <span>{optLoading ? 'Solving...' : 'Solve Optimal Strategy'}</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1">Target Revenue (Cr)</label>
            <input
              type="number"
              step="0.5"
              value={targetRevenue}
              onChange={(e) => setTargetRevenue(Number(e.target.value))}
              className="w-full p-2.5 rounded-xl border border-slate-200 text-xs font-semibold text-slate-800"
            />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1">Minimum Margin Guardrail (%)</label>
            <input
              type="number"
              step="0.5"
              value={minMargin}
              onChange={(e) => setMinMargin(Number(e.target.value))}
              className="w-full p-2.5 rounded-xl border border-slate-200 text-xs font-semibold text-slate-800"
            />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1">Max Marketing Spend (Cr)</label>
            <input
              type="number"
              step="0.2"
              value={maxBudget}
              onChange={(e) => setMaxBudget(Number(e.target.value))}
              className="w-full p-2.5 rounded-xl border border-slate-200 text-xs font-semibold text-slate-800"
            />
          </div>
        </div>

        {prescriptiveRes && (
          <div className="p-4 bg-orange-50/50 rounded-xl border border-orange-200 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-orange-900 flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Optimal Strategy Solved (Feasibility: {prescriptiveRes.feasibility_score}%)</span>
              </span>
              <span className="text-xs font-bold text-orange-800">
                Projected Revenue: ₹{prescriptiveRes.expected_outcome.revenue_cr} Cr | Margin: {prescriptiveRes.expected_outcome.margin_pct}%
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
              <div className="p-3 bg-white rounded-lg border border-orange-100 text-xs">
                <span className="text-slate-400 font-medium">Recommended Marketing:</span>
                <p className="text-sm font-bold text-slate-900 m-0 mt-0.5">{prescriptiveRes.recommended_strategy.marketing_spend_delta}</p>
                <span className="text-[10px] text-slate-400">Spend: ₹{prescriptiveRes.expected_outcome.marketing_spend_cr} Cr</span>
              </div>
              <div className="p-3 bg-white rounded-lg border border-orange-100 text-xs">
                <span className="text-slate-400 font-medium">Recommended Pricing:</span>
                <p className="text-sm font-bold text-slate-900 m-0 mt-0.5">{prescriptiveRes.recommended_strategy.price_optimization_delta}</p>
                <span className="text-[10px] text-slate-400">Protects margin guardrail</span>
              </div>
              <div className="p-3 bg-white rounded-lg border border-orange-100 text-xs">
                <span className="text-slate-400 font-medium">Recommended Sales Capacity:</span>
                <p className="text-sm font-bold text-slate-900 m-0 mt-0.5">{prescriptiveRes.recommended_strategy.sales_capacity_delta}</p>
                <span className="text-[10px] text-slate-400">Fulfills pipeline conversion</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
