import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.core.security import hash_password
from app.db.models import AppUser, Cpse

# SQLite in-memory engine for unit tests
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="function")
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    
    # Create test CPSE and users
    cpse = Cpse(code="TEST_CPSE", name="Test CPSE", is_synthetic=True)
    session.add(cpse)
    session.flush()
    
    admin_user = AppUser(
        username="admin",
        password_hash=hash_password("AdminPassword123!"),
        role="SUPER_ADMIN",
        cpse_id=cpse.id
    )
    steward_user = AppUser(
        username="steward",
        password_hash=hash_password("StewardPassword123!"),
        role="DATA_STEWARD",
        cpse_id=cpse.id
    )
    session.add(admin_user)
    session.add(steward_user)
    session.commit()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
