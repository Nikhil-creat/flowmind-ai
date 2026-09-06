from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_membership, get_current_user, require_role
from app.models.models import User, Workspace, WorkspaceMember
from app.models.schemas import (CheckoutResponse, MemberInvite, MemberOut,
                                 MemberRoleUpdate, WorkspaceCreate, WorkspaceOut)
from app.services import billing

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceOut])
def list_my_workspaces(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id).all()
    out = []
    for m in memberships:
        ws = db.query(Workspace).filter(Workspace.id == m.workspace_id).first()
        if ws:
            out.append(WorkspaceOut(id=ws.id, name=ws.name, plan=ws.plan, role=m.role, created_at=ws.created_at))
    return out


@router.post("", response_model=WorkspaceOut)
def create_workspace(payload: WorkspaceCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = Workspace(name=payload.name, plan="free")
    db.add(ws)
    db.commit()
    db.refresh(ws)
    db.add(WorkspaceMember(workspace_id=ws.id, user_id=current_user.id, role="owner"))
    db.commit()
    return WorkspaceOut(id=ws.id, name=ws.name, plan=ws.plan, role="owner", created_at=ws.created_at)


@router.get("/{workspace_id}/members", response_model=list[MemberOut])
def list_members(
    workspace_id: str,
    membership: WorkspaceMember = Depends(get_current_membership),
    db: Session = Depends(get_db),
):
    if membership.workspace_id != workspace_id:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    members = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id).all()
    out = []
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        if user:
            out.append(MemberOut(user_id=user.id, full_name=user.full_name, email=user.email, role=m.role, created_at=m.created_at))
    return out


@router.post("/{workspace_id}/invite", response_model=MemberOut)
def invite_member(
    workspace_id: str,
    payload: MemberInvite,
    db: Session = Depends(get_db),
    _: WorkspaceMember = Depends(require_role("owner", "admin")),
):
    """Adds an existing FlowMind user to the workspace by email. (Inviting
    someone who hasn't signed up yet - i.e. emailing them a signup link - is
    a natural next step; this covers the core team-membership mechanic.)"""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No FlowMind account found for that email yet")

    existing = (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already a member of this workspace")

    member = WorkspaceMember(workspace_id=workspace_id, user_id=user.id, role=payload.role)
    db.add(member)
    db.commit()
    return MemberOut(user_id=user.id, full_name=user.full_name, email=user.email, role=member.role, created_at=member.created_at)


@router.put("/{workspace_id}/members/{user_id}", response_model=MemberOut)
def update_member_role(
    workspace_id: str,
    user_id: str,
    payload: MemberRoleUpdate,
    db: Session = Depends(get_db),
    _: WorkspaceMember = Depends(require_role("owner")),
):
    member = (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.role = payload.role
    db.commit()
    user = db.query(User).filter(User.id == user_id).first()
    return MemberOut(user_id=user.id, full_name=user.full_name, email=user.email, role=member.role, created_at=member.created_at)


@router.delete("/{workspace_id}/members/{user_id}")
def remove_member(
    workspace_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    _: WorkspaceMember = Depends(require_role("owner", "admin")),
):
    member = (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
    return {"removed": user_id}


@router.post("/{workspace_id}/billing/checkout", response_model=CheckoutResponse)
def create_billing_checkout(
    workspace_id: str,
    db: Session = Depends(get_db),
    membership: WorkspaceMember = Depends(require_role("owner")),
):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    result = billing.create_checkout_session(ws.id, ws.name)
    return CheckoutResponse(**result)
