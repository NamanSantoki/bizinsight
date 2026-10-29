import axios from 'axios';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Automatic JWT Bearer token interceptor
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('bizinsight_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

// Response interceptor for session expiration handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      console.warn('Authentication token invalid or expired.');
    }
    return Promise.reject(error);
  }
);

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
}

export interface Dataset {
  id: number;
  name: string;
  description?: string;
  source_type: string;
  row_count: number;
  column_count: number;
  storage_table_name?: string;
  file_hash?: string;
  schema_metadata?: any;
  created_at: string;
  updated_at: string;
}

export interface DataQualityReport {
  id: number;
  dataset_id: number;
  quality_score: number;
  formula_description: string;
  summary: {
    total_rows: number;
    total_columns: number;
    duplicate_rows: number;
    duplicate_pct: number;
    null_cells: number;
    null_pct: number;
    total_issues_found: number;
    quality_rating: string;
  };
  column_issues: Array<{
    column?: string;
    severity: string;
    issue_type: string;
    message: string;
  }>;
  passed: boolean;
  created_at: string;
}

export interface KPIResult {
  dataset_rows: number;
  available_columns: string[];
  primary_metric?: string;
  quantity_metric?: string;
  date_metric?: string;
  cards: Record<string, { label: string; value: number; formatted: string }>;
  trends: Array<{ period: string; value: number; count: number }>;
  breakdowns: {
    products?: Array<{ name: string; value: number }>;
    regions?: Array<{ name: string; value: number }>;
    categories?: Array<{ name: string; value: number }>;
  };
}

export interface ForecastResponse {
  status: string;
  message?: string;
  best_model?: string;
  validation_strategy?: string;
  train_period?: string;
  test_period?: string;
  model_comparison?: Array<{
    model: string;
    mae: number;
    rmse: number;
    mape: number;
    r2: number;
    improvement_vs_baseline_pct: number;
  }>;
  selected_model_metrics?: any;
  future_predictions?: Array<{
    step: number;
    date: string;
    forecast: number;
    lower_bound: number;
    upper_bound: number;
    is_estimate: boolean;
  }>;
  uncertainty_note?: string;
}

export interface AnomalyResponse {
  status: string;
  message?: string;
  total_records_evaluated: number;
  features_used: string[];
  anomalies_detected_count: number;
  anomaly_percentage: number;
  contamination_threshold: number;
  top_anomalies: Array<{
    record_index: number;
    timestamp?: string | null;
    anomaly_score: number;
    severity: string;
    top_affected_fields?: string[];
    affected_fields?: string[];
    field_deviations?: any[];
    explanation: string;
    record_payload: Record<string, any>;
  }>;
  distribution?: {
    normal_count: number;
    anomaly_count: number;
  };
}

export interface SegmentationResponse {
  status: string;
  message?: string;
  methodology?: string;
  disclaimer?: string;
  total_unique_customers?: number;
  cluster_count?: number;
  segments: Array<{
    cluster_id: number;
    segment_label: string;
    customer_count: number;
    percentage?: number;
    customer_percentage?: number;
    median_recency_days?: number;
    median_frequency?: number;
    median_monetary?: number;
    total_cluster_revenue?: number;
    characteristics?: {
      avg_recency: number;
      avg_frequency: number;
      avg_monetary: number;
    };
    recommended_strategy?: string;
  }>;
}

export interface AskDataResponse {
  question: string;
  sql_query?: string;
  results?: Array<Record<string, any>>;
  row_count: number;
  answer: string;
  sources_used: string[];
  confidence_explanation: string;
  execution_time_ms: number;
}

export interface CausalResponse {
  status: string;
  message?: string;
  target_metric: string;
  intervention_driver?: string;
  available_drivers?: string[];
  sample_size?: number;
  metrics?: {
    elasticity: number;
    elasticity_interpretation: string;
    marginal_effect_slope: number;
    slope_ci_95: [number, number];
    r_squared: number;
    p_value: number;
    statistically_significant: boolean;
    [key: string]: any;
  };
  counterfactual_simulation?: {
    intervention_scenario: string;
    baseline_mean_target: number;
    simulated_target: number;
    estimated_impact: number;
    impact_range_95: [number, number];
    [key: string]: any;
  };
  simulation_curve?: Array<{
    driver_val: number;
    expected_target: number;
    upper_bound: number;
    lower_bound: number;
    [key: string]: any;
  }>;
  methodological_caveat?: string;
}

