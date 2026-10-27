import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Dataset {
  id: number;
  name: string;
  description?: string;
  source_type: string;
  row_count: number;
  column_count: number;
  storage_table_name?: string;
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
    timestamp?: string;
    anomaly_score: number;
    severity: string;
    top_affected_fields: string[];
    explanation: string;
    record_payload: any;
  }>;
}

export interface SegmentationResponse {
  status: string;
  message?: string;
  methodology?: string;
  total_unique_customers?: number;
  cluster_count?: number;
  segments?: Array<{
    cluster_id: number;
    segment_label: string;
    customer_count: number;
    percentage: number;
    median_recency_days: number;
    median_frequency: number;
    median_monetary: number;
    total_cluster_revenue: number;
  }>;
  sample_assignments?: Array<any>;
  disclaimer?: string;
}

export interface AskDataResponse {
  question: string;
  sql_query?: string;
  results?: any[];
  row_count: number;
  answer: string;
  sources_used: string[];
  confidence_explanation: string;
  execution_time_ms: number;
}
