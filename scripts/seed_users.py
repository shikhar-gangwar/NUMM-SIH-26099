import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath("backend"))

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.db.models import AppUser

def seed_users():
    password = settings.SEED_ADMIN_PASSWORD
    if not password:
        print("ERROR: SEED_ADMIN_PASSWORD environment variable is missing or empty.")
        print("Set SEED_ADMIN_PASSWORD in your .env file or environment before seeding.")
        sys.exit(1)

    db = SessionLocal()
    try:
        # 1. steward_admin (SUPER_ADMIN)
        user = db.query(AppUser).filter_by(username="steward_admin").first()
        hashed_pwd = hash_password(password)

        if user:
            user.password_hash = hashed_pwd
            user.role = "SUPER_ADMIN"
            user.is_active = True
            print("[OK] Updated existing user 'steward_admin' (Role: SUPER_ADMIN).")
        else:
            new_user = AppUser(
                username="steward_admin",
                password_hash=hashed_pwd,
                role="SUPER_ADMIN",
                is_active=True
            )
            db.add(new_user)
            print("[OK] Created new development seed user 'steward_admin' (Role: SUPER_ADMIN).")

        # 2. reviewer_demo (REVIEWER)
        reviewer = db.query(AppUser).filter_by(username="reviewer_demo").first()
        reviewer_pwd = hash_password("NUMM-Demo-Reviewer-2026!")

        if reviewer:
            reviewer.password_hash = reviewer_pwd
            reviewer.role = "REVIEWER"
            reviewer.is_active = True
            print("[OK] Updated existing user 'reviewer_demo' (Role: REVIEWER).")
        else:
            new_reviewer = AppUser(
                username="reviewer_demo",
                password_hash=reviewer_pwd,
                role="REVIEWER",
                is_active=True
            )
            db.add(new_reviewer)
            print("[OK] Created new demo seed user 'reviewer_demo' (Role: REVIEWER).")

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"ERROR: Failed to seed users: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed_users()
