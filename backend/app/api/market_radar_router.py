import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.all_models import MarketSignalEvent, CausalImpactAssessment, CompanyProfile, User
from backend.app.security.auth import get_current_active_user
from backend.app.analytics.market_intelligence import market_radar, MACRO_ELASTICITY_MATRIX
from backend.app.audit.service import log_audit_event

logger = logging.getLogger("bizinsight.market_radar_api")
router = APIRouter(prefix="/market-radar", tags=["Autonomous Market Radar"])

class AcknowledgeRequest(BaseModel):
    notes: Optional[str] = None

@router.get("/feed", summary="Get real-time market signals and company causal impact feed")
def get_market_radar_feed(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieves all detected macroeconomic signals and their company-specific causal assessments."""
    company = db.query(CompanyProfile).first()
    if not company:
        return {
            "configured": False,
            "message": "Company DNA not yet configured. Complete company profile onboarding.",
            "signals": [],
            "assessments": []
        }

    # Fetch recent signals and assessments
    assessments = db.query(CausalImpactAssessment).filter(
        CausalImpactAssessment.company_profile_id == company.id
    ).order_by(CausalImpactAssessment.created_at.desc()).all()

    formatted_assessments = []
    for a in assessments:
        sig = a.signal
        formatted_assessments.append({
            "id": a.id,
            "signal_id": sig.signal_id if sig else "UNKNOWN",
            "source": sig.source if sig else "MACRO_TELEMETRY",
            "factor_key": sig.factor_key if sig else "general",
            "headline": sig.headline if sig else "Market Shockwave",
            "event_summary": sig.event_summary if sig else "",
            "magnitude_pct": sig.magnitude_pct if sig else 0.0,
            "shock_direction": sig.shock_direction if sig else "surge",
            "confidence_score": sig.confidence_score if sig else 0.9,
            "affected_kpi": a.affected_kpi,
            "projected_impact_pct": a.projected_impact_pct,
            "impact_direction": a.impact_direction,
            "time_to_impact_days_min": a.time_to_impact_days_min,
            "time_to_impact_days_max": a.time_to_impact_days_max,
            "transmission_mechanism": a.transmission_mechanism,
            "prescribed_actions": a.prescribed_actions,
            "action_priority": a.action_priority,
            "hedging_strategy": a.hedging_strategy,
            "is_acknowledged": a.is_acknowledged,
            "acknowledged_by": a.acknowledged_by,
            "detected_at": sig.detected_at.isoformat() if sig else a.created_at.isoformat()
        })

    return {
        "configured": True,
        "organization_name": company.organization_name,
        "industry_sector": company.industry_sector,
        "sensitivities": company.key_macro_sensitivities,
        "total_active_shocks": len(formatted_assessments),
        "critical_p0_count": sum(1 for a in formatted_assessments if a["action_priority"] == "P0_CRITICAL"),
        "assessments": formatted_assessments
    }

@router.post("/scan", summary="Trigger autonomous AI market radar scan")
async def trigger_market_radar_scan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Executes a real-time market scan, correlates shocks against the Company DNA,
    and updates causal impact ledgers.
    """
    result = await market_radar.run_autonomous_radar_scan(db)
    
    log_audit_event(
        db=db,
        action="market_radar_scan_executed",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="market_radar",
        resource_id="scan_cycle",
        details=result
    )

    return result

@router.post("/assessments/{assessment_id}/acknowledge", summary="Executive sign-off on action briefing")
def acknowledge_assessment(
    assessment_id: int,
    payload: Optional[AcknowledgeRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Records formal executive acknowledgement and mitigation sign-off for governance audits."""
    assessment = db.query(CausalImpactAssessment).filter(
        CausalImpactAssessment.id == assessment_id
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment record not found.")

    assessment.is_acknowledged = True
    assessment.acknowledged_by = current_user.username
    assessment.acknowledged_at = datetime.now(timezone.utc)
    db.commit()

    log_audit_event(
        db=db,
        action="causal_assessment_acknowledged",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="causal_assessment",
        resource_id=str(assessment.id),
        details={
            "affected_kpi": assessment.affected_kpi,
            "action_priority": assessment.action_priority,
            "notes": payload.notes if payload else None
        }
    )

    return {"status": "acknowledged", "id": assessment.id, "acknowledged_by": current_user.username}

@router.get("/sensitivity-matrix", summary="Get econometric cross-elasticity matrix")
def get_sensitivity_matrix(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Returns the econometric pass-through elasticity equations mapping macro variables to KPIs."""
    company = db.query(CompanyProfile).first()
    matrix = []
    for factor, meta in MACRO_ELASTICITY_MATRIX.items():
        is_active = factor in (company.key_macro_sensitivities if company else [])
        matrix.append({
            "factor_key": factor,
            "affected_kpi": meta["affected_kpi"],
            "pass_through_elasticity": meta["pass_through_elasticity"],
            "lag_days": f"{meta['time_lag_days'][0]} - {meta['time_lag_days'][1]} days",
            "benchmark_source": meta["source"],
            "company_is_exposed": is_active
        })
    return {"matrix": matrix}

