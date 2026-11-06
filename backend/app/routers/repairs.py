from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.database import get_db
from app.models import Ticket, RepairRecord
from app.schemas import RepairCreate, RepairOut
from app.services.hindsight_service import hindsight_service

router = APIRouter(prefix="/api/tickets", tags=["repairs"])

@router.post("/{ticket_id}/repairs", response_model=RepairOut)
async def record_repair_outcome(ticket_id: int, payload: RepairCreate, db: Session = Depends(get_db)):
    """
    Authorized staff/technician records the physical repair action and its confirmed outcome.
    Valid outcomes: 'successful', 'temporary', 'unsuccessful', 'pending'.
    
    Upon confirmation, this experience is retained into Hindsight Cloud so the
    entire organization's collective intelligence learns from it.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    now = datetime.now(timezone.utc)
    is_confirmed = payload.outcome in ["successful", "temporary", "unsuccessful"]

    repair = RepairRecord(
        ticket_id=ticket.id,
        action=payload.action,
        outcome=payload.outcome,
        technician_notes=payload.technician_notes,
        confirmed_by=payload.confirmed_by if is_confirmed else None,
        confirmed_at=now if is_confirmed else None
    )
    db.add(repair)

    # Update ticket status accordingly
    if payload.outcome == "successful":
        ticket.status = "Resolved"
    elif payload.outcome in ["temporary", "unsuccessful"]:
        ticket.status = "In Progress"
    
    db.commit()
    db.refresh(repair)

    # If staff confirmed the outcome, retain this valuable experience in Hindsight
    if is_confirmed:
        outcome_exp_text = (
            f"REPAIR EXPERIENCE for {ticket.product.model} ({ticket.issue_category}): "
            f"Action performed: '{payload.action}'. Confirmed outcome: '{payload.outcome}'. "
            f"Technician notes: '{payload.technician_notes or 'None'}'. "
            f"Original complaint: '{ticket.issue_description}'. Ticket: {ticket.ticket_code or ticket.id}."
        )
        await hindsight_service.retain(
            db=db,
            entity_type="repair",
            entity_id=repair.id,
            content=outcome_exp_text,
            metadata={
                "ticket_code": ticket.ticket_code or f"TCK-{ticket.id}",
                "product_model": ticket.product.model,
                "category": ticket.issue_category,
                "action": payload.action,
                "outcome": payload.outcome,
                "confirmed_by": payload.confirmed_by
            }
        )

    return repair
