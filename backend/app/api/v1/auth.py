from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.rate_limiter import rate_limit_auth
from app.models import User
from app.schemas import LoginRequest, Token, UserResponse, UserCreate
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    # Privileged fields like 'role' or 'id' are deliberately omitted to prevent role-escalation

from datetime import datetime, timezone, timedelta
import json
from app.core.security import verify_password, create_access_token, get_password_hash, verify_pin
from app.schemas import LoginRequest, PinLoginRequest, Token, UserResponse, UserCreate

@router.post("/login", response_model=Token, dependencies=[Depends(rate_limit_auth)])
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    
    # Record last login and reset any PIN failure state
    user.last_login_at = datetime.now(timezone.utc)
    user.failed_pin_attempts = 0
    db.commit()

    token = create_access_token(
        subject=user.id,
        role=user.role,
        token_version=getattr(user, "token_version", 1)
    )
    return Token(
        access_token=token,
        token_type="bearer",
        role=user.role,
        full_name=user.full_name,
        user_id=user.id,
        temp_password_active=getattr(user, "temp_password_active", False)
    )

@router.post("/pin-login", response_model=Token, dependencies=[Depends(rate_limit_auth)])
def pin_login(credentials: PinLoginRequest, db: Session = Depends(get_db)):
    """
    Rapid POS / Workstation PIN login with lockout protection.
    Locks after 5 consecutive failed attempts for 15 minutes.
    """
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect terminal email or PIN",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    # Check lockout
    now = datetime.now(timezone.utc)
    if user.pin_locked_until and user.pin_locked_until.replace(tzinfo=timezone.utc if user.pin_locked_until.tzinfo is None else None) > now:
        remaining_min = int((user.pin_locked_until.replace(tzinfo=timezone.utc if user.pin_locked_until.tzinfo is None else None) - now).total_seconds() / 60) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"PIN terminal locked due to repeated failed attempts. Please retry in {remaining_min} minute(s) or consult an Admin."
        )

    if not user.pin_hash or not verify_pin(credentials.pin, user.pin_hash):
        user.failed_pin_attempts = (user.failed_pin_attempts or 0) + 1
        if user.failed_pin_attempts >= 5:
            user.pin_locked_until = now + timedelta(minutes=15)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect terminal email or PIN",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Success: clear failure counters and log in
    user.failed_pin_attempts = 0
    user.pin_locked_until = None
    user.last_login_at = now
    db.commit()

    token = create_access_token(
        subject=user.id,
        role=user.role,
        token_version=getattr(user, "token_version", 1)
    )
    return Token(
        access_token=token,
        token_type="bearer",
        role=user.role,
        full_name=user.full_name,
        user_id=user.id,
        temp_password_active=getattr(user, "temp_password_active", False)
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    perms = []
    try:
        if current_user.permissions:
            perms = json.loads(current_user.permissions)
    except Exception:
        perms = []
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        pin_configured=bool(current_user.pin_hash),
        permissions=perms,
        temp_password_active=bool(current_user.temp_password_active),
        last_login_at=current_user.last_login_at,
        created_at=current_user.created_at
    )

@router.patch("/profile", response_model=UserResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Blueprint Section 2: Role Escalation Protection.
    Stripping privileged fields from client update payloads.
    Users cannot elevate their own role to ADMIN or alter primary keys.
    """
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip()
    if payload.email is not None:
        # Check uniqueness if changing email
        if payload.email != current_user.email:
            exists = db.query(User).filter(User.email == payload.email).first()
            if exists:
                raise HTTPException(status_code=400, detail="Email is already in use by another user.")
            current_user.email = payload.email

    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/register", response_model=UserResponse, dependencies=[Depends(rate_limit_auth)])
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # Safe default: public registrations are strictly assigned EMPLOYEE role (no auto-admin)
    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role="EMPLOYEE"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
