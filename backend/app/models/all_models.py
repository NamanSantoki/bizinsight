import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum, JSON
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    datasets = relationship("Dataset", back_populates="owner")
    audit_logs = relationship("AuditLog", back_populates="user")

class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)  # csv, excel, postgres, api
    connection_config = Column(JSON, nullable=True)   # for api or postgres
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

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
    
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    schema_metadata = Column(JSON, nullable=True)
    
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="anomalies")

class CustomerSegmentRecord(Base):
    __tablename__ = "customer_segments"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    cluster_id = Column(Integer, nullable=False)
    segment_label = Column(String(100), nullable=False) # e.g. "High Value, High Frequency"
    customer_count = Column(Integer, nullable=False)
    characteristics = Column(JSON, nullable=False) # avg recency, avg frequency, avg monetary
    created_at = Column(DateTime, default=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")
