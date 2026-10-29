from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from backend.app.security.auth import get_current_active_user
from backend.app.ingestion.scheduler import ingestion_scheduler
from backend.app.notifications.dispatcher import dispatcher
from backend.app.security.api_keys import api_key_manager

router = APIRouter(prefix="/enterprise-connectors", tags=["Enterprise Connectors & Automation"])

class CreateScheduleRequest(BaseModel):
    name: str
    source_id: int
    cron_expression: str
    incremental_column: Optional[str] = None

class CreateAPIKeyRequest(BaseModel):
    name: str
    scopes: List[str]
    rate_limit_per_minute: int = 120

class WebhookAlertRequest(BaseModel):
    webhook_url: str
    title: str
    message: str
    severity: str = "warning"
    fields: Optional[Dict[str, Any]] = None

# --- Ingestion Schedules & CDC ---
@router.get("/schedules", summary="List automated CDC & recurring ingestion schedules")
def list_ingestion_schedules(current_user = Depends(get_current_active_user)):
    return {"schedules": ingestion_scheduler.list_schedules()}

@router.post("/schedules", summary="Register a new automated cron schedule")
def register_ingestion_schedule(
    payload: CreateScheduleRequest,
    current_user = Depends(get_current_active_user)
):
    import uuid
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    task = ingestion_scheduler.register_schedule(
        task_id=task_id,
        name=payload.name,
        source_id=payload.source_id,
        cron_expression=payload.cron_expression,
        incremental_column=payload.incremental_column
    )
    return {"status": "REGISTERED", "task_id": task.task_id}

@router.post("/schedules/{task_id}/run", summary="Trigger manual execution of an incremental sync job")
def trigger_schedule_now(
    task_id: str,
    new_records: int = Query(default=250),
    current_user = Depends(get_current_active_user)
):
    try:
        result = ingestion_scheduler.trigger_sync_now(task_id, new_records=new_records)
        return result
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

# --- API Key Management ---
@router.get("/api-keys", summary="List active developer and machine-to-machine API keys")
def list_api_keys(current_user = Depends(get_current_active_user)):
    return {"api_keys": api_key_manager.list_keys()}

@router.post("/api-keys", summary="Generate a new scoped enterprise API key")
def generate_api_key(
    payload: CreateAPIKeyRequest,
    current_user = Depends(get_current_active_user)
):
    return api_key_manager.create_key(
        name=payload.name,
        scopes=payload.scopes,
        rate_limit=payload.rate_limit_per_minute
    )

# --- Real-Time Alert Dispatching (Slack / Webhooks) ---
@router.post("/alerts/slack", summary="Dispatch real-time enterprise alert to Slack channel")
async def dispatch_slack_alert(
    payload: WebhookAlertRequest,
    current_user = Depends(get_current_active_user)
):
    success = await dispatcher.send_slack_alert(
        webhook_url=payload.webhook_url,
        title=payload.title,
        message=payload.message,
        severity=payload.severity,
        fields=payload.fields
    )
    return {
        "delivered": success,
        "channel": "slack",
        "severity": payload.severity,
        "title": payload.title
    }

