from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.db.session import get_db
from app.api.deps import require_role
from app.integration.sap import MockSapAdapter

router = APIRouter(prefix="/integration/sap", tags=["Enterprise Integration (Mock SAP)"])

@router.get("/status")
def get_sap_integration_status(
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["VIEWER", "REVIEWER", "DATA_STEWARD", "SUPER_ADMIN"]))
):
    """
    Returns the current status of the Mock SAP S/4HANA enterprise integration adapter.
    """
    return MockSapAdapter.get_status(db)

@router.post("/sync", status_code=status.HTTP_200_OK)
def trigger_sap_synchronization(
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["DATA_STEWARD", "SUPER_ADMIN"]))
):
    """
    Triggers an outbound synchronization of active National Materials to the mock SAP ERP material master.
    Strictly enforces SAP 40-character description constraints and generates RFC/BAPI payloads.
    """
    result = MockSapAdapter.sync_national_materials(db, actor_id=current_user.id)
    return result

@router.get("/materials")
def list_sap_mock_materials(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["VIEWER", "REVIEWER", "DATA_STEWARD", "SUPER_ADMIN"]))
):
    """
    Returns paginated list of synchronized materials inside the simulated SAP material master.
    """
    return MockSapAdapter.list_synced_materials(db, page=page, page_size=page_size)
