from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.models import PatternAlert, User
from app.services.pattern_service import pattern_service
from app.services.auth_service import get_current_user, require_roles
from app.services.notification_service import notification_service

router = APIRouter(prefix="/api/insights", tags=["insights"])

@router.get("/patterns")
def get_ripple_effect_patterns(
    current_user: User = Depends(require_roles(["ADMIN", "TECHNICIAN"])),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Returns active Ripple Effect clusters (cross-customer patterns).
    Grounded strictly in distinct customers per model + issue category.
    """
    return pattern_service.get_all_patterns(db)

@router.post("/patterns/{alert_id}/review")
def review_pattern_alert(
    alert_id: int,
    status: str = Body(..., embed=True),  # investigating, acknowledged, resolved, dismissed, active
    staff_notes: str = Body("", embed=True),
    current_user: User = Depends(require_roles(["ADMIN", "TECHNICIAN"])),
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

@router.post("/patterns/{alert_id}/action")
def take_action_on_pattern(
    alert_id: int,
    action_type: str = Body("engineering_review", embed=True),
    notes: str = Body("", embed=True),
    current_user: User = Depends(require_roles(["ADMIN", "TECHNICIAN"])),
    db: Session = Depends(get_db)
):
    """
    'Take Action' on an alert:
    1. Updates pattern status to 'investigating' / 'acknowledged'
    2. Creates an engineering review task/note
    3. Notifies all ADMIN users
    """
    alert = db.query(PatternAlert).filter(PatternAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "investigating"
    alert.staff_notes = f"Engineering Review Task created by {current_user.name}: {notes or 'Initiated cross-customer component defect analysis.'}"
    db.commit()

    # Notify Admins
    notification_service.notify_user_by_role(
        db=db,
        role="ADMIN",
        type="RIPPLE_ALERT_ACTION",
        title=f"Engineering Review: {alert.product_model}",
        body=f"Action taken on {alert.case_count}-customer cluster for '{alert.issue_category}' by {current_user.name}. Status: Investigating."
    )

    return {
        "status": "investigating",
        "alert_id": alert.id,
        "message": f"Engineering review task created and administrators notified."
    }
