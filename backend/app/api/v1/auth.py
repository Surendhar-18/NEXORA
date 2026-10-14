"""
NEXORA Authentication & Identity Router.
Provides secure token issuance, identity inspection, safe bootstrapping, and operator account lifecycle.
"""

from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.core.rate_limit import check_login_rate_limit, reset_rate_limit
from app.models.user import User, UserRole
from app.models.audit import AuditLog
from app.schemas.user import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    UserCreate,
    UserUpdate,
    BootstrapRequest
)
from app.api.deps import get_current_user, require_admin

router = APIRouter(tags=["Authentication & Identity"])


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Authenticates operator with username and password, issuing a signed JWT Bearer token.
    Protected against credential brute-forcing via IP/username sliding-window rate limiting.
    """
    check_login_rate_limit(request, payload.username)

    user = db.query(User).filter(User.username == payload.username.strip()).first()
    
    # Secure constant-time-like check preventing account enumeration
    if not user or not verify_password(payload.password, user.hashed_password):
        # Audit failed login attempt without recording password
        client_ip = request.client.host if request.client else "unknown"
        db.add(AuditLog(
            actor_id=payload.username.strip() or "anonymous",
            actor_role="anonymous",
            action_type="login_failed",
            entity_type="auth",
            entity_id=payload.username.strip() or "unknown",
            details={"ip": client_ip, "reason": "invalid_credentials"},
            ip_address=client_ip
        ))
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Contact an administrator."
        )

    # Success: reset rate limiter and update login timestamp
    reset_rate_limit(request, payload.username)
    user.last_login_at = datetime.now(timezone.utc)
    
    client_ip = request.client.host if request.client else "unknown"
    db.add(AuditLog(
        actor_id=user.username,
        actor_role=user.role,
        action_type="login_success",
        entity_type="auth",
        entity_id=user.id,
        details={"ip": client_ip},
        ip_address=client_ip
    ))
    db.commit()

    token = create_access_token({
        "sub": user.id,
        "username": user.username,
        "role": user.role
    })

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=UserResponse.model_validate(user)
    )


@router.get("/auth/me", response_model=UserResponse)
def get_current_operator_profile(current_user: User = Depends(get_current_user)):
    """Retrieves profile and permissions of the currently authenticated operator."""
    return UserResponse.model_validate(current_user)


@router.post("/auth/bootstrap", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def bootstrap_administrator(payload: BootstrapRequest, db: Session = Depends(get_db)):
    """
    Initializes the first system administrator.
    Strictly locked: returns HTTP 409 Conflict if any administrator already exists.
    """
    admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()
    if admin_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="System already initialized. An administrator account exists. Bootstrap is locked."
        )
    
    # Check if username or email collision
    existing = db.query(User).filter(
        (User.username == payload.username) | (User.email == payload.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already in use."
        )

    admin = User(
        username=payload.username.strip(),
        email=payload.email.strip().lower(),
        hashed_password=hash_password(payload.password),
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(admin)
    db.flush()

    db.add(AuditLog(
        actor_id=admin.username,
        actor_role=admin.role,
        action_type="admin_bootstrapped",
        entity_type="user",
        entity_id=admin.id,
        details={"username": admin.username, "email": admin.email}
    ))
    db.commit()
    db.refresh(admin)

    return UserResponse.model_validate(admin)


# =============================================================================
# OPERATOR ACCOUNT MANAGEMENT (ADMIN ONLY)
# =============================================================================

@router.get("/users", response_model=List[UserResponse])
@router.get("/auth/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """Lists all operator accounts. Requires Administrator privileges."""
    users = db.query(User).order_by(User.created_at.asc()).all()
    return [UserResponse.model_validate(u) for u in users]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@router.post("/auth/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """Creates a new operator account. Requires Administrator privileges."""
    existing = db.query(User).filter(
        (User.username == payload.username.strip()) | (User.email == payload.email.strip().lower())
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this username or email already exists."
        )

    new_user = User(
        username=payload.username.strip(),
        email=payload.email.strip().lower(),
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=True
    )
    db.add(new_user)
    db.flush()

    db.add(AuditLog(
        actor_id=current_user.username,
        actor_role=current_user.role,
        action_type="user_created",
        entity_type="user",
        entity_id=new_user.id,
        details={"created_username": new_user.username, "assigned_role": new_user.role}
    ))
    db.commit()
    db.refresh(new_user)

    return UserResponse.model_validate(new_user)


@router.put("/users/{user_id}", response_model=UserResponse)
@router.put("/auth/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Updates operator account status, role, or credentials. Requires Administrator privileges.
    Guarantees that the last active administrator cannot be deactivated or demoted.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")

    # Guard against locked-out system: cannot deactivate or demote last active admin
    if user.role == UserRole.ADMIN:
        is_demoting = payload.role is not None and payload.role != UserRole.ADMIN
        is_deactivating = payload.is_active is False
        if is_demoting or is_deactivating:
            active_admin_count = db.query(User).filter(
                User.role == UserRole.ADMIN,
                User.is_active == True
            ).count()
            if active_admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot deactivate or demote the last remaining active administrator."
                )

    if payload.email is not None:
        user.email = payload.email.strip().lower()
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password is not None and payload.password.strip():
        user.hashed_password = hash_password(payload.password.strip())

    db.add(AuditLog(
        actor_id=current_user.username,
        actor_role=current_user.role,
        action_type="user_updated",
        entity_type="user",
        entity_id=user.id,
        details={"target_username": user.username, "updated_fields": list(payload.model_dump(exclude_unset=True).keys())}
    ))
    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}")
@router.delete("/auth/users/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Deactivates or deletes an operator account. Requires Administrator privileges.
    Guarantees that the last active administrator cannot be deleted.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")

    if user.role == UserRole.ADMIN:
        active_admin_count = db.query(User).filter(
            User.role == UserRole.ADMIN,
            User.is_active == True
        ).count()
        if active_admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate or delete the last active administrator."
            )

    username = user.username
    db.delete(user)
    db.add(AuditLog(
        actor_id=current_user.username,
        actor_role=current_user.role,
        action_type="user_deleted",
        entity_type="user",
        entity_id=user_id,
        details={"deleted_username": username}
    ))
    db.commit()
    return {"status": "success", "message": f"User {username} deleted successfully."}
