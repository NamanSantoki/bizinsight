import React, { useState, useEffect, useCallback } from 'react';
import { 
  Database, Upload, ShieldCheck, AlertCircle, RefreshCw, 
  LogOut, Lock
} from 'lucide-react';
import type { Dataset } from '../services/api';
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
}

export const Navbar: React.FC<NavbarProps> = ({
  datasets,
  selectedDatasetId,
  onSelectDataset,
  onFileUpload,
  currentUser,
  onOpenAuth,
  onLogout
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
    <header className="h-16 shrink-0 bg-white border-b border-slate-200/90 px-6 flex items-center justify-between z-10 shadow-2xs">
      {/* Left: Active Dataset Selector */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2 bg-slate-50 border border-slate-200/80 rounded-2xl px-3 py-1.5">
          <Database className="w-4 h-4 text-blue-600 shrink-0" />
          <select
            value={selectedDatasetId || ''}
            onChange={(e) => onSelectDataset(Number(e.target.value))}
            className="bg-transparent text-xs font-bold text-slate-800 focus:outline-none cursor-pointer pr-2 max-w-xs truncate"
          >
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.row_count.toLocaleString()} rows)
              </option>
            ))}
          </select>
        </div>

        {selectedDataset && (
          <div className="hidden lg:flex items-center space-x-2 text-[11px] text-slate-400">
            <span>•</span>
            <span className="font-mono text-slate-500 font-semibold">{selectedDataset.source_type.toUpperCase()}</span>
            <span>•</span>
            <span>{selectedDataset.column_count} columns</span>
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
      <div className="flex items-center space-x-3">
        {/* Upload Button */}
        <label className="flex items-center space-x-1.5 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-bold rounded-xl border border-blue-200 cursor-pointer transition-colors">
          <Upload className="w-3.5 h-3.5" />
          <span>Ingest Dataset</span>
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
          className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-xl border text-[11px] font-semibold transition-all ${
            auditStatus?.status === 'valid'
              ? 'bg-emerald-50 text-emerald-800 border-emerald-200 hover:bg-emerald-100'
              : auditStatus?.status === 'compromised' || auditStatus?.status === 'tampered'
              ? 'bg-rose-50 text-rose-800 border-rose-300 animate-pulse'
              : 'bg-slate-50 text-slate-600 border-slate-200'
          }`}
        >
          {verifyingAudit ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-slate-500" />
          ) : auditStatus?.status === 'valid' ? (
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          ) : (
            <AlertCircle className="w-3.5 h-3.5 text-amber-500" />
          )}
          <span className="hidden sm:inline">
            {verifyingAudit ? 'Verifying Chain...' : auditStatus?.status === 'valid' ? 'Audit Chain Verified' : 'Audit Chain Check'}
          </span>
        </button>

        {/* User Identity / Role Pill */}
        {currentUser ? (
          <div className="flex items-center space-x-2 pl-2 border-l border-slate-200">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-bold text-slate-800">{currentUser.username}</div>
              <div className="text-[10px] font-semibold text-blue-600 uppercase tracking-wider">{currentUser.role}</div>
            </div>
            <button
              onClick={onLogout}
              title="Sign Out"
              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={onOpenAuth}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold rounded-xl transition-all shadow-xs"
          >
            <Lock className="w-3.5 h-3.5" />
            <span>Sign In</span>
          </button>
        )}
      </div>
    </header>
  );
};
