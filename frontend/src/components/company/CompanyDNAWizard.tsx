import React, { useState, useEffect } from 'react';
import { 
  Building2, Globe, TrendingUp, Compass, ShieldCheck, 
  Check, ChevronRight, ChevronLeft, X, Sparkles, AlertCircle
} from 'lucide-react';
import { apiClient } from '../../services/api';
import type { CompanyProfile, TaxonomyData } from '../../services/api';

interface CompanyDNAWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (profile: CompanyProfile) => void;
  initialProfile?: CompanyProfile | null;
}

export const CompanyDNAWizard: React.FC<CompanyDNAWizardProps> = ({
  isOpen,
  onClose,
  onSuccess,
  initialProfile
}) => {
  const [step, setStep] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [taxonomies, setTaxonomies] = useState<TaxonomyData | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Form State
  const [orgName, setOrgName] = useState<string>('');
  const [sector, setSector] = useState<string>('');
  const [bizModel, setBizModel] = useState<string>('');
  const [revenueBracket, setRevenueBracket] = useState<string>('USD $10M - $50M');
  const [currencies, setCurrencies] = useState<string[]>(['USD']);
  const [regions, setRegions] = useState<string[]>(['North America']);
  const [sensitivities, setSensitivities] = useState<string[]>(['crude_oil', 'freight_rates']);
  const [competitorsText, setCompetitorsText] = useState<string>('');
  const [kpis, setKpis] = useState<string[]>(['gross_margin', 'inventory_turnover']);
  const [riskTolerance, setRiskTolerance] = useState<string>('moderate');

  useEffect(() => {
    // Fetch standardized enterprise taxonomies
    const loadTaxonomies = async () => {
      try {
        const res = await apiClient.get<TaxonomyData>('/company/profile/taxonomies');
        setTaxonomies(res.data);
        if (!sector && res.data.sectors.length > 0) {
          setSector(res.data.sectors[0].label);
        }
        if (!bizModel && res.data.business_models.length > 0) {
          setBizModel(res.data.business_models[0]);
        }
      } catch (err) {
        console.error('Failed to load taxonomies:', err);
      }
    };
    if (isOpen) {
      loadTaxonomies();
    }
  }, [isOpen]);

  useEffect(() => {
    if (initialProfile) {
      setOrgName(initialProfile.organization_name || '');
      setSector(initialProfile.industry_sector || '');
      setBizModel(initialProfile.business_model || '');
      setRevenueBracket(initialProfile.annual_revenue_bracket || 'USD $10M - $50M');
      setCurrencies(initialProfile.operating_currencies || ['USD']);
      setRegions(initialProfile.geographic_regions || ['North America']);
      setSensitivities(initialProfile.key_macro_sensitivities || []);
      setCompetitorsText((initialProfile.key_competitors || []).join(', '));
      setKpis(initialProfile.monitored_kpis || []);
      setRiskTolerance(initialProfile.risk_tolerance || 'moderate');
    }
  }, [initialProfile]);

  if (!isOpen) return null;

  const toggleArrayItem = (arr: string[], item: string, setter: (val: string[]) => void) => {
    if (arr.includes(item)) {
      if (arr.length > 1) setter(arr.filter(x => x !== item));
    } else {
      setter([...arr, item]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orgName.trim()) {
      setErrorMsg('Organization name is required.');
      return;
    }
    setLoading(true);
    setErrorMsg(null);

    const competitorsList = competitorsText
      .split(',')
      .map(s => s.trim())
      .filter(Boolean);

    const payload: CompanyProfile = {
      organization_name: orgName.trim(),
      industry_sector: sector || 'Retail & E-Commerce',
      business_model: bizModel || 'B2B Enterprise Contracts',
      annual_revenue_bracket: revenueBracket,
      operating_currencies: currencies,
      geographic_regions: regions,
      key_macro_sensitivities: sensitivities,
      key_competitors: competitorsList,
      monitored_kpis: kpis,
      risk_tolerance: riskTolerance
    };

    try {
      const res = await apiClient.post<CompanyProfile>('/company/profile', payload);
      onSuccess(res.data);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to save enterprise company DNA.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden my-auto animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="px-6 py-5 bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-950 text-white flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-blue-500/20 border border-blue-400/30 flex items-center justify-center text-blue-300">
              <Compass className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-black tracking-wide text-white m-0">Corporate DNA & Risk Profile</h3>
                <span className="text-[9px] font-black px-1.5 py-0.5 bg-blue-500/30 text-blue-300 rounded border border-blue-400/40 uppercase tracking-widest">
                  STEP {step} OF 4
                </span>
              </div>
              <p className="text-xs text-slate-300 m-0">Calibrate the Autonomous Market Radar to your company's reality</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-100 h-1.5">
          <div 
            className="bg-blue-600 h-1.5 transition-all duration-300"
            style={{ width: `${(step / 4) * 100}%` }}
          />
        </div>

        {errorMsg && (
          <div className="mx-6 mt-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Form Body */}
        <div className="p-6">
          {/* STEP 1: Corporate Identity */}
          {step === 1 && (
            <div className="space-y-4">
              <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-400">
                <Building2 className="w-4 h-4 text-blue-600" />
                <span>Corporate Identity & Operating Model</span>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Official Organization Name *
                </label>
                <input
                  type="text"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  placeholder="e.g. Acme Global Logistics Corp"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Industry Sector
                  </label>
                  <select
                    value={sector}
                    onChange={(e) => setSector(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  >
                    {taxonomies?.sectors.map(s => (
                      <option key={s.id} value={s.label}>{s.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Business Model
                  </label>
                  <select
                    value={bizModel}
                    onChange={(e) => setBizModel(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  >
                    {taxonomies?.business_models.map(m => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Annual Revenue Tier
                </label>
                <select
                  value={revenueBracket}
                  onChange={(e) => setRevenueBracket(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value="Under USD $10M">Under USD $10M</option>
                  <option value="USD $10M - $50M">USD $10M - $50M</option>
                  <option value="USD $50M - $250M">USD $50M - $250M</option>
                  <option value="USD $250M - $1B">USD $250M - $1B</option>
                  <option value="USD $1B+ Enterprise">USD $1B+ Global Enterprise</option>
                </select>
              </div>
            </div>
          )}

          {/* STEP 2: Geographic & Currency Exposure */}
          {step === 2 && (
            <div className="space-y-4">
              <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-400">
                <Globe className="w-4 h-4 text-blue-600" />
                <span>Geographic Footprint & Currencies</span>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-2">
                  Operating & Distribution Regions (select all that apply)
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {taxonomies?.geographic_regions.map(reg => {
                    const selected = regions.includes(reg);
                    return (
                      <button
                        type="button"
                        key={reg}
                        onClick={() => toggleArrayItem(regions, reg, setRegions)}
                        className={`p-3 rounded-xl border text-left text-xs font-bold flex items-center justify-between transition-all ${
                          selected
                            ? 'bg-blue-50 border-blue-400 text-blue-900 shadow-xs'
                            : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                        }`}
                      >
                        <span>{reg}</span>
                        {selected && <Check className="w-4 h-4 text-blue-600 shrink-0" />}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-2">
                  Treasury & Operating Currencies
                </label>
                <div className="flex flex-wrap gap-2">
                  {taxonomies?.supported_currencies.map(curr => {
                    const selected = currencies.includes(curr);
                    return (
                      <button
                        type="button"
                        key={curr}
                        onClick={() => toggleArrayItem(currencies, curr, setCurrencies)}
                        className={`px-3 py-1.5 rounded-lg border text-xs font-mono font-bold transition-all ${
                          selected
                            ? 'bg-indigo-600 border-indigo-600 text-white'
                            : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                        }`}
                      >
                        {curr}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: Macroeconomic Risk Sensitivities */}
          {step === 3 && (
            <div className="space-y-4">
              <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-400">
                <TrendingUp className="w-4 h-4 text-blue-600" />
                <span>External Macroeconomic Sensitivities</span>
              </div>
              <p className="text-xs text-slate-500 m-0">
                Which external market shifts directly threaten your revenue, margins, or operations?
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-h-72 overflow-y-auto pr-1">
                {taxonomies?.macro_sensitivities.map(ms => {
                  const selected = sensitivities.includes(ms.id);
                  return (
                    <button
                      type="button"
                      key={ms.id}
                      onClick={() => toggleArrayItem(sensitivities, ms.id, setSensitivities)}
                      className={`p-3 rounded-2xl border text-left transition-all ${
                        selected
                          ? 'bg-blue-50/80 border-blue-400 shadow-xs'
                          : 'bg-white border-slate-200/90 hover:border-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className={`text-xs font-bold ${selected ? 'text-blue-900' : 'text-slate-800'}`}>
                          {ms.label}
                        </span>
                        {selected && <Check className="w-4 h-4 text-blue-600 shrink-0" />}
                      </div>
                      <p className="text-[11px] text-slate-500 line-clamp-2 m-0">
                        {ms.description}
                      </p>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* STEP 4: Strategic Objectives & Competitor Watchlist */}
          {step === 4 && (
            <div className="space-y-4">
              <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-400">
                <ShieldCheck className="w-4 h-4 text-blue-600" />
                <span>Competitor Watchlist & Priority KPIs</span>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Key Competitors (comma separated)
                </label>
                <input
                  type="text"
                  value={competitorsText}
                  onChange={(e) => setCompetitorsText(e.target.value)}
                  placeholder="e.g. Amazon, Maersk, DHL, Target"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-2">
                  Priority KPIs to Guard Against Shocks
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {taxonomies?.standard_kpis.map(kpi => {
                    const selected = kpis.includes(kpi.id);
                    return (
                      <button
                        type="button"
                        key={kpi.id}
                        onClick={() => toggleArrayItem(kpis, kpi.id, setKpis)}
                        className={`p-2.5 rounded-xl border text-left text-xs font-bold flex items-center justify-between transition-all ${
                          selected
                            ? 'bg-emerald-50 border-emerald-400 text-emerald-900'
                            : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300'
                        }`}
                      >
                        <span className="truncate">{kpi.label}</span>
                        {selected && <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0" />}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Corporate Risk Appetite
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: 'conservative', label: 'Conservative', desc: 'Prioritize margin safety' },
                    { id: 'moderate', label: 'Moderate', desc: 'Balanced growth & risk' },
                    { id: 'aggressive', label: 'Aggressive', desc: 'Maximize volume growth' }
                  ].map(ra => (
                    <button
                      type="button"
                      key={ra.id}
                      onClick={() => setRiskTolerance(ra.id)}
                      className={`p-2.5 rounded-xl border text-center transition-all ${
                        riskTolerance === ra.id
                          ? 'bg-slate-900 text-white border-slate-900 font-bold'
                          : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100 text-xs font-medium'
                      }`}
                    >
                      <div className="text-xs">{ra.label}</div>
                      <div className="text-[9px] opacity-75 mt-0.5">{ra.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Navigation */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200/80 flex items-center justify-between">
          {step > 1 ? (
            <button
              type="button"
              onClick={() => setStep(step - 1)}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-bold text-slate-600 hover:text-slate-900 hover:bg-slate-200/60 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Previous</span>
            </button>
          ) : (
            <div />
          )}

          {step < 4 ? (
            <button
              type="button"
              onClick={() => {
                if (step === 1 && !orgName.trim()) {
                  setErrorMsg('Organization name is required.');
                  return;
                }
                setErrorMsg(null);
                setStep(step + 1);
              }}
              className="flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition-colors"
            >
              <span>Continue</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={loading}
              className="flex items-center space-x-1.5 px-5 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-md shadow-emerald-600/20 transition-all disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              <span>{loading ? 'Activating DNA...' : 'Save Corporate Profile'}</span>
            </button>
          )}
        </div>

      </div>
    </div>
  );
};
