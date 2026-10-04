from fastapi import APIRouter
from app.api.v1 import auth, meta, audit, imports, matching, reviews, national, analytics, exports, materials, integration

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth.router)
api_v1_router.include_router(meta.router)
api_v1_router.include_router(audit.router)
api_v1_router.include_router(imports.router)
api_v1_router.include_router(matching.router)
api_v1_router.include_router(reviews.router)
api_v1_router.include_router(national.router)
api_v1_router.include_router(analytics.router)
api_v1_router.include_router(exports.router)
api_v1_router.include_router(materials.router)
api_v1_router.include_router(integration.router)


