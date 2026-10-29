import React, { useState, useEffect, useCallback } from 'react';
import { 
  Database, Upload, ShieldCheck, AlertCircle, RefreshCw, 
  LogOut, Lock, Menu, Building2, Sparkles
} from 'lucide-react';
import type { Dataset, CompanyProfile } from '../services/api';
import { apiClient } from '../services/api';

interface NavbarProps {
  datasets: Dataset[];
  selectedDatasetId: number | null;
  onSelectDataset: (id: number) => void;
  onFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  currentUser: any;
  onOpenAuth: () => void;
  onLogout: () => void;
  loading?: boolean;
  onToggleSidebar?: () => void;
  companyProfile?: CompanyProfile | null;
  onOpenCompanyDNA?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  datasets,
  selectedDatasetId,
  onSelectDataset,
  onFileUpload,
  currentUser,
  onOpenAuth,
  onLogout,
  onToggleSidebar,
  companyProfile,
  onOpenCompanyDNA
}) => {
  const [auditStatus, setAuditStatus] = useState<{ status: string; total_records?: number } | null>(null);
  const [verifyingAudit, setVerifyingAudit] = useState(false);

  const verifyAuditChain = useCallback(async () => {
    try {
      setVerifyingAudit(true);
      const res = await apiClient.get('/auth/audit/verify-chain');
      setAuditStatus(res.data);
    } catch (_err) {
      setAuditStatus({ status: 'unverified' });
    } finally {
      setVerifyingAudit(false);
    }
  }, []);

  useEffect(() => {
    verifyAuditChain();
  }, [verifyAuditChain]);

  const selectedDataset = datasets.find(d => d.id === selectedDatasetId);

  return (
    <header className="h-16 shrink-0 bg-white border-b border-slate-200/90 px-3 sm:px-6 flex items-center justify-between z-10 shadow-2xs gap-2">
      {/* Left: Mobile Sidebar Toggle + Dataset Selector */}
      <div className="flex items-center space-x-2 sm:space-x-3 min-w-0">
        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            className="lg:hidden p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors shrink-0"
            title="Toggle Navigation Menu"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        <div className="flex items-center space-x-1.5 sm:space-x-2 bg-slate-50 border border-slate-200/80 rounded-2xl px-2.5 sm:px-3 py-1.5 min-w-0">
          <Database className="w-4 h-4 text-blue-600 shrink-0" />
          <select
            value={selectedDatasetId || ''}
            onChange={(e) => onSelectDataset(Number(e.target.value))}
            className="bg-transparent text-xs font-bold text-slate-800 focus:outline-none cursor-pointer pr-1 max-w-[130px] xs:max-w-[180px] sm:max-w-xs truncate"
          >
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.row_count.toLocaleString()} rows)
              </option>
            ))}
          </select>
        </div>

        {selectedDataset && (
          <div className="hidden xl:flex items-center space-x-2 text-[11px] text-slate-400">
            <span>•</span>
            <span className="font-mono text-slate-500 font-semibold">{selectedDataset.source_type.toUpperCase()}</span>
            <span>•</span>
            <span>{selectedDataset.column_count} cols</span>
            {selectedDataset.file_hash && (
              <>
                <span>•</span>
                <span className="font-mono text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded-md border border-slate-200" title={`SHA-256 Digest: ${selectedDataset.file_hash}`}>
                  SHA-256: {selectedDataset.file_hash.substring(0, 8)}...
                </span>
              </>
            )}
          </div>
        )}
      </div>

      {/* Right Controls: Ingest Button, Audit Verification Badge, Auth Profile */}
      <div className="flex items-center space-x-1.5 sm:space-x-3 shrink-0">
        {/* Company DNA Profile Indicator */}
        {onOpenCompanyDNA && (
          <button
            onClick={onOpenCompanyDNA}
            title={companyProfile ? "Edit Enterprise DNA & Risk Profile" : "Configure Corporate DNA & Risk Sensitivities"}
            className={`hidden md:flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border text-xs font-bold transition-all shrink-0 ${
              companyProfile
                ? 'bg-slate-50 hover:bg-slate-100 border-slate-200 text-slate-800'
                : 'bg-indigo-50 hover:bg-indigo-100 border-indigo-200 text-indigo-700 animate-pulse'
            }`}
          >
            {companyProfile ? (
              <>
                <Building2 className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                <span className="truncate max-w-[140px]">{companyProfile.organization_name}</span>
                <span className="text-[10px] text-slate-400 font-normal">({companyProfile.industry_sector.split(' ')[0]})</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                <span>Setup Company DNA</span>
              </>
            )}
          </button>
        )}

        {/* Upload Button */}
        <label className="flex items-center space-x-1.5 px-2.5 sm:px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-bold rounded-xl border border-blue-200 cursor-pointer transition-colors shrink-0">
          <Upload className="w-3.5 h-3.5 shrink-0" />
          <span className="hidden sm:inline">Ingest Dataset</span>
          <span className="sm:hidden text-[11px]">Ingest</span>
          <input
            type="file"
            accept=".csv,.xlsx,.xls,.txt"
            onChange={onFileUpload}
            className="hidden"
          />
        </label>

        {/* Cryptographic Audit Chain Verification Badge */}
        <button
          onClick={verifyAuditChain}
          disabled={verifyingAudit}
          title="Click to re-verify cryptographic SHA-256 blockchain audit logs"
          className={`flex items-center space-x-1 sm:space-x-1.5 px-2 sm:px-2.5 py-1.5 rounded-xl border text-[11px] font-semibold transition-all shrink-0 ${
            auditStatus?.status === 'valid'
              ? 'bg-emerald-50 text-emerald-800 border-emerald-200 hover:bg-emerald-100'
              : auditStatus?.status === 'compromised' || auditStatus?.status === 'tampered'
              ? 'bg-rose-50 text-rose-800 border-rose-300 animate-pulse'
              : 'bg-slate-50 text-slate-600 border-slate-200'
          }`}
        >
          {verifyingAudit ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-slate-500 shrink-0" />
          ) : auditStatus?.status === 'valid' ? (
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
          ) : (
            <AlertCircle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
          )}
          <span className="hidden md:inline">
            {verifyingAudit ? 'Verifying Chain...' : auditStatus?.status === 'valid' ? 'Audit Verified' : 'Audit Check'}
          </span>
        </button>

        {/* User Identity / Role Pill */}
        {currentUser ? (
          <div className="flex items-center space-x-1.5 sm:space-x-2 pl-1 sm:pl-2 border-l border-slate-200 shrink-0">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-bold text-slate-800 leading-tight">{currentUser.username}</div>
              <div className="text-[10px] font-semibold text-blue-600 uppercase tracking-wider">{currentUser.role}</div>
            </div>
            <button
              onClick={onLogout}
              title="Sign Out"
              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors shrink-0"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={onOpenAuth}
            className="flex items-center space-x-1.5 px-2.5 sm:px-3 py-1.5 bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold rounded-xl transition-all shadow-xs shrink-0"
          >
            <Lock className="w-3.5 h-3.5" />
            <span className="hidden xs:inline">Sign In</span>
          </button>
        )}
      </div>
    </header>
  );
};
