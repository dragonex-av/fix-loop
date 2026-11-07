from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import Ticket, TicketEvent, User

# Single Status Enum
VALID_STATUSES = {
    "OPEN",
    "SCHEDULED",
    "IN_PROGRESS",
    "PENDING_VERIFICATION",
    "RESOLVED",
    "RESCHEDULED",
    "CANCELLED"
}

# Legal status transitions: key = current_status, value = set of allowed next statuses
ALLOWED_TRANSITIONS = {
    "OPEN": {"SCHEDULED", "CANCELLED"},
    "SCHEDULED": {"IN_PROGRESS", "RESCHEDULED", "CANCELLED"},
    "RESCHEDULED": {"SCHEDULED", "IN_PROGRESS", "CANCELLED"},
    "IN_PROGRESS": {"PENDING_VERIFICATION", "CANCELLED"},
    "PENDING_VERIFICATION": {"RESOLVED", "IN_PROGRESS", "CANCELLED"},
    "RESOLVED": set(),  # Terminal state
    "CANCELLED": set()  # Terminal state
}

def transition_ticket_status(
    db: Session,
    ticket: Ticket,
    target_status: str,
    actor: Optional[User] = None,
    note: Optional[str] = None
) -> TicketEvent:
    """
    Enforces the single status state machine:
    OPEN -> SCHEDULED -> IN_PROGRESS -> PENDING_VERIFICATION -> RESOLVED
    (+ RESCHEDULED, CANCELLED).
    Raises HTTPException(409) on illegal move.
    Logs transition into ticket_events table.
    """
    current_status = ticket.status.upper() if ticket.status else "OPEN"
    target_status = target_status.upper()

    if target_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target status '{target_status}'. Must be one of {list(VALID_STATUSES)}"
        )

    allowed_next = ALLOWED_TRANSITIONS.get(current_status, set())
    if target_status not in allowed_next:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Illegal state transition from '{current_status}' to '{target_status}'. Allowed transitions: {list(allowed_next)}"
        )

    # Apply transition
    ticket.status = target_status

    # Record audit event
    actor_id = actor.id if actor else None
    actor_name = actor.name if actor else "System"
    actor_role = actor.role if actor else "SYSTEM"

    event = TicketEvent(
        ticket_id=ticket.id,
        from_status=current_status,
        to_status=target_status,
        actor_id=actor_id,
        actor_name=actor_name,
        actor_role=actor_role,
        note=note or f"Transitioned from {current_status} to {target_status}"
    )
    db.add(event)
    db.commit()
    db.refresh(ticket)
    return event
