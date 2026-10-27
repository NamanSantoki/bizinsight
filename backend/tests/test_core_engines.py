import pytest
import pandas as pd
import numpy as np
from backend.app.ingestion.service import inspect_and_read_file
from backend.app.analytics.profiler import compute_dataset_profile
from backend.app.data_quality.engine import evaluate_data_quality
from backend.app.data_quality.cleaner import clean_dataset
from backend.app.analytics.kpi import compute_business_kpis
from backend.app.forecasting.engine import run_chronological_forecasting, evaluate_forecast_metrics
from backend.app.anomaly.engine import detect_anomalies
from backend.app.segmentation.engine import run_rfm_segmentation
from backend.app.ai.ask_data import validate_sql_query
from backend.app.security.auth import get_password_hash, verify_password

def test_password_hashing():
    pwd = "EnterpriseSecurePassword2026!"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_csv_ingestion_and_delimiter_detection():
    csv_content = b"invoice_id,customer_id,transaction_date,amount,region\n1,C101,2026-01-01,150.50,North\n2,C102,2026-01-02,230.00,South\n"
    df, meta = inspect_and_read_file(csv_content, "test_sales.csv")
    assert len(df) == 2
    assert meta["raw_rows"] == 2
    assert "amount" in meta["numeric_columns"]
    assert "transaction_date" in meta["date_columns"]

def test_data_profiler_and_statistics():
    df = pd.DataFrame({
        "sales": [10.0, 20.0, 30.0, 40.0, 1000.0],
        "category": ["A", "B", "A", "C", "A"],
        "date": pd.date_range("2026-01-01", periods=5)
    })
    profile = compute_dataset_profile(df)
    assert profile["dimensions"]["total_rows"] == 5
    assert profile["columns"]["sales"]["stats"]["min"] == 10.0
    assert profile["columns"]["sales"]["stats"]["max"] == 1000.0
    assert profile["columns"]["category"]["top_categories"]["A"] == 3

def test_data_quality_scoring_formula():
    # Clean dataset -> High score
    clean_df = pd.DataFrame({
        "revenue": [100.0, 200.0, 150.0, 180.0, 220.0],
        "customer": ["C1", "C2", "C3", "C4", "C5"]
    })
    res_clean = evaluate_data_quality(clean_df)
    assert res_clean["quality_score"] == 100.0
    assert res_clean["passed"] is True

    # Dirty dataset with nulls, duplicates, and prohibited negative price
    dirty_df = pd.DataFrame({
        "revenue": [100.0, -50.0, np.nan, 100.0, 100.0],
        "customer": ["C1", "C2", "C3", "C1", "C1"]
    })
    res_dirty = evaluate_data_quality(dirty_df)
    assert res_dirty["quality_score"] < 100.0
    assert any(i["issue_type"] == "invalid_negative_values" for i in res_dirty["column_issues"])

def test_auditable_data_cleaning():
    df = pd.DataFrame({
        "Product Name ": ["Widget A", "Widget B", "Widget A"],
        "price": [10.0, np.nan, 10.0]
    })
    cleaned, logs = clean_dataset(df, remove_duplicates=True, missing_strategy="median_mode", clean_column_names=True)
    assert len(cleaned) == 2 # 1 duplicate removed
    assert "product_name" in cleaned.columns # column renamed
    assert cleaned["price"].isnull().sum() == 0 # imputed
    assert len(logs) > 0

def test_business_kpis():
    df = pd.DataFrame({
        "order_date": pd.date_range("2026-01-01", periods=30, freq="D"),
        "revenue": [100.0 + i * 5 for i in range(30)],
        "customer_id": [f"C{i%5}" for i in range(30)],
        "region": ["North", "South", "East"] * 10
    })
    kpis = compute_business_kpis(df)
    assert kpis["primary_metric"] == "revenue"
    assert "total_metric" in kpis["cards"]
    assert len(kpis["trends"]) > 0
    assert len(kpis["breakdowns"]["regions"]) == 3

def test_chronological_forecasting_integrity():
    # Construct 60 days of real business series
    dates = pd.date_range("2026-01-01", periods=60, freq="D")
    sales = [100.0 + (i % 7) * 20.0 + i * 1.5 + (np.sin(i) * 10) for i in range(60)]
    df = pd.DataFrame({"trans_date": dates, "sales": sales})

    res = run_chronological_forecasting(
        df=df,
        date_col="trans_date",
        target_col="sales",
        forecast_horizon=7,
        frequency="D"
    )
    assert res["status"] == "success"
    assert "Chronological" in res["validation_strategy"]
    assert len(res["model_comparison"]) >= 4
    assert len(res["future_predictions"]) == 7
    # Verify uncertainty interval exists
    assert "lower_bound" in res["future_predictions"][0]
    assert "upper_bound" in res["future_predictions"][0]
    assert res["future_predictions"][0]["lower_bound"] <= res["future_predictions"][0]["forecast"]
    assert res["future_predictions"][0]["upper_bound"] >= res["future_predictions"][0]["forecast"]

def test_forecasting_honesty_on_insufficient_data():
    df = pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=5),
        "sales": [10, 20, 30, 40, 50]
    })
    res = run_chronological_forecasting(df, "date", "sales")
    assert "error" in res
    assert "Insufficient temporal observations" in res["error"]

def test_isolation_forest_anomalies():
    np.random.seed(42)
    normal_data = np.random.normal(loc=50, scale=5, size=(100, 2))
    outliers = np.array([[500.0, 600.0], [520.0, 580.0]])
    data = np.vstack([normal_data, outliers])
    df = pd.DataFrame(data, columns=["metric_a", "metric_b"])

    res = detect_anomalies(df, feature_columns=["metric_a", "metric_b"], contamination=0.03)
    assert res["status"] == "success"
    assert res["anomalies_detected_count"] > 0
    assert len(res["top_anomalies"]) > 0

def test_rfm_customer_segmentation():
    records = []
    # 20 distinct customers with multiple purchases
    for c_id in range(25):
        for o in range(1 + (c_id % 5)):
            records.append({
                "cust_id": f"C_{c_id}",
                "date": f"2026-0{(c_id%3)+1}-15",
                "spend": 50.0 + (c_id * 35.0)
            })
    df = pd.DataFrame(records)
    res = run_rfm_segmentation(df, "cust_id", "date", "spend", n_clusters=3)
    assert res["status"] == "success"
    assert len(res["segments"]) == 3
    assert res["total_unique_customers"] == 25

def test_sql_security_filter():
    # Valid SELECT
    is_valid, q, err = validate_sql_query('SELECT * FROM "sales" WHERE revenue > 100', "sales")
    assert is_valid is True
    assert "LIMIT" in q

    # Block DROP TABLE
    is_valid_drop, _, err_drop = validate_sql_query('DROP TABLE "sales"', "sales")
    assert is_valid_drop is False
    assert "Security Violation" in err_drop or "Only SELECT" in err_drop

    # Block DELETE
    is_valid_del, _, err_del = validate_sql_query('DELETE FROM "sales" WHERE 1=1', "sales")
    assert is_valid_del is False

    # Block UPDATE
    is_valid_up, _, err_up = validate_sql_query('UPDATE "sales" SET revenue = 0', "sales")
    assert is_valid_up is False
