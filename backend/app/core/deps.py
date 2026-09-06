from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.models import User, WorkspaceMember

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_membership(
    x_workspace_id: str | None = Header(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspaceMember:
    """Resolves which workspace the request applies to, and confirms the user
    belongs to it. Pass `X-Workspace-ID` to target a specific workspace; if
    omitted, the user's first (usually personal) workspace is used."""
    query = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id)
    if x_workspace_id:
        membership = query.filter(WorkspaceMember.workspace_id == x_workspace_id).first()
    else:
        membership = query.order_by(WorkspaceMember.created_at.asc()).first()

    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    return membership


def require_role(*roles: str):
    """Dependency factory: require the current membership to have one of the
    given roles (e.g. require_role("owner", "admin")) for admin-only actions."""

    def _check(membership: WorkspaceMember = Depends(get_current_membership)) -> WorkspaceMember:
        if membership.role not in roles:
            raise HTTPException(status_code=403, detail=f"Requires one of roles: {', '.join(roles)}")
        return membership

    return _check
