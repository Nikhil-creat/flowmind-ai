from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_membership, get_current_user
from app.core.limiter import limiter
from app.models.models import User, Workflow, WorkflowRun, WorkspaceMember
from app.models.schemas import WorkflowCreate, WorkflowOut, WorkflowRunOut, WorkflowUpdate
from app.services.workflow_engine import run_workflow
from app.services.scheduler import sync_schedule_for_workflow, remove_schedule_for_workflow

router = APIRouter(prefix="/api/workflows", tags=["workflows"])
settings = get_settings()


@router.post("", response_model=WorkflowOut)
def create_workflow(
    payload: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: WorkspaceMember = Depends(get_current_membership),
):
    wf = Workflow(workspace_id=membership.workspace_id, owner_id=current_user.id, name=payload.name,
                  description=payload.description, definition=payload.definition, is_active=payload.is_active)
    db.add(wf)
    db.commit()
    db.refresh(wf)
    sync_schedule_for_workflow(wf)
    return wf


@router.get("", response_model=list[WorkflowOut])
def list_workflows(db: Session = Depends(get_db), membership: WorkspaceMember = Depends(get_current_membership)):
    return (
        db.query(Workflow)
        .filter(Workflow.workspace_id == membership.workspace_id)
        .order_by(Workflow.updated_at.desc())
        .all()
    )


@router.get("/{workflow_id}", response_model=WorkflowOut)
def get_workflow(workflow_id: str, db: Session = Depends(get_db), membership: WorkspaceMember = Depends(get_current_membership)):
    wf = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.workspace_id == membership.workspace_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.put("/{workflow_id}", response_model=WorkflowOut)
def update_workflow(workflow_id: str, payload: WorkflowUpdate, db: Session = Depends(get_db), membership: WorkspaceMember = Depends(get_current_membership)):
    wf = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.workspace_id == membership.workspace_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(wf, field, value)
    db.commit()
    db.refresh(wf)
    sync_schedule_for_workflow(wf)
    return wf


@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: str, db: Session = Depends(get_db), membership: WorkspaceMember = Depends(get_current_membership)):
    wf = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.workspace_id == membership.workspace_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    remove_schedule_for_workflow(wf.id)
    db.delete(wf)
    db.commit()
    return {"deleted": workflow_id}


@router.post("/{workflow_id}/run", response_model=WorkflowRunOut)
@limiter.limit(settings.RATE_LIMIT_WORKFLOW_RUN)
def run_workflow_now(request: Request, workflow_id: str, db: Session = Depends(get_db), membership: WorkspaceMember = Depends(get_current_membership)):
    wf = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.workspace_id == membership.workspace_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    run = WorkflowRun(workflow_id=wf.id, status="running", trigger_type="manual")
    db.add(run)
    db.commit()
    db.refresh(run)

    log = run_workflow(wf.definition, workspace_id=membership.workspace_id, trigger_payload={"text": ""})
    run.log = log
    run.status = "success" if all(step["status"] == "success" for step in log) else "failed"
    run.finished_at = datetime.utcnow()
    db.commit()
    db.refresh(run)
    return run


@router.get("/{workflow_id}/runs", response_model=list[WorkflowRunOut])
def list_runs(workflow_id: str, db: Session = Depends(get_db), membership: WorkspaceMember = Depends(get_current_membership)):
    wf = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.workspace_id == membership.workspace_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return (
        db.query(WorkflowRun)
        .filter(WorkflowRun.workflow_id == workflow_id)
        .order_by(WorkflowRun.started_at.desc())
        .limit(50)
        .all()
    )