export interface StressAuditResponse {
  status: string;
  message?: string;
  total_records?: number;
  sample_split?: string;
  feature_drift_analysis?: Array<{
    column: string;
    type: string;
    ks_statistic: number;
    p_value: number;
    mean_shift_pct: number;
    skewness: number;
    kurtosis: number;
    tail_risk: string;
    drift_status: string;
    [key: string]: any;
  }>;
  stress_shocks?: Array<{
    column: string;
    current_median: number;
    shock_down_20pct: number;
    shock_up_20pct: number;
    tail_value_at_risk_5pct: number;
    tail_upside_95pct: number;
    [key: string]: any;
  }>;
  categorical_entropy_diversity?: Array<{
    column: string;
    shannon_entropy_bits: number;
    diversity_ratio: number;
    status: string;
    [key: string]: any;
  }>;
  overall_stability_verdict: string;
}

export interface ShapExplainResponse {
  status: string;
  message?: string;
  target_column: string;
  sample_size: number;
  total_records: number;
  expected_base_value: number;
  record_index: number;
  predicted_value: number;
  actual_value?: number;
  global_importance: Array<{
    feature: string;
    mean_abs_shap: number;
    relative_importance_pct: number;
  }>;
  local_contributions: Array<{
    feature: string;
    feature_value: any;
    shap_value: number;
    direction: 'positive' | 'negative';
    abs_impact: number;
  }>;
  available_records_count: number;
  algorithm: string;
}

export interface GoalSeekResponse {
  status: string;
  message?: string;
  target_metric: string;
  baseline_metric_value: number;
  target_goal_value: number;
  achieved_prediction: number;
  target_gap_pct: number;
  feasibility_verdict: string;
  optimization_success: boolean;
  iterations_used: number;
  available_candidate_levers: string[];
  active_levers: string[];
  recommendations: Array<{
    lever: string;
    baseline_value: number;
    recommended_value: number;
    absolute_change: number;
    percentage_change: number;
    min_bound: number;
    max_bound: number;
  }>;
  mathematical_model: string;
}

// Enterprise Platform 2.0 Types
export interface DataSourceItem {
  id: string;
  name: string;
  type: string;
  connection_url_masked: string;
  status: string;
  last_sync: string;
  rows_count: number;
  quality_score: number;
  last_error?: string;
}

export interface QualityGateSummary {
  dataset_id: number;
  dataset_name: string;
  final_gate_verdict: 'PUBLISHED' | 'QUARANTINED';
  quality_score_summary: {
    overall_score: number;
    gate_status: string;
    gate_passed: boolean;
    threshold: number;
    dimensions: {
      completeness: number;
      validity: number;
      uniqueness: number;
      consistency: number;
      freshness: number;
      distribution: number;
    };
    field_completeness: Record<string, number>;
    summary: string;
  };
  contract_validation_summary: {
    dataset: string;
    status: string;
    schema_compatible: boolean;
    required_fields_present: boolean;
    data_types_valid: boolean;
    invalid_records_pct: number;
    invalid_revenue_values_pct: number;
    duplicate_keys_count: number;
    total_records: number;
    quarantined_count: number;
    violations_summary: string[];
  };
}

export interface LineageNodeData {
  id: string;
  name: string;
  layer: string;
  source: string;
  transformation: string;
  last_updated: string;
  records: number;
  quality_score: number;
  upstream_datasets: string[];
  downstream_consumers: string[];
  owner: string;
}

export interface LineageGraphData {
  nodes: LineageNodeData[];
  edges: Array<{ from: string; to: string }>;
}

export interface SemanticMetricItem {
  id: string;
  name: string;
  formula: string;
  sql_expression: string;
  category: string;
  unit: string;
  description: string;
  dimensions: string[];
  owner: string;
}

export interface ModelRegistryItem {
  name: string;
  current_production_version: string;
  latest_version: string;
  algorithm: string;
  total_versions: number;
  production_details: {
    model_id: string;
    name: string;
    version: string;
    algorithm: string;
    dataset: string;
    features_count: number;
    training_period: string;
    mae: number;
    rmse: number;
    accuracy_score: number;
    status: string;
    created_at: string;
    owner: string;
  };
  versions: Array<any>;
}

export interface MLMonitoringItem {
  model_id: string;
  model_name: string;
  prediction_volume: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  error_rate_pct: number;
  data_drift_pct: number;
  prediction_drift_pct: number;
  feature_drift_pct: number;
  performance_delta_pct: number;
  drift_status: string;
  top_drifting_features: Array<{ feature: string; drift_score: number; alert: boolean }>;
  retraining_recommendation: { is_candidate: boolean; reason: string; priority: string };
  last_checked: string;
}

