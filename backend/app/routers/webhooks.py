from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Workflow, WorkflowRun
from app.services.workflow_engine import run_workflow

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/{workflow_id}")
async def trigger_via_webhook(workflow_id: str, request: Request, db: Session = Depends(get_db)):
    """External systems (CRMs, forms, cron services, etc.) POST here to fire a
    workflow whose definition contains a `trigger.webhook` node."""
    wf = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.is_active == True).first()  # noqa: E712
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found or inactive")

    payload: dict[str, Any] = {}
    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        payload = {}

    run = WorkflowRun(workflow_id=wf.id, status="running", trigger_type="webhook")
    db.add(run)
    db.commit()
    db.refresh(run)

    log = run_workflow(wf.definition, workspace_id=wf.workspace_id, trigger_payload=payload)
    run.log = log
    run.status = "success" if all(step["status"] == "success" for step in log) else "failed"
    run.finished_at = datetime.utcnow()
    db.commit()

    return {"run_id": run.id, "status": run.status}
