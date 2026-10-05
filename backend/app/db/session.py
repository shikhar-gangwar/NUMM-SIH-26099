from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
}
if "sqlite" not in settings.DATABASE_URL:
    engine_kwargs.update({
        "pool_size": 25,
        "max_overflow": 50,
        "pool_recycle": 1800,
        "pool_timeout": 30,
    })

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

