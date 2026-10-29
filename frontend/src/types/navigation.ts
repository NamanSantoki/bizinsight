import { 
  BarChart3, ShieldCheck, TrendingUp, Users, 
  FileText, Activity, AlertTriangle, GitFork,
  Sparkles, Target, Terminal, Database, GitBranch,
  Layers, Sliders, Cpu, Lock, Radio
} from 'lucide-react';

export type TabType = 
  | 'overview' 
  | 'quality'
  | 'analytics' 
  | 'data_sources'
  | 'contracts_gates'
  | 'lineage'
  | 'metrics_store'
  | 'forecasting' 
  | 'anomalies' 
  | 'segmentation' 
  | 'causal' 
  | 'market_radar'
  | 'stress_drift'
  | 'digital_twin'
  | 'goal_seek' 
  | 'shap_explain' 
  | 'ask_data' 
  | 'mlops_registry'
  | 'governance_abac'
  | 'audit'
  | 'operations_center';

export interface TabItem {
  id: TabType;
  label: string;
  icon: any;
  color: string;
  badge?: string;
  section: 'Analytics' | 'Data Platform' | 'AI & ML' | 'Decision Intelligence' | 'Governance' | 'Operations';
}

export const TAB_CONFIG: TabItem[] = [
  // Analytics
  { id: 'overview', label: 'Executive Dashboard', icon: BarChart3, color: '#2563eb', badge: 'Core', section: 'Analytics' },
  { id: 'analytics', label: 'Exploratory Analytics', icon: TrendingUp, color: '#0284c7', section: 'Analytics' },

  // Data Platform
  { id: 'data_sources', label: 'Data Sources (Connectors)', icon: Database, color: '#0891b2', badge: 'Multi-Src', section: 'Data Platform' },
  { id: 'contracts_gates', label: 'Contracts & Quality Gates', icon: ShieldCheck, color: '#10b981', badge: '6-Dim', section: 'Data Platform' },
  { id: 'lineage', label: 'Full Data Lineage DAG', icon: GitBranch, color: '#059669', badge: 'Lakehouse', section: 'Data Platform' },
  { id: 'metrics_store', label: 'Semantic Metrics Store', icon: Layers, color: '#6366f1', badge: 'Governed', section: 'Data Platform' },

  // AI & ML
  { id: 'ask_data', label: 'Governed AI Analyst (NLQ)', icon: Terminal, color: '#4f46e5', badge: 'AST Verified', section: 'AI & ML' },
  { id: 'mlops_registry', label: 'MLOps Registry & Drift', icon: Cpu, color: '#7c3aed', badge: 'v1..v7', section: 'AI & ML' },
  { id: 'shap_explain', label: 'SHAP Explainability (XAI)', icon: Sparkles, color: '#059669', badge: 'TreeSHAP', section: 'AI & ML' },
  { id: 'forecasting', label: 'Time-Series Forecast', icon: Activity, color: '#7c3aed', badge: 'Quantile', section: 'AI & ML' },
  { id: 'anomalies', label: 'Anomaly Detection', icon: AlertTriangle, color: '#e11d48', badge: 'IsoForest', section: 'AI & ML' },
  { id: 'segmentation', label: 'Customer Segments', icon: Users, color: '#d97706', badge: 'RFM', section: 'AI & ML' },

  // Decision Intelligence
  { id: 'market_radar', label: 'Autonomous Market Radar', icon: Radio, color: '#f59e0b', badge: 'Causal AI', section: 'Decision Intelligence' },
  { id: 'digital_twin', label: 'Digital Twin Scenario Sim', icon: Sliders, color: '#ec4899', badge: 'What-If', section: 'Decision Intelligence' },
  { id: 'goal_seek', label: 'Prescriptive Goal-Seek', icon: Target, color: '#ea580c', badge: 'Convex', section: 'Decision Intelligence' },
  { id: 'causal', label: 'Econometric Causal Engine', icon: GitFork, color: '#db2777', badge: 'DML / IPW', section: 'Decision Intelligence' },

  // Governance & Security
  { id: 'governance_abac', label: 'ABAC & PII Masking', icon: Lock, color: '#b45309', badge: 'RLS / CLS', section: 'Governance' },
  { id: 'audit', label: 'Cryptographic Audit Trail', icon: FileText, color: '#475569', badge: 'SHA-256', section: 'Governance' },

  // Operations Center
  { id: 'operations_center', label: 'Operations & Telemetry', icon: Radio, color: '#0284c7', badge: 'Live Ops', section: 'Operations' },
];
