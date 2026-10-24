import json
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        token_version: int = payload.get("tv", 1)
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if user is None:
        raise credentials_exception
        
    # Enforce active session validity: invalidate old tokens if credentials or permissions changed
    if getattr(user, "token_version", 1) != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked due to security/credential update. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required for this administrative operation"
        )
    return current_user

def require_permission(permission_name: str):
    """
    Granular permission gatekeeper.
    Admins are always granted all operations.
    Employees must possess the explicit permission in their user.permissions JSON array.
    """
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role == "ADMIN":
            return current_user
        
        user_perms = []
        try:
            if current_user.permissions:
                user_perms = json.loads(current_user.permissions)
        except Exception:
            user_perms = []
            
        if permission_name not in user_perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Missing required permission '{permission_name}'"
            )
        return current_user
    return permission_checker
