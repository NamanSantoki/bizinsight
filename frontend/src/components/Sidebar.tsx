import React from 'react';
import { Zap, X } from 'lucide-react';
import { TAB_CONFIG } from '../types/navigation';
import type { TabType } from '../types/navigation';

interface SidebarProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  activeTab, 
  onTabChange, 
  isOpen = false, 
  onClose 
}) => {
  // Group tabs by section
  const sections = Array.from(new Set(TAB_CONFIG.map(t => t.section)));

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs z-40 lg:hidden transition-opacity"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Drawer */}
      <aside 
        className={`fixed inset-y-0 left-0 z-50 w-72 flex flex-col justify-between shrink-0 bg-slate-900 border-r border-slate-800 text-slate-300 shadow-2xl lg:shadow-xl lg:static lg:translate-x-0 transition-transform duration-200 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex flex-col h-full overflow-hidden">
          {/* Brand & Logo Header */}
          <div className="px-5 py-4 flex items-center justify-between border-b border-slate-800 bg-slate-950/40">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/30 text-white shrink-0">
                <Zap className="w-5 h-5 fill-current" />
              </div>
              <div>
                <div className="flex items-center space-x-1.5">
                  <h1 className="text-sm font-black tracking-wider text-white m-0">BIZINSIGHT</h1>
                  <span className="text-[9px] font-black px-1.5 py-0.5 bg-blue-500/20 text-blue-400 rounded border border-blue-500/40 tracking-widest">2.0 ENT</span>
                </div>
                <p className="text-[10px] font-medium text-slate-400 m-0">Enterprise Data & Decision Platform</p>
              </div>
            </div>

            {/* Mobile Close Button */}
            {onClose && (
              <button
                onClick={onClose}
                className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                title="Close Sidebar"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>

          {/* Navigation Sections */}
          <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-4 scrollbar-thin scrollbar-thumb-slate-700">
            {sections.map((secName) => {
              const sectionTabs = TAB_CONFIG.filter(t => t.section === secName);
              return (
                <div key={secName} className="space-y-1">
                  <div className="px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    {secName}
                  </div>
                  {sectionTabs.map((t) => {
                    const Icon = t.icon;
                    const isActive = activeTab === t.id;
                    return (
                      <button
                        key={t.id}
                        onClick={() => {
                          onTabChange(t.id);
                          if (onClose) onClose();
                        }}
                        className={`w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-xs font-medium transition-all group ${
                          isActive
                            ? 'bg-blue-600 text-white font-semibold shadow-md shadow-blue-600/30'
                            : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
                        }`}
                      >
                        <div className="flex items-center space-x-2.5 truncate">
                          <div
                            className={`p-1 rounded-md transition-colors shrink-0 ${
                              isActive ? 'bg-blue-700 text-white' : 'text-slate-400 group-hover:text-blue-400'
                            }`}
                          >
                            <Icon className="w-3.5 h-3.5" />
                          </div>
                          <span className="truncate">{t.label}</span>
                        </div>
                        {t.badge && (
                          <span
                            className={`text-[8px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider shrink-0 ml-1.5 ${
                              isActive
                                ? 'bg-blue-700 text-blue-100'
                                : 'bg-slate-800 text-slate-400 group-hover:bg-slate-700 group-hover:text-slate-200'
                            }`}
                          >
                            {t.badge}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              );
            })}
          </nav>

          {/* Footer Info */}
          <div className="p-3 border-t border-slate-800 bg-slate-950/40 text-[10px] text-slate-400 flex items-center justify-between shrink-0">
            <span className="flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Cluster: Ready</span>
            </span>
            <span className="font-mono text-slate-500">v2.0-enterprise</span>
          </div>
        </div>
      </aside>
    </>
  );
};
