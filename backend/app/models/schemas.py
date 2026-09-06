from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=8)
    company: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str


# ---------- Workspaces / Teams ----------
class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceOut(BaseModel):
    id: str
    name: str
    plan: str
    role: str  # the requesting user's role in this workspace
    created_at: datetime

    class Config:
        from_attributes = True


class MemberInvite(BaseModel):
    email: EmailStr
    role: str = "member"  # owner | admin | member


class MemberRoleUpdate(BaseModel):
    role: str


class MemberOut(BaseModel):
    user_id: str
    full_name: str
    email: EmailStr
    role: str
    created_at: datetime


class CheckoutResponse(BaseModel):
    configured: bool
    checkout_url: Optional[str] = None
    message: str


class UserOut(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    company: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Documents ----------
class DocumentOut(BaseModel):
    id: str
    filename: str
    content_type: Optional[str]
    size_bytes: int
    chunk_count: int
    status: str
    summary: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    session_id: str
    message: str
    document_ids: Optional[list[str]] = None  # restrict search to these docs if provided


class ChatSource(BaseModel):
    document_id: str
    filename: str
    snippet: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    sources: list[ChatSource]
    ai_provider: str = "extractive"


# ---------- Workflows ----------
class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    definition: dict[str, Any]  # {"nodes": [...], "edges": [...]}
    is_active: bool = True


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    definition: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class WorkflowOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    is_active: bool
    definition: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowRunOut(BaseModel):
    id: str
    workflow_id: str
    status: str
    trigger_type: Optional[str]
    log: Optional[list[dict[str, Any]]]
    started_at: datetime
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True


# ---------- Analytics ----------
class DashboardStats(BaseModel):
    total_documents: int
    total_workflows: int
    active_workflows: int
    total_workflow_runs: int
    successful_runs: int
    failed_runs: int
    runs_last_7_days: list[dict[str, Any]]
