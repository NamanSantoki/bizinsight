"""
Enterprise Platform 2.0 API Router
Exposes enterprise data platform, semantic layer, ABAC governance,
MLOps registry & monitoring, decision intelligence, and observability.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
import pandas as pd

from backend.app.core.database import get_db
from backend.app.models.all_models import User, Dataset
from backend.app.security.auth import get_current_user
from backend.app.security.rbac import require_role
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

router = APIRouter(prefix="/enterprise", tags=["enterprise-platform"])

# ----------------- DATA PLATFORM -----------------
@router.get("/sources")
def list_data_sources(current_user: User = Depends(get_current_user)):
    return data_source_manager.list_sources()

@router.post("/sources")
def add_data_source(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(require_role(["admin"]))
):
    name = payload.get("name", "New Source")
    stype = payload.get("type", "postgresql")
    url = payload.get("connection_url", "")
    return data_source_manager.add_source(name, stype, url)

@router.post("/sources/{source_id}/test")
def test_data_source(source_id: str, current_user: User = Depends(get_current_user)):
    return data_source_manager.test_connection(source_id)

@router.post("/sources/{source_id}/sync")
def sync_data_source(
    source_id: str,
    current_user: User = Depends(require_role(["admin", "analyst"]))
):
    return data_source_manager.trigger_sync(source_id)

@router.get("/contracts/{dataset_name}")
def get_data_contract(dataset_name: str, current_user: User = Depends(get_current_user)):
    return contract_engine.get_contract(dataset_name)

@router.get("/contracts/{dataset_name}/quarantine")
def get_quarantined_records(dataset_name: str, current_user: User = Depends(get_current_user)):
    return contract_engine.get_quarantined_records(dataset_name)

@router.get("/quality-gates/{dataset_id}")
def evaluate_dataset_quality_gate(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        df = pd.read_sql_table(dataset.table_name, con=db.bind)
    except Exception:
        df = pd.DataFrame()

    dq_result = quality_gate_engine.evaluate_dataframe(df, dataset.name)
    contract_result = contract_engine.validate_dataframe(dataset.name, df)
    
    # Combined gate verdict
    final_status = "PUBLISHED" if (dq_result["gate_passed"] and contract_result["status"] == "PASSED") else "QUARANTINED"
    
    return {
        "dataset_id": dataset.id,
        "dataset_name": dataset.name,
        "final_gate_verdict": final_status,
        "quality_score_summary": dq_result,
        "contract_validation_summary": contract_result
    }

@router.get("/lineage")
def get_data_lineage(current_user: User = Depends(get_current_user)):
    return lineage_engine.get_lineage_graph()

@router.get("/lineage/{node_id}")
def get_lineage_node_details(node_id: str, current_user: User = Depends(get_current_user)):
    node = lineage_engine.get_node_lineage(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Lineage node {node_id} not found")
    return node

# ----------------- SEMANTIC LAYER -----------------
@router.get("/semantic/metrics")
def list_semantic_metrics(current_user: User = Depends(get_current_user)):
    return metrics_store.list_metrics()

@router.get("/semantic/metrics/{metric_id}")
def get_semantic_metric(metric_id: str, current_user: User = Depends(get_current_user)):
    metric = metrics_store.get_metric(metric_id)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found in semantic layer")
    return metric

@router.post("/semantic/query")
def compile_semantic_query(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
):
    metric_id = payload.get("metric_id", "revenue")
    dimension = payload.get("dimension")
    filter_str = payload.get("filter")
    return metrics_store.compile_query(metric_id, dimension, filter_str)

# ----------------- GOVERNANCE & SECURITY -----------------
@router.post("/governance/abac/evaluate")
def evaluate_abac_policy(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
):
    user_role = payload.get("user_role", current_user.role)
    user_dept = payload.get("user_department", "Finance")
    user_reg = payload.get("user_region", "Global")
    res_dept = payload.get("resource_department", "Finance")
    res_sens = payload.get("resource_sensitivity", "Confidential")
    action = payload.get("action", "read")
    return abac_engine.evaluate(user_role, user_dept, user_reg, res_dept, res_sens, action)

@router.get("/governance/classification/{dataset_id}")
def get_dataset_classification(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    try:
        df = pd.read_sql_table(dataset.table_name, con=db.bind)
    except Exception:
        df = pd.DataFrame()
    return classification_engine.classify_dataframe(df)

@router.get("/governance/approvals")
def list_governance_approvals(current_user: User = Depends(get_current_user)):
    return approval_engine.list_requests()

@router.post("/governance/approvals")
def create_governance_approval(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
):
    action = payload.get("action", "MODEL_DEPLOYMENT")
    resource = payload.get("resource", "Default Resource")
    reason = payload.get("reason", "Standard operational workflow")
    meta = payload.get("metadata", {})
    return approval_engine.create_request(action, resource, current_user.username, reason, meta)

@router.post("/governance/approvals/{request_id}/review")
def review_governance_approval(
    request_id: str,
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(require_role(["admin"]))
):
    approve = payload.get("approve", True)
    note = payload.get("note", "Reviewed and verified.")
    return approval_engine.review_request(request_id, current_user.username, approve, note)

@router.post("/governance/export")
def request_governed_export(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
):
    dataset_name = payload.get("dataset_name", "dataset")
    classification = payload.get("classification", "Confidential")
    contains_pii = payload.get("contains_pii", True)
    return export_governance.request_export(
        dataset_name=dataset_name,
        user_role=current_user.role,
        user_department="Finance",
        user_id=current_user.username,
        classification_tier=classification,
        contains_pii=contains_pii
    )

# ----------------- MLOPS PLATFORM -----------------
@router.get("/mlops/models")
def list_mlops_models(current_user: User = Depends(get_current_user)):
    return model_registry.list_models()

@router.post("/mlops/models/transition")
def transition_model_stage(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(require_role(["admin"]))
):
    model_name = payload.get("model_name", "Revenue Forecast Model")
    version = payload.get("version", "v7")
    target_stage = payload.get("target_stage", "PRODUCTION")
    return model_registry.transition_stage(model_name, version, target_stage, current_user.username)

@router.get("/mlops/monitoring")
def get_mlops_monitoring(current_user: User = Depends(get_current_user)):
    return ml_monitoring.get_monitoring_overview()

# ----------------- DECISION INTELLIGENCE -----------------
@router.post("/decision/scenario")
def run_digital_twin_scenario(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
):
    mkt = float(payload.get("marketing_delta_pct", 0.0))
    price = float(payload.get("price_delta_pct", 0.0))
    staff = float(payload.get("sales_staff_delta_pct", 0.0))
    return scenario_engine.simulate_scenario(mkt, price, staff)

@router.post("/decision/prescriptive")
def run_prescriptive_optimization(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
):
    target_rev = float(payload.get("target_revenue_cr", 25.0))
    min_margin = float(payload.get("min_margin_pct", 20.0))
    max_budget = float(payload.get("max_marketing_budget_cr", 4.0))
    return prescriptive_optimizer.optimize(target_rev, min_margin, max_budget)

@router.get("/decision/causal")
def get_causal_econometric_evaluation(current_user: User = Depends(get_current_user)):
    return causal_rigor_engine.evaluate_causal_effect()

# ----------------- OBSERVABILITY & OPERATIONS -----------------
@router.get("/observability/telemetry")
def get_system_telemetry(current_user: User = Depends(get_current_user)):
    return telemetry_cost.get_system_telemetry()

@router.get("/observability/costs")
def get_cloud_cost_governance(current_user: User = Depends(get_current_user)):
    return telemetry_cost.get_cost_observability()

@router.get("/observability/operations")
def get_operations_center_status(current_user: User = Depends(get_current_user)):
    return operations_center.get_operations_status()

