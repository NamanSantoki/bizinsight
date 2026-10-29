import React, { useState } from 'react';
import { ShieldCheck, Lock, User, Key, AlertCircle, X } from 'lucide-react';
import { apiClient } from '../../services/api';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (user: any) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onLoginSuccess }) => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('AdminPass2026!');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const res = await apiClient.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      if (res.data.access_token) {
        localStorage.setItem('bizinsight_token', res.data.access_token);
        localStorage.setItem('bizinsight_user', JSON.stringify(res.data.user));
        onLoginSuccess(res.data.user);
        onClose();
      }
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Invalid username or password. Please verify credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const setDemoRole = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
    setErrorMessage(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
      <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-5 bg-gradient-to-r from-blue-600 to-indigo-700 text-white flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-white/10 backdrop-blur-md flex items-center justify-center border border-white/20">
              <Lock className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Enterprise Authentication</h3>
              <p className="text-xs text-blue-100/80">Zero-Trust Role-Based Access Control</p>
            </div>
          </div>
          <button onClick={onClose} className="text-white/70 hover:text-white p-1 rounded-full hover:bg-white/10 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleLogin} className="p-6 space-y-4">
          {errorMessage && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-start space-x-2.5 text-xs text-rose-800">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700">Username / Identity</label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. admin or analyst"
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700">Secure Password</label>
            <div className="relative">
              <Key className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Quick Demo Credentials */}
          <div className="pt-2">
            <div className="text-[11px] font-medium text-slate-400 mb-1.5">Preset Credentials:</div>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setDemoRole('admin', 'AdminPass2026!')}
                className="p-2 bg-slate-100 hover:bg-blue-50 border border-slate-200 hover:border-blue-200 rounded-xl text-left transition-colors"
              >
                <div className="text-xs font-bold text-slate-800">Administrator</div>
                <div className="text-[10px] text-slate-500 font-mono">admin : AdminPass2026!</div>
              </button>
              <button
                type="button"
                onClick={() => setDemoRole('analyst', 'AnalystPass2026!')}
                className="p-2 bg-slate-100 hover:bg-blue-50 border border-slate-200 hover:border-blue-200 rounded-xl text-left transition-colors"
              >
                <div className="text-xs font-bold text-slate-800">Analyst</div>
                <div className="text-[10px] text-slate-500 font-mono">analyst : AnalystPass2026!</div>
              </button>
            </div>
          </div>

          <div className="pt-3">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-md shadow-blue-500/20 transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              {isLoading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>Authenticate & Authorize</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
