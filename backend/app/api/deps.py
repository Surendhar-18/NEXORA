"""
NEXORA API Dependencies — Authentication and Role-Based Access Control (RBAC).
Provides defense-in-depth authorization for all sensitive endpoints.
"""

from typing import Optional, List, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.config import settings
from app.core.security import decode_access_token
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False
)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates JWT Bearer token and returns authenticated User entity.
    If no token is supplied and settings.REQUIRE_AUTH is False, falls back
    to default development identity for backwards compatibility.
    """
    if token:
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid, malformed, or expired authentication token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token missing subject claim.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = db.query(User).filter((User.id == user_id) | (User.username == user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account associated with token no longer exists.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account has been deactivated.",
            )
        
        return user

    # No token provided
    if settings.REQUIRE_AUTH:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fallback development principal when REQUIRE_AUTH is False
    dev_user = User(
        id="dev-principal-001",
        username="operator",
        email="operator@nexora.local",
        role=UserRole.ADMIN,
        is_active=True
    )
    return dev_user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensures authenticated user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )
    return current_user


def require_role(allowed_roles: List[str]) -> Callable[[User], User]:
    """
    Factory creating a FastAPI dependency that verifies the principal
    possesses one of the specified allowed roles.
    """
    def role_verifier(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied: Operation requires one of roles {allowed_roles}. "
                    f"Your current role is '{current_user.role}'."
                )
            )
        return current_user
    
    return role_verifier


# Pre-configured role dependencies
require_admin = require_role([UserRole.ADMIN])
require_operator = require_role([UserRole.ADMIN, UserRole.OPERATOR])
require_observer = require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.OBSERVER])
