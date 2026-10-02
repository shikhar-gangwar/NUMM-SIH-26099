from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_v1_router

app = FastAPI(
    title="National Unified Material Master Framework API",
    description="SIH 2026 PS 26099 Core Governance & Matching API",
    version="0.1.0"
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
