import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.models import User, Workspace, WorkspaceMember
from app.models.schemas import GoogleAuthRequest, Token, UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


def _create_personal_workspace(db: Session, user: User) -> None:
    """Every new user gets a personal workspace they own, so documents and
    workflows always have somewhere to live - teammates can be invited into
    it later, or the user can create additional shared workspaces."""
    workspace = Workspace(name=f"{user.full_name}'s Workspace", plan="free")
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner"))
    db.commit()


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        company=payload.company,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _create_personal_workspace(db, user)

    token = create_access_token(subject=user.id)
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(subject=user.id)
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/google", response_model=Token)
def google_login(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Verifies a Google Identity Services ID token and logs the user in,
    creating an account (and personal workspace) on first sign-in. Requires
    GOOGLE_CLIENT_ID to be set."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google Sign-In is not configured on this server")

    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token

    try:
        claims = google_id_token.verify_oauth2_token(
            payload.id_token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = claims.get("email")
    full_name = claims.get("name", email)
    if not email:
        raise HTTPException(status_code=400, detail="Google account has no email")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(full_name=full_name, email=email, hashed_password=hash_password(str(uuid.uuid4())))
        db.add(user)
        db.commit()
        db.refresh(user)
        _create_personal_workspace(db, user)

    token = create_access_token(subject=user.id)
    return Token(access_token=token, user=UserOut.model_validate(user))
