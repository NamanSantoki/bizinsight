from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: str
    role: str = "analyst"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    username: str
    password: str

class AuditLogCreate(BaseModel):
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    username: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    prev_hash: Optional[str] = None
    record_hash: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DatasetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    source_type: str
    row_count: int
    column_count: int
    storage_table_name: Optional[str] = None
    file_hash: Optional[str] = None
    schema_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DataQualityReportResponse(BaseModel):
    id: int
    dataset_id: int
    quality_score: float
    formula_description: str
    summary: Dict[str, Any]
    column_issues: List[Dict[str, Any]]
    passed: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CleaningRequest(BaseModel):
    remove_duplicates: bool = True
    missing_strategy: str = "none" # "none", "drop", "median_mode", "forward_fill"
    clean_column_names: bool = True
    normalize_dates: bool = True
    date_columns: Optional[List[str]] = None
    outlier_handling: str = "none" # "none", "clip_iqr"
    numeric_columns: Optional[List[str]] = None

class ForecastRequest(BaseModel):
    date_column: str
    target_column: str
    forecast_horizon: int = 14 # number of future periods
    frequency: str = "D"       # 'D', 'W', 'M'
    model_types: Optional[List[str]] = ["Naive", "MovingAverage", "LinearRegression", "RandomForest", "XGBoost"]

class AnomalyRequest(BaseModel):
    feature_columns: Optional[List[str]] = None
    date_column: Optional[str] = None
    contamination: float = 0.05 # expected outlier fraction

class SegmentationRequest(BaseModel):
    customer_id_col: str
    date_col: str
    monetary_col: str
    n_clusters: int = 4

class AskDataRequest(BaseModel):
    question: str
    dataset_id: int

class AskDataResponse(BaseModel):
    question: str
    sql_query: Optional[str]
    results: Optional[List[Dict[str, Any]]]
    row_count: int
    answer: str
    sources_used: List[str]
    confidence_explanation: str
    execution_time_ms: float