export interface DigitalTwinResponse {
  baseline: {
    revenue_cr: number;
    margin_pct: number;
    customers_count: number;
    marketing_budget_cr: number;
  };
  inputs: {
    marketing_delta_pct: number;
    price_delta_pct: number;
    sales_staff_delta_pct: number;
  };
  projected: {
    revenue_cr: number;
    margin_pct: number;
    customers_count: number;
    confidence_score: number;
    prediction_interval_80: [number, number];
    revenue_delta_cr: number;
    margin_delta_pts: number;
    customer_delta: number;
  };
  methodology: string;
  evidence: string[];
}

export interface PrescriptiveResponse {
  feasible: boolean;
  feasibility_score: number;
  target: {
    revenue_cr: number;
    min_margin_pct: number;
    max_marketing_budget_cr: number;
  };
  recommended_strategy: {
    marketing_spend_delta: string;
    price_optimization_delta: string;
    sales_capacity_delta: string;
  };
  expected_outcome: {
    revenue_cr: number;
    margin_pct: number;
    marketing_spend_cr: number;
  };
  governance_note: string;
}

export interface CausalRigorResponse {
  treatment: string;
  outcome: string;
  confounders: string[];
  sample_size: {
    treated_units: number;
    control_units: number;
    matched_pairs: number;
  };
  causal_effect: {
    average_treatment_effect_ate: number;
    unit: string;
    standard_error: number;
    confidence_interval_95: [number, number];
    p_value: number;
    statistically_significant: boolean;
  };
  covariate_balance: Array<{
    variable: string;
    raw_smd: number;
    matched_smd: number;
    balanced: boolean;
  }>;
  refutation_tests: Record<string, any>;
  assumptions_checklist: Array<{ assumption: string; verified: boolean; evidence: string }>;
  methodology: string;
  epistemic_disclaimer: string;
}

export interface ClassificationSummary {
  columns: Array<{
    column: string;
    tier: string;
    color: string;
    tag: string;
    reason: string;
  }>;
  summary_counts: {
    highly_sensitive: number;
    confidential: number;
    internal: number;
    public: number;
    total_columns: number;
  };
}

export interface ApprovalRequestItem {
  id: string;
  action: string;
  resource: string;
  requested_by: string;
  requested_at: string;
  reason: string;
  metadata: Record<string, any>;
  status: string;
  reviewer?: string;
  reviewed_at?: string;
  decision_note?: string;
}

export interface OperationsCenterData {
  overall_system_status: string;
  services: Array<{ service: string; status: string; latency_ms: number; uptime: string }>;
  active_incidents: Array<{
    id: string;
    title: string;
    severity: string;
    status: string;
    started_at: string;
    impact: string;
    root_cause: string;
    owner: string;
    remediation: string;
  }>;
  incident_count: number;
  last_evaluated: string;
}

export interface TelemetryData {
  traffic: {
    requests_total_24h: number;
    current_throughput_rps: number;
    error_rate_pct: number;
    active_websockets: number;
  };
  latency: {
    p50_ms: number;
    p95_ms: number;
    p99_ms: number;
    avg_db_query_ms: number;
  };
  infrastructure: {
    cpu_utilization_pct: number;
    memory_utilization_pct: number;
    disk_usage_pct: number;
  };
  timestamp: string;
}

export interface CostData {
  billing_cycle: string;
  currency: string;
  total_spend: number;
  breakdown_by_category: Array<{ category: string; cost: number; pct: number }>;
  breakdown_by_tenant: Array<{ tenant: string; spend: number; status: string }>;
  cost_efficiency_rating: string;
}

export interface CompanyProfile {
  id?: number;
  organization_name: string;
  industry_sector: string;
  business_model: string;
  annual_revenue_bracket?: string;
  operating_currencies: string[];
  geographic_regions: string[];
  key_macro_sensitivities: string[];
  key_competitors: string[];
  monitored_kpis: string[];
  risk_tolerance: string;
  created_at?: string;
  updated_at?: string;
}

export interface TaxonomyItem {
  id: string;
  label: string;
  description: string;
}

export interface TaxonomyData {
  sectors: TaxonomyItem[];
  business_models: string[];
  macro_sensitivities: TaxonomyItem[];
  standard_kpis: TaxonomyItem[];
  supported_currencies: string[];
  geographic_regions: string[];
}
