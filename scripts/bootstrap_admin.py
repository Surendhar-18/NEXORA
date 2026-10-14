"""
NEXORA - Administrator Account Bootstrap Utility.
Safely initializes the first administrative account.
Enforces security guarantees:
1. Refuses to overwrite an existing administrator.
2. Hashes password using bcrypt before persisting.
3. Does not output or log sensitive passwords.
"""

import sys
import argparse
import getpass
from typing import Optional
from pathlib import Path

# Add backend directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal, Base, engine
from app.models.user import User, UserRole
from app.core.security import hash_password
from app.models.audit import AuditLog


def bootstrap_admin(username: str, email: str, password: Optional[str] = None):
    print("=" * 60)
    print("NEXORA - ADMINISTRATOR BOOTSTRAP")
    print("=" * 60)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if an admin already exists
        existing_admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if existing_admin:
            print(f"FAILED: An active administrator already exists ('{existing_admin.username}').", file=sys.stderr)
            print("For security reasons, bootstrap cannot overwrite existing administrators.", file=sys.stderr)
            sys.exit(1)

        # Prompt for password if not supplied
        if not password:
            while True:
                p1 = getpass.getpass("Enter new administrator password (min 8 chars): ")
                if len(p1) < 8:
                    print("Error: Password must be at least 8 characters.")
                    continue
                p2 = getpass.getpass("Confirm administrator password: ")
                if p1 != p2:
                    print("Error: Passwords do not match.")
                    continue
                password = p1
                break

        # Check username / email collisions
        collision = db.query(User).filter((User.username == username) | (User.email == email)).first()
        if collision:
            print(f"FAILED: User with username '{username}' or email '{email}' already exists.", file=sys.stderr)
            sys.exit(1)

        admin = User(
            username=username.strip(),
            email=email.strip().lower(),
            hashed_password=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        db.flush()

        db.add(AuditLog(
            actor_id=admin.username,
            actor_role=admin.role,
            action_type="admin_bootstrapped_cli",
            entity_type="user",
            entity_id=admin.id,
            details={"username": admin.username, "email": admin.email}
        ))
        db.commit()

        print(f"SUCCESS: Administrator '{admin.username}' created successfully!")
        print("Role: admin")
        print("Email:", admin.email)
        print("System is initialized and ready for secure operations.")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap the initial NEXORA administrator account.")
    parser.add_argument("--username", default="admin", help="Administrator username (default: admin)")
    parser.add_argument("--email", default="admin@nexora.local", help="Administrator email")
    parser.add_argument("--password", help="Administrator password (prompted if omitted)")
    args = parser.parse_args()

    bootstrap_admin(username=args.username, email=args.email, password=args.password)
