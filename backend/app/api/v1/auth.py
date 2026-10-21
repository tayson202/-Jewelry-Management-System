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
    
    token = create_access_token(subject=user.id, role=user.role)
    return Token(
        access_token=token,
        token_type="bearer",
        role=user.role,
        full_name=user.full_name
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

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
