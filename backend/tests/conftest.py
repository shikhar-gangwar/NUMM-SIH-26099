import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import get_db
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
    
    import secrets
    test_pwd = secrets.token_urlsafe(16)
    admin_user = AppUser(
        username="admin",
        password_hash=hash_password(test_pwd),
        role="SUPER_ADMIN",
        cpse_id=cpse.id
    )
    steward_user = AppUser(
        username="steward",
        password_hash=hash_password(test_pwd),
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

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def sample_user(db_session):
    return db_session.query(AppUser).filter_by(username="admin").first()

@pytest.fixture(scope="function")
def auth_headers(client, sample_user):
    from app.core.security import create_access_token
    token = create_access_token({"sub": sample_user.username, "role": sample_user.role})
    return {"Authorization": f"Bearer {token}"}


