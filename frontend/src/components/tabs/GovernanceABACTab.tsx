import React, { useState, useEffect } from 'react';
import { Lock, CheckCircle2, XCircle, Download } from 'lucide-react';
import { apiClient } from '../../services/api';
import type { ApprovalRequestItem, ClassificationSummary } from '../../services/api';

interface GovernanceABACTabProps {
  datasetId: number | null;
}

export const GovernanceABACTab: React.FC<GovernanceABACTabProps> = ({ datasetId }) => {
  // ABAC state
  const [userRole, setUserRole] = useState<string>('analyst');
  const [userDept, setUserDept] = useState<string>('Finance');
  const [userRegion, setUserRegion] = useState<string>('Europe');
  const [resSensitivity, setResSensitivity] = useState<string>('Confidential');
  const [abacDecision, setAbacDecision] = useState<any>(null);

  // Classification & Approvals state
  const [classification, setClassification] = useState<ClassificationSummary | null>(null);
  const [approvals, setApprovals] = useState<ApprovalRequestItem[]>([]);
  const [exportMsg, setExportMsg] = useState<string | null>(null);

  const evaluateABAC = async () => {
    try {
      const res = await apiClient.post('/enterprise/governance/abac/evaluate', {
        user_role: userRole,
        user_department: userDept,
        user_region: userRegion,
        resource_department: 'Finance',
        resource_sensitivity: resSensitivity,
        action: 'read',
      });
      setAbacDecision(res.data);
    } catch (err: any) {
      console.error(err);
    }
  };

  const fetchGovernanceData = async () => {
    try {
      const [appRes] = await Promise.all([
        apiClient.get<ApprovalRequestItem[]>('/enterprise/governance/approvals'),
      ]);
      setApprovals(appRes.data);

      if (datasetId) {
        const clsRes = await apiClient.get<ClassificationSummary>(`/enterprise/governance/classification/${datasetId}`);
        setClassification(clsRes.data);
      }
    } catch (err: any) {
      console.error(err);
    }
  };

  useEffect(() => {
    evaluateABAC();
    fetchGovernanceData();
  }, [datasetId]);

  const handleReviewApproval = async (reqId: string, approve: boolean) => {
    try {
      await apiClient.post(`/enterprise/governance/approvals/${reqId}/review`, {
        approve,
        note: approve ? 'Verified dual-control security clearance.' : 'Rejected due to insufficient justification.',
      });
      fetchGovernanceData();
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleRequestExport = async () => {
    setExportMsg(null);
    try {
      const res = await apiClient.post('/enterprise/governance/export', {
        dataset_name: 'Customer Master Fact',
        classification: 'Confidential',
        contains_pii: true,
      });
      if (res.data.authorized) {
        setExportMsg(`Export authorized! Single-use download token generated (${res.data.download_token}, expires in 15 mins). PII dynamically masked: ${res.data.pii_masked ? 'YES' : 'NO'}`);
      } else {
        setExportMsg(`Export denied: ${res.data.reason}`);
      }
    } catch (err: any) {
      setExportMsg(`Export error: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-2 rounded-xl bg-amber-50 text-amber-700">
              <Lock className="w-5 h-5" />
            </span>
            <h2 className="text-lg font-bold text-slate-900 m-0">Enterprise Governance: ABAC, PII Masking & Dual Approvals</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Attribute-Based Access Control, Row/Column-level dynamic security, automated 4-tier data classification, and dual-authorization workflows.
          </p>
        </div>
      </div>

      {/* Grid: ABAC Policy Simulator & Classification */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: ABAC Policy Evaluation Simulator */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900 m-0">ABAC Policy Evaluation Engine</h3>
            <p className="text-xs text-slate-400">Dynamic evaluation across Role, Department, Region, and Data Sensitivity</p>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">User Role:</label>
              <select
                value={userRole}
                onChange={(e) => { setUserRole(e.target.value); }}
                className="w-full p-2 rounded-lg border border-slate-200 text-xs"
              >
                <option value="admin">Admin (Full Access)</option>
                <option value="analyst">Analyst</option>
                <option value="viewer">Viewer</option>
              </select>
            </div>
            <div>
              <label className="font-semibold text-slate-700 block mb-1">User Department:</label>
              <select
                value={userDept}
                onChange={(e) => { setUserDept(e.target.value); }}
                className="w-full p-2 rounded-lg border border-slate-200 text-xs"
              >
                <option value="Finance">Finance</option>
                <option value="Marketing">Marketing</option>
                <option value="Engineering">Engineering</option>
                <option value="Executive">Executive</option>
              </select>
            </div>
            <div>
              <label className="font-semibold text-slate-700 block mb-1">User Region:</label>
              <select
                value={userRegion}
                onChange={(e) => { setUserRegion(e.target.value); }}
                className="w-full p-2 rounded-lg border border-slate-200 text-xs"
              >
                <option value="Global">Global</option>
                <option value="Europe">Europe</option>
                <option value="NorthAmerica">North America</option>
                <option value="APAC">APAC</option>
              </select>
            </div>
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Resource Sensitivity:</label>
              <select
                value={resSensitivity}
                onChange={(e) => { setResSensitivity(e.target.value); }}
                className="w-full p-2 rounded-lg border border-slate-200 text-xs"
              >
                <option value="Public">Public</option>
                <option value="Internal">Internal</option>
                <option value="Confidential">Confidential</option>
                <option value="Highly Sensitive">Highly Sensitive</option>
              </select>
            </div>
          </div>

          <button
            onClick={evaluateABAC}
            className="w-full py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold transition"
          >
            Evaluate ABAC Authorization
          </button>

          {abacDecision && (
            <div className={`p-3.5 rounded-xl border text-xs ${
              abacDecision.decision === 'ALLOW' ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-rose-50 border-rose-200 text-rose-900'
            }`}>
              <div className="font-bold flex items-center space-x-1.5">
                {abacDecision.decision === 'ALLOW' ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <XCircle className="w-4 h-4 text-rose-600" />}
                <span>DECISION: {abacDecision.decision}</span>
              </div>
              <p className="mt-1 m-0 text-[11px]">{abacDecision.reason}</p>
            </div>
          )}
        </div>

        {/* Right: Automated PII Detection & Data Classification */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900 m-0">Automated Data Classification (4 Tiers)</h3>
            <p className="text-xs text-slate-400">Deep column inspection for GDPR / HIPAA compliance</p>
          </div>

          {/* Classification Cards */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-900">
              <span className="text-[10px] uppercase font-bold tracking-wider">🔴 Highly Sensitive</span>
              <p className="text-lg font-black mt-1 m-0">{classification?.summary_counts?.highly_sensitive ?? 4} columns</p>
              <span className="text-[10px] text-rose-700">SSN, Passport, Payment cards</span>
            </div>
            <div className="p-3 rounded-xl bg-orange-50 border border-orange-200 text-orange-900">
              <span className="text-[10px] uppercase font-bold tracking-wider">🟠 Confidential</span>
              <p className="text-lg font-black mt-1 m-0">{classification?.summary_counts?.confidential ?? 17} columns</p>
              <span className="text-[10px] text-orange-700">Customer email, phone, revenue</span>
            </div>
            <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-900">
              <span className="text-[10px] uppercase font-bold tracking-wider">🟡 Internal</span>
              <p className="text-lg font-black mt-1 m-0">{classification?.summary_counts?.internal ?? 32} columns</p>
              <span className="text-[10px] text-amber-700">Order ID, Status, Category</span>
            </div>
            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900">
              <span className="text-[10px] uppercase font-bold tracking-wider">🟢 Public</span>
              <p className="text-lg font-black mt-1 m-0">{classification?.summary_counts?.public ?? 8} columns</p>
              <span className="text-[10px] text-emerald-700">Country, Currency, Date</span>
            </div>
          </div>

          {/* Export Governance Trigger */}
          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-100 space-y-2 pt-3">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-slate-800">Governed Export Request Pipeline</span>
              <button
                onClick={handleRequestExport}
                className="flex items-center space-x-1 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold transition"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Request Export</span>
              </button>
            </div>
            {exportMsg && (
              <p className="text-[11px] text-slate-700 bg-white p-2 rounded border border-slate-200 m-0">
                {exportMsg}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Section: Dual-Authorization Workflows */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
        <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 m-0">Two-Person Dual Authorization Workflows</h3>
            <p className="text-xs text-slate-400">Separation of duties: Critical model deployments and PII exports require independent approval.</p>
          </div>
          <span className="text-xs font-semibold text-slate-500">
            {approvals.filter(a => a.status === 'PENDING_APPROVAL').length} Pending Review
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-100">
              <tr>
                <th className="py-2.5 px-3">Request ID</th>
                <th className="py-2.5 px-3">Action</th>
                <th className="py-2.5 px-3">Resource Target</th>
                <th className="py-2.5 px-3">Requested By</th>
                <th className="py-2.5 px-3">Justification</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">Review</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {approvals.map((req) => {
                const isPending = req.status === 'PENDING_APPROVAL';
                return (
                  <tr key={req.id} className="hover:bg-slate-50">
                    <td className="py-3 px-3 font-mono font-bold text-slate-900">{req.id}</td>
                    <td className="py-3 px-3 font-semibold text-slate-800">{req.action}</td>
                    <td className="py-3 px-3 text-slate-600">{req.resource}</td>
                    <td className="py-3 px-3 font-mono text-slate-500">{req.requested_by}</td>
                    <td className="py-3 px-3 text-slate-600 max-w-xs truncate">{req.reason}</td>
                    <td className="py-3 px-3">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                          req.status === 'APPROVED'
                            ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                            : req.status === 'REJECTED'
                            ? 'bg-rose-100 text-rose-800 border-rose-300'
                            : 'bg-amber-100 text-amber-800 border-amber-300'
                        }`}
                      >
                        {req.status}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right space-x-1.5">
                      {isPending ? (
                        <>
                          <button
                            onClick={() => handleReviewApproval(req.id, true)}
                            className="px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[11px] font-semibold transition"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleReviewApproval(req.id, false)}
                            className="px-2 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded text-[11px] font-semibold transition"
                          >
                            Reject
                          </button>
                        </>
                      ) : (
                        <span className="text-[11px] text-slate-400">Reviewed by {req.reviewer}</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
