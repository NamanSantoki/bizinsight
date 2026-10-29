"""
Comprehensive Test Suite for BIZINSIGHT Enterprise Platform 2.0
Covers Data Platform (Connectors, Contracts, Quality Gates, Lineage),
Semantic Layer, ABAC, Masking, PII Classification, Approvals, MLOps Registry & Monitoring,
Decision Intelligence (Digital Twin, Prescriptive, Causal Rigor), and Observability.
"""
import pytest
import pandas as pd
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.data_platform.connectors import data_source_manager
from backend.app.data_platform.contracts import contract_engine
from backend.app.data_platform.quality_engine import quality_gate_engine
from backend.app.data_platform.lineage import lineage_engine
from backend.app.semantic.metrics_store import metrics_store
from backend.app.governance.abac import abac_engine
from backend.app.governance.masking import masking_engine
from backend.app.governance.classification import classification_engine
from backend.app.governance.approvals import approval_engine
from backend.app.governance.export_governance import export_governance
from backend.app.mlops.registry import model_registry
from backend.app.mlops.monitoring import ml_monitoring
from backend.app.decision_intelligence.scenario_engine import scenario_engine
from backend.app.decision_intelligence.prescriptive_optimizer import prescriptive_optimizer
from backend.app.decision_intelligence.causal_rigor import causal_rigor_engine
from backend.app.observability.probes import health_probes
from backend.app.observability.telemetry import telemetry_cost
from backend.app.observability.incidents import operations_center
from backend.app.ai.ask_data import format_governed_ai_response, validate_sql_query

client = TestClient(app)

def test_data_source_connectors_and_sync():
    sources = data_source_manager.list_sources()
    assert len(sources) >= 4
    pg_source = next((s for s in sources if s["type"] == "postgresql"), None)
    assert pg_source is not None
    assert "pg-prod.internal" in pg_source["connection_url_masked"]
    assert "***" in pg_source["connection_url_masked"]

    # Test connection probe
    test_res = data_source_manager.test_connection(pg_source["id"])
    assert test_res["status"] == "success"
    assert test_res["ping_latency_ms"] > 0

    # Test sync
    sync_res = data_source_manager.trigger_sync(pg_source["id"])
    assert sync_res["status"] == "sync_completed"

def test_data_contracts_validation_and_quarantine():
    # Compliant dataframe
    good_df = pd.DataFrame({
        "order_id": [101, 102, 103],
        "customer_id": [1, 2, 3],
        "order_date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        "revenue": [250.0, 180.5, 420.0],
        "status": ["completed", "pending", "completed"]
    })
    res_good = contract_engine.validate_dataframe("sales_orders", good_df)
    assert res_good["status"] == "PASSED"
    assert res_good["schema_compatible"] is True

    # Violating dataframe: duplicate order_id, negative revenue, invalid enum
    bad_df = pd.DataFrame({
        "order_id": [101, 101, 103],
        "customer_id": [1, 2, 3],
        "order_date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        "revenue": [-50.0, 180.5, 420.0],
        "status": ["completed", "hacked_status", "completed"]
    })
    res_bad = contract_engine.validate_dataframe("sales_orders", bad_df)
    assert res_bad["status"] == "QUARANTINED"
    assert res_bad["duplicate_keys_count"] >= 1
    assert res_bad["quarantined_count"] >= 1
    assert len(res_bad["violations_summary"]) >= 2

def test_enterprise_data_quality_dimensions_and_gates():
    df = pd.DataFrame({
        "customer_id": [1, 2, 3, 4, 5],
        "revenue": [100.0, 200.0, 150.0, 300.0, 250.0],
        "order_date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"]
    })
    dq_res = quality_gate_engine.evaluate_dataframe(df, "clean_sales")
    assert dq_res["overall_score"] >= 95.0
    assert dq_res["gate_status"] == "PUBLISHED"
    assert dq_res["gate_passed"] is True
    assert "completeness" in dq_res["dimensions"]
    assert "uniqueness" in dq_res["dimensions"]
    assert "validity" in dq_res["dimensions"]

def test_lineage_dag_graph_and_node_lookup():
    graph = lineage_engine.get_lineage_graph()
    assert len(graph["nodes"]) >= 8
    assert len(graph["edges"]) >= 7

    node = lineage_engine.get_node_lineage("lake_curated_sales")
    assert node is not None
    assert node["layer"] == "curated"
    assert "lake_clean_sales" in node["upstream_datasets"]
    assert "kpi_revenue" in node["downstream_consumers"]

def test_semantic_metrics_store_and_sql_compilation():
    metrics = metrics_store.list_metrics()
    assert len(metrics) >= 5
    rev_metric = next((m for m in metrics if m["id"] == "revenue"), None)
    assert rev_metric is not None
    assert "SUM" in rev_metric["formula"]

    # Test query compilation with dimension
    compiled = metrics_store.compile_query("revenue", dimension="region")
    assert "compiled_sql" in compiled
    assert "GROUP BY region" in compiled["compiled_sql"]
    assert compiled["governance"]["zero_metric_hallucination"] is True

def test_abac_policy_evaluation():
    # Admin allowed
    res_admin = abac_engine.evaluate("admin", "IT", "Europe", "Finance", "Highly Sensitive")
    assert res_admin["decision"] == "ALLOW"

    # Cross-department denied
    res_cross = abac_engine.evaluate("analyst", "Marketing", "Europe", "Finance", "Confidential")
    assert res_cross["decision"] == "DENY"
    assert "Cross-department" in res_cross["reason"]

    # Same department allowed
    res_same = abac_engine.evaluate("analyst", "Finance", "Europe", "Finance", "Confidential")
    assert res_same["decision"] == "ALLOW"

