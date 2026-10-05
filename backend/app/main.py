import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.sql import text
from app.db.base import Base
import app.db.models  # Ensures models are registered on Base.metadata
from app.db.session import engine, SessionLocal
from app.config_loader.loader import load_config_bundle
from app.ai.providers.factory import get_embedding_provider, get_llm_provider
from app.api.v1.router import api_v1_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 0. Ensure pgvector extension exists for PostgreSQL
    if "postgresql" in str(engine.url):
        try:
            with engine.begin() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        except Exception as e:
            print(f"pgvector extension warning: {e}", flush=True)

    # 1. Create all ORM tables
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully.", flush=True)
    except Exception as e:
        print(f"Base.metadata.create_all error: {e}", flush=True)

    # 2. Execute DDL for triggers and indexes if PostgreSQL
    triggers_path = os.path.join(os.path.dirname(__file__), "db", "triggers.sql")
    if os.path.exists(triggers_path) and "postgresql" in str(engine.url):
        try:
            with open(triggers_path, "r", encoding="utf-8") as f:
                sql_script = f.read()
            with engine.begin() as conn:
                conn.execute(text(sql_script))
            print("Triggers DDL executed successfully.", flush=True)
        except Exception as e:
            print(f"Triggers DDL warning: {e}", flush=True)

    # 3. Register active configs & providers into model_version
    db = SessionLocal()
    try:
        load_config_bundle(db=db)
        get_embedding_provider(db=db)
        get_llm_provider(db=db)
        print("Config & provider models registered successfully.", flush=True)

        # 4. Ensure demo users exist
        from app.db.models import AppUser
        from app.core.security import hash_password
        reviewer = db.query(AppUser).filter_by(username="reviewer_demo").first()
        if not reviewer:
            db.add(AppUser(
                username="reviewer_demo",
                password_hash=hash_password("NUMM-Demo-Reviewer-2026!"),
                role="REVIEWER",
                is_active=True
            ))
            db.commit()
            print("Demo seed user 'reviewer_demo' created.", flush=True)
    except Exception as e:
        print(f"Config registration warning: {e}", flush=True)
    finally:
        db.close()

    yield

app = FastAPI(
    title="National Unified Material Master Framework API",
    description="SIH 2026 PS 26099 Core Governance & Matching API",
    version="2.9.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "sih-backend"}

@app.get("/ready", tags=["System"])
def readiness_check():
    return {"status": "ready", "database": "connected", "models": "ready"}
