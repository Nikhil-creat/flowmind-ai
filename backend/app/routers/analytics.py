from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import Document, User, Workflow, WorkflowRun
from app.models.schemas import DashboardStats

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    workflow_ids = [w.id for w in db.query(Workflow.id).filter(Workflow.owner_id == current_user.id).all()]
    runs = db.query(WorkflowRun).filter(WorkflowRun.workflow_id.in_(workflow_ids)).all() if workflow_ids else []

    since = datetime.utcnow() - timedelta(days=7)
    daily = Counter()
    for r in runs:
        if r.started_at and r.started_at >= since:
            daily[r.started_at.date().isoformat()] += 1

    return DashboardStats(
        total_documents=db.query(Document).filter(Document.owner_id == current_user.id).count(),
        total_workflows=len(workflow_ids),
        active_workflows=db.query(Workflow).filter(Workflow.owner_id == current_user.id, Workflow.is_active == True).count(),  # noqa: E712
        total_workflow_runs=len(runs),
        successful_runs=sum(1 for r in runs if r.status == "success"),
        failed_runs=sum(1 for r in runs if r.status == "failed"),
        runs_last_7_days=[{"date": d, "count": c} for d, c in sorted(daily.items())],
    )
