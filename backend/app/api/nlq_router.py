from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict

# Import existing NLQ logic
from ..ai.ask_data import process_natural_language_query
from ..audit.jsonl_exporter import log_nlq_query
from ..security.rbac import require_role

router = APIRouter(prefix="/enterprise/nlq", tags=["NLQ"])

class NLQRequest(BaseModel):
    query: str
    dataset_id: str

class NLQResponse(BaseModel):
    query: str
    sql: str
    result: Any
    contract_id: str | None = None

@router.post("/", response_model=NLQResponse)
async def run_nlq(request: NLQRequest, role: str = Depends(require_role("user"))):
    """Run a natural‑language query against a dataset with governance audit.

    The underlying `process_natural_language_query` returns a tuple
    `(sql_statement, result, contract_id)`.  The call is wrapped in an audit
    record that stores the raw NL query, generated SQL, user/team role and
    timestamp.
    """
    try:
        sql, result, contract_id = await process_natural_language_query(
            request.query, request.dataset_id
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Governance audit – store a JSON line entry
    log_nlq_query(
        user_role=role,
        dataset_id=request.dataset_id,
        nl_query=request.query,
        sql=sql,
    )
    return NLQResponse(
        query=request.query,
        sql=sql,
        result=result,
        contract_id=contract_id,
    )

