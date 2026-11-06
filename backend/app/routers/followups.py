from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Dict, Any
from app.database import get_db
from app.models import Followup, Ticket
from app.schemas import FollowupCreate, FollowupUpdate
from app.services.followup_service import followup_service

router = APIRouter(prefix="/api/followups", tags=["followups"])

@router.get("")
def get_followup_queue(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    return followup_service.get_queue(db)

@router.post("")
def create_followup(payload: FollowupCreate, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == payload.ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    followup = Followup(
        customer_id=ticket.customer_id,
        ticket_id=ticket.id,
        promised_at=payload.promised_at,
        owner=payload.owner,
        status="upcoming",
        notes=payload.notes
    )
    db.add(followup)
    db.commit()
    db.refresh(followup)
    return followup

@router.patch("/{followup_id}")
def update_followup(followup_id: int, payload: FollowupUpdate, db: Session = Depends(get_db)):
    followup = db.query(Followup).filter(Followup.id == followup_id).first()
    if not followup:
        raise HTTPException(status_code=404, detail="Followup commitment not found")

    if payload.status:
        followup.status = payload.status
        if payload.status == "completed":
            followup.completed_at = datetime.now(timezone.utc)
    if payload.notes is not None:
        followup.notes = payload.notes

    db.commit()
    db.refresh(followup)
    return followup
