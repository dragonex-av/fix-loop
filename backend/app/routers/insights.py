from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.models import PatternAlert
from app.services.pattern_service import pattern_service

router = APIRouter(prefix="/api/insights", tags=["insights"])

@router.get("/patterns")
def get_ripple_effect_patterns(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Returns active Ripple Effect clusters (cross-customer patterns).
    Grounded strictly in SQLite tickets, with underlying cases queryable.
    """
    return pattern_service.get_all_patterns(db)

@router.post("/patterns/{alert_id}/review")
def review_pattern_alert(
    alert_id: int,
    status: str = Body(..., embed=True),  # investigating, dismissed, active
    staff_notes: str = Body("", embed=True),
    db: Session = Depends(get_db)
):
    alert = db.query(PatternAlert).filter(PatternAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = status
    if staff_notes:
        alert.staff_notes = staff_notes
    db.commit()
    return {"status": alert.status, "message": f"Pattern #{alert.id} status updated to {alert.status}."}