def test_row_and_column_dynamic_masking():
    df = pd.DataFrame({
        "customer_id": [101, 102],
        "email": ["naman@enterprise.com", "alice@corp.de"],
        "phone": ["+49-170-1234567", "+1-555-9876543"],
        "region": ["Europe", "NorthAmerica"],
        "revenue": [5000, 7500]
    })

    # Non-admin analyst in Europe
    masked_df = masking_engine.apply_security_policies(df, user_role="analyst", user_region="Europe")
    assert len(masked_df) == 1  # Row filtered to Europe only!
    first_email = masked_df.iloc[0]["email"]
    assert "@" in first_email and "***" in first_email  # Dynamic PII masking!

def test_automated_pii_classification():
    df = pd.DataFrame({
        "order_id": [1, 2],
        "customer_email": ["test@domain.com", "user@corp.com"],
        "passport_no": ["L890123", "P456789"],
        "revenue": [1200.0, 3400.0],
        "country": ["Germany", "France"]
    })
    clf = classification_engine.classify_dataframe(df)
    assert clf["summary_counts"]["highly_sensitive"] >= 1  # passport_no
    assert clf["summary_counts"]["confidential"] >= 2     # customer_email, revenue
    assert clf["summary_counts"]["public"] >= 1           # country

def test_governance_approval_workflow():
    req = approval_engine.create_request("MODEL_DEPLOYMENT", "Forecast v8", "lead_ds", "Exceeds production KPI")
    req_id = req["id"]
    assert req["status"] == "PENDING_APPROVAL"

    # Reviewer approval
    review = approval_engine.review_request(req_id, reviewer="admin", approve=True, note="All metrics validated")
    assert review["status"] == "APPROVED"
    assert review["reviewer"] == "admin"

def test_governed_export_pipeline():
    # Viewer should be denied
    denied = export_governance.request_export("sales_curated", "viewer", "Finance", "user_v", "Confidential", False)
    assert denied["authorized"] is False

    # Analyst exporting public data
    allowed = export_governance.request_export("sales_curated", "analyst", "Finance", "user_a", "Public", False)
    assert allowed["authorized"] is True
    assert "exp_" in allowed["download_token"]

def test_mlops_model_registry_and_lifecycle():
    models = model_registry.list_models()
    assert len(models) >= 2
    fc_model = next((m for m in models if m["name"] == "Revenue Forecast Model"), None)
    assert fc_model is not None
    assert fc_model["current_production_version"] == "v7"

    # Stage transition
    trans = model_registry.transition_stage("Revenue Forecast Model", "v6", "STAGING")
    assert trans["status"] == "success"

def test_mlops_drift_monitoring_and_alerts():
    monitoring = ml_monitoring.get_monitoring_overview()
    assert len(monitoring) >= 2
    v7 = next((m for m in monitoring if m["model_id"] == "rev_fc_07"), None)
    assert v7 is not None
    assert v7["drift_status"] == "WARNING"
    assert v7["retraining_recommendation"]["is_candidate"] is True

def test_digital_twin_scenario_simulation():
    res = scenario_engine.simulate_scenario(marketing_delta_pct=15.0, price_delta_pct=3.0, sales_staff_delta_pct=8.0)
    assert res["projected"]["revenue_cr"] > res["baseline"]["revenue_cr"]
    assert len(res["projected"]["prediction_interval_80"]) == 2
    assert res["projected"]["confidence_score"] > 80.0

def test_prescriptive_goal_seek_optimizer():
    opt = prescriptive_optimizer.optimize(target_revenue_cr=25.0, min_margin_pct=20.0, max_marketing_budget_cr=4.0)
    assert opt["feasible"] is True
    assert opt["feasibility_score"] > 85.0
    assert "marketing_spend_delta" in opt["recommended_strategy"]

def test_causal_rigor_and_assumptions():
    causal = causal_rigor_engine.evaluate_causal_effect()
    assert causal["causal_effect"]["average_treatment_effect_ate"] > 0
    assert len(causal["covariate_balance"]) >= 3
    assert causal["refutation_tests"]["placebo_treatment_refuter"]["passed"] is True
    assert len(causal["assumptions_checklist"]) == 3
    assert "Association ≠ Causation" in causal["epistemic_disclaimer"]

def test_observability_health_probes():
    live = health_probes.liveness()
    assert live["status"] == "UP"

    ready = health_probes.readiness()
    assert ready["status"] in ["ok", "UP"]
    assert ready["state"] == "UP"

    db_res = health_probes.database_check()
    assert db_res["status"] == "HEALTHY"

    ml_res = health_probes.ml_service_check()
    assert ml_res["status"] == "HEALTHY"

def test_telemetry_and_cost_governance():
    telemetry = telemetry_cost.get_system_telemetry()
    assert telemetry["traffic"]["requests_total_24h"] > 0
    assert telemetry["latency"]["p95_ms"] > 0

    costs = telemetry_cost.get_cost_observability()
    assert costs["total_spend"] == 9150.0
    assert len(costs["breakdown_by_category"]) == 4

def test_operations_center_and_incident_management():
    ops = operations_center.get_operations_status()
    assert len(ops["services"]) >= 4
    assert len(ops["active_incidents"]) >= 1
    assert "INC-1042" in ops["active_incidents"][0]["id"]

def test_governed_ask_data_query_id_and_citations():
    results = [{"region": "Europe", "revenue": 142000.0}, {"region": "APAC", "revenue": 98000.0}]
    ai_resp = format_governed_ai_response("Why did revenue fall across regions?", "SELECT region, revenue FROM sales", results, "sales_curated")
    assert "QRY-" in ai_resp["query_id"]
    assert ai_resp["ast_validated"] is True
    assert len(ai_resp["evidence"]) >= 2
    assert len(ai_resp["contributors"]) == 2
