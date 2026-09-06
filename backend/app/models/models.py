import uuid
from datetime import datetime

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, JSON,
                         String, Text)
from sqlalchemy.orm import relationship

from app.core.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    company = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="owner", cascade="all, delete-orphan")
    memberships = relationship("WorkspaceMember", back_populates="user", cascade="all, delete-orphan")


class Workspace(Base):
    """A team/organization container. Documents and workflows belong to a
    workspace, not directly to a user, so teammates can share them."""
    __tablename__ = "workspaces"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    plan = Column(String, default="free")  # free | pro
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="workspace", cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="workspace", cascade="all, delete-orphan")


class WorkspaceMember(Base):
    """A user's membership + role within a workspace."""
    __tablename__ = "workspace_members"

    id = Column(String, primary_key=True, default=gen_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    role = Column(String, default="member")  # owner | admin | member
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="memberships")


class Document(Base):
    """An uploaded file that has been chunked + embedded for RAG search."""
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=gen_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)  # who uploaded it
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=True)
    size_bytes = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    status = Column(String, default="processing")  # processing | ready | failed
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="documents")
    workspace = relationship("Workspace", back_populates="documents")


class ChatMessage(Base):
    """A single turn in a document Q&A / RAG chat session."""
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=gen_uuid)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # list of {document_id, filename, snippet}
    created_at = Column(DateTime, default=datetime.utcnow)


class Workflow(Base):
    """A visual automation workflow: trigger node -> one or more action nodes."""
    __tablename__ = "workflows"

    id = Column(String, primary_key=True, default=gen_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)  # who created it
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    definition = Column(JSON, nullable=False)  # {nodes: [...], edges: [...]}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="workflows")
    workspace = relationship("Workspace", back_populates="workflows")
    runs = relationship("WorkflowRun", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowRun(Base):
    """One execution of a workflow, with a per-node log for observability."""
    __tablename__ = "workflow_runs"

    id = Column(String, primary_key=True, default=gen_uuid)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    status = Column(String, default="running")  # running | success | failed
    trigger_type = Column(String, nullable=True)  # manual | schedule | webhook
    log = Column(JSON, nullable=True)  # list of {node_id, status, output, error}
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    workflow = relationship("Workflow", back_populates="runs")
