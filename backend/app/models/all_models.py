import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum, JSON
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.ANALYST.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    datasets = relationship("Dataset", back_populates="owner")
    audit_logs = relationship("AuditLog", back_populates="user")

class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)  # csv, excel, postgres, api
    connection_config = Column(JSON, nullable=True)   # for api or postgres
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=utc_now)

    datasets = relationship("Dataset", back_populates="data_source")

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source_type = Column(String(50), nullable=False)  # csv, excel, postgres, api
    raw_file_path = Column(String(500), nullable=False)
    processed_file_path = Column(String(500), nullable=True)
    storage_table_name = Column(String(100), nullable=True) # for dynamic SQL queries
    file_hash = Column(String(64), nullable=True)           # SHA-256 raw file digest
    
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    schema_metadata = Column(JSON, nullable=True)
    
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    owner = relationship("User", back_populates="datasets")
    data_source = relationship("DataSource", back_populates="datasets")
    quality_reports = relationship("DataQualityReport", back_populates="dataset", cascade="all, delete-orphan")
    model_runs = relationship("ModelRun", back_populates="dataset", cascade="all, delete-orphan")
    anomalies = relationship("AnomalyRecord", back_populates="dataset", cascade="all, delete-orphan")
    segments = relationship("CustomerSegmentRecord", back_populates="dataset", cascade="all, delete-orphan")

class DataQualityReport(Base):
    __tablename__ = "data_quality_reports"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    quality_score = Column(Float, nullable=False)
    formula_description = Column(Text, nullable=False)
    summary = Column(JSON, nullable=False)       # missing %, duplicates, invalid counts
    column_issues = Column(JSON, nullable=False) # list of column-level errors/warnings
    passed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    dataset = relationship("Dataset", back_populates="quality_reports")

class ModelRun(Base):
    __tablename__ = "model_runs"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    model_type = Column(String(100), nullable=False) # forecasting, anomaly, segmentation
    algorithm = Column(String(100), nullable=False)  # LinearRegression, XGBoost, ARIMA, IsolationForest, KMeans
    target_column = Column(String(100), nullable=True)
    date_column = Column(String(100), nullable=True)
    feature_columns = Column(JSON, nullable=True)
    hyperparameters = Column(JSON, nullable=True)
    
    # Validation strategy
    validation_strategy = Column(String(100), nullable=True) # chronological_train_test_split
    train_start = Column(DateTime, nullable=True)
    train_end = Column(DateTime, nullable=True)
    test_start = Column(DateTime, nullable=True)
    test_end = Column(DateTime, nullable=True)

    metrics = Column(JSON, nullable=False) # mae, rmse, mape, baseline_mae, improvement_pct
    model_path = Column(String(500), nullable=True)
    predictions_payload = Column(JSON, nullable=True) # forecasts with upper/lower bounds
    feature_importance = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    dataset = relationship("Dataset", back_populates="model_runs")

class AnomalyRecord(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    record_index = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=True)
    anomaly_score = Column(Float, nullable=False)
    severity = Column(String(50), default="high") # high, medium, low
    affected_fields = Column(JSON, nullable=False)
    record_payload = Column(JSON, nullable=False)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    dataset = relationship("Dataset", back_populates="anomalies")

class CustomerSegmentRecord(Base):
    __tablename__ = "customer_segments"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    cluster_id = Column(Integer, nullable=False)
    segment_label = Column(String(100), nullable=False) # e.g. "High Value, High Frequency"
    customer_count = Column(Integer, nullable=False)
    characteristics = Column(JSON, nullable=False) # avg recency, avg frequency, avg monetary
    created_at = Column(DateTime, default=utc_now)

    dataset = relationship("Dataset", back_populates="segments")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False) # login, upload, cleaning, forecast, query, etc.
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(100), nullable=True)
    prev_hash = Column(String(64), nullable=True)    # Cryptographic block linkage
    record_hash = Column(String(64), nullable=True)  # SHA-256 digest of this block
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="audit_logs")

class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(Integer, primary_key=True, index=True)
    organization_name = Column(String(255), nullable=False)
    industry_sector = Column(String(100), nullable=False)
    business_model = Column(String(100), nullable=False)
    annual_revenue_bracket = Column(String(50), nullable=True)
    operating_currencies = Column(JSON, nullable=False, default=list)
    geographic_regions = Column(JSON, nullable=False, default=list)
    key_macro_sensitivities = Column(JSON, nullable=False, default=list)
    key_competitors = Column(JSON, nullable=False, default=list)
    monitored_kpis = Column(JSON, nullable=False, default=list)
    risk_tolerance = Column(String(50), default="moderate")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    assessments = relationship("CausalImpactAssessment", back_populates="company")

class MarketSignalEvent(Base):
    __tablename__ = "market_signals"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(String(100), unique=True, index=True, nullable=False)
    source = Column(String(100), nullable=False) # e.g. FRED, EIA_CRUDE, BALTIC_FREIGHT, BLS_CPI
    factor_key = Column(String(100), index=True, nullable=False) # crude_oil, freight_rates, interest_rates, etc.
    headline = Column(String(255), nullable=False)
    event_summary = Column(Text, nullable=False)
    magnitude_pct = Column(Float, nullable=False) # e.g. +7.4%
    shock_direction = Column(String(50), nullable=False) # surge, drop, volatility_spike
    confidence_score = Column(Float, default=0.92, nullable=False)
    raw_indicators = Column(JSON, nullable=True) # Underlying telemetry metrics
    detected_at = Column(DateTime, default=utc_now, nullable=False)

    assessments = relationship("CausalImpactAssessment", back_populates="signal", cascade="all, delete-orphan")

class CausalImpactAssessment(Base):
    __tablename__ = "causal_impact_assessments"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("market_signals.id"), nullable=False)
    company_profile_id = Column(Integer, ForeignKey("company_profiles.id"), nullable=False)
    
    affected_kpi = Column(String(100), nullable=False) # gross_margin, inventory_turnover, etc.
    projected_impact_pct = Column(Float, nullable=False) # e.g. -2.3%
    impact_direction = Column(String(50), nullable=False) # negative, positive, neutral
    time_to_impact_days_min = Column(Integer, nullable=False) # e.g. 14
    time_to_impact_days_max = Column(Integer, nullable=False) # e.g. 28
    
    transmission_mechanism = Column(Text, nullable=False) # Explains the causal chain
    prescribed_actions = Column(JSON, nullable=False) # Actionable steps
    action_priority = Column(String(50), default="P1_HIGH", nullable=False) # P0_CRITICAL, P1_HIGH, P2_MEDIUM
    hedging_strategy = Column(Text, nullable=True)
    
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_by = Column(String(100), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    signal = relationship("MarketSignalEvent", back_populates="assessments")
    company = relationship("CompanyProfile", back_populates="assessments")
