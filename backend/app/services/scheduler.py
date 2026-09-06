"""
Wires "trigger.schedule" nodes to APScheduler cron jobs, so workflows can
run automatically (e.g. daily digests) without any request from the frontend.
"""
from __future__ import annotations

from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()


def _job_id(workflow_id: str) -> str:
    return f"workflow-{workflow_id}"


def _execute_scheduled_workflow(workflow_id: str) -> None:
    # Imported lazily to avoid circular imports at module load time.
    from app.core.database import SessionLocal
    from app.models.models import Workflow, WorkflowRun
    from app.services.workflow_engine import run_workflow

    db = SessionLocal()
    try:
        wf = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.is_active == True).first()  # noqa: E712
        if not wf:
            return
        run = WorkflowRun(workflow_id=wf.id, status="running", trigger_type="schedule")
        db.add(run)
        db.commit()
        db.refresh(run)

        log = run_workflow(wf.definition, user_id=wf.owner_id, trigger_payload={"text": ""})
        run.log = log
        run.status = "success" if all(step["status"] == "success" for step in log) else "failed"
        run.finished_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


def _find_schedule_node(definition: dict) -> dict | None:
    for node in definition.get("nodes", []):
        if node.get("type") == "trigger.schedule":
            return node
    return None


def sync_schedule_for_workflow(workflow) -> None:
    """Add/update/remove the APScheduler job to match the workflow's current state."""
    job_id = _job_id(workflow.id)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    if not workflow.is_active:
        return

    node = _find_schedule_node(workflow.definition)
    if not node:
        return

    cron_expr = node.get("data", {}).get("cron")  # e.g. "0 9 * * *" = every day at 9am
    if not cron_expr:
        return

    scheduler.add_job(
        _execute_scheduled_workflow,
        CronTrigger.from_crontab(cron_expr),
        args=[workflow.id],
        id=job_id,
        replace_existing=True,
    )


def remove_schedule_for_workflow(workflow_id: str) -> None:
    job_id = _job_id(workflow_id)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
