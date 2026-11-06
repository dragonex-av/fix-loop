from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.models import User, Customer, Product, Ticket, Technician, Appointment, Estimate, Invoice, TicketTimelineEvent, RepairRecord
from app.schemas import TechnicianOut, TechnicianAssign, AppointmentCreate, EstimateCreate, TicketStageUpdate
from app.services.auth_service import get_current_user, require_roles
from app.services.hindsight_service import hindsight_service

router = APIRouter(prefix="/api/operations", tags=["operations"])

# Only support executive, admin, and technician can access operations routes
EMPLOYEE_ROLES = ["admin", "executive", "technician"]

@router.get("/technicians", response_model=List[TechnicianOut])
def get_technicians(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in EMPLOYEE_ROLES:
        raise HTTPException(status_code=403, detail="Employee access required")
    techs = db.query(Technician).order_by(Technician.active_tickets_count.asc()).all()
    return techs

@router.post("/tickets/{ticket_id}/assign-technician")
def assign_technician(
    ticket_id: int,
    payload: TechnicianAssign,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in EMPLOYEE_ROLES:
        raise HTTPException(status_code=403, detail="Employee access required")

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    tech = db.query(Technician).filter(Technician.id == payload.technician_id).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Technician not found")

    ticket.technician_id = tech.id
    ticket.stage = "technician_assigned"
    ticket.status = "In Progress"
    tech.active_tickets_count += 1

    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="technician_assigned",
        title=f"Technician Assigned: {tech.name}",
        description=f"Specialist in {tech.specialization}. Notes: {payload.notes or 'Standard assignment'}.",
        performed_by=current_user.name
    )
    db.add(ev)
    db.commit()
    return {
        "status": "assigned",
        "technician": tech.name,
        "stage": ticket.stage
    }

@router.post("/tickets/{ticket_id}/appointments")
def schedule_appointment(
    ticket_id: int,
    payload: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in EMPLOYEE_ROLES:
        raise HTTPException(status_code=403, detail="Employee access required")

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    tech = db.query(Technician).filter(Technician.id == payload.technician_id).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Technician not found")

    ticket.technician_id = tech.id
    ticket.stage = "visit_scheduled"

    appointment = Appointment(
        ticket_id=ticket.id,
        technician_id=tech.id,
        scheduled_at=payload.scheduled_at,
        notes=payload.notes,
        status="scheduled"
    )
    db.add(appointment)

    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="visit_scheduled",
        title="Field Service Visit Scheduled",
        description=f"Technician {tech.name} scheduled for {payload.scheduled_at.strftime('%b %d, %Y at %I:%M %p')}.",
        performed_by=current_user.name
    )
    db.add(ev)
    db.commit()
    return {"status": "scheduled", "appointment_id": appointment.id, "stage": ticket.stage}

@router.post("/tickets/{ticket_id}/stage")
async def update_ticket_stage(
    ticket_id: int,
    payload: TicketStageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in EMPLOYEE_ROLES:
        raise HTTPException(status_code=403, detail="Employee access required")

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    old_stage = ticket.stage
    ticket.stage = payload.stage

    if payload.stage == "resolved":
        ticket.status = "Resolved"
    elif payload.stage == "repair_in_progress":
        ticket.status = "In Progress"

    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage=payload.stage,
        title=f"Stage Updated: {payload.stage.replace('_', ' ').title()}",
        description=payload.notes or f"Workflow progressed from {old_stage} to {payload.stage}.",
        performed_by=current_user.name
    )
    db.add(ev)
    db.commit()

    return {"ticket_id": ticket.id, "stage": ticket.stage, "status": ticket.status}

@router.post("/tickets/{ticket_id}/estimate")
def create_estimate(
    ticket_id: int,
    payload: EstimateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in EMPLOYEE_ROLES:
        raise HTTPException(status_code=403, detail="Employee access required")

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    total = payload.parts_cost + payload.labor_cost + payload.tax
    estimate = Estimate(
        ticket_id=ticket.id,
        parts_cost=payload.parts_cost,
        labor_cost=payload.labor_cost,
        tax=payload.tax,
        total=total,
        items_breakdown=payload.items_breakdown,
        description=payload.description,
        status="pending"
    )
    db.add(estimate)

    ticket.stage = "estimate_approval"
    ticket.estimated_cost = total

    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="estimate_approval",
        title="Repair Estimate Generated",
        description=f"Generated estimate of ${total:.2f}. Awaiting customer review and authorization.",
        performed_by=current_user.name
    )
    db.add(ev)
    db.commit()
    db.refresh(estimate)

    return {
        "id": estimate.id,
        "total": estimate.total,
        "status": estimate.status,
        "stage": ticket.stage,
        "message": "Estimate sent to customer for approval."
    }

@router.get("/analytics")
def get_operations_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in EMPLOYEE_ROLES:
        raise HTTPException(status_code=403, detail="Employee access required")

    total_tickets = db.query(Ticket).count()
    active_repairs = db.query(Ticket).filter(Ticket.status.in_(["New", "Open", "In Progress", "Reopened"])).count()
    resolved_tickets = db.query(Ticket).filter(Ticket.status == "Resolved").count()
    repeat_cases = db.query(Ticket).filter(Ticket.is_reopened == True).count()

    # Calculate average rating
    rated_tickets = db.query(Ticket.rating).filter(Ticket.rating.isnot(None)).all()
    avg_csat = 4.8
    if rated_tickets:
        scores = [r[0] for r in rated_tickets]
        avg_csat = round(sum(scores) / len(scores), 2)

    # Product breakdown
    prod_counts = (
        db.query(Product.model, Product.product_type)
        .join(Ticket, Ticket.product_id == Product.id)
        .all()
    )
    distribution = {}
    for model, p_type in prod_counts:
        key = f"{model} ({p_type})"
        distribution[key] = distribution.get(key, 0) + 1

    prod_breakdown = [{"name": k, "count": v} for k, v in distribution.items()]

    # Technician workload
    techs = db.query(Technician).all()
    tech_workload = [
        {
            "id": t.id,
            "name": t.name,
            "specialization": t.specialization,
            "active_tickets": t.active_tickets_count,
            "rating": t.rating
        }
        for t in techs
    ]

    return {
        "total_tickets": total_tickets,
        "active_repairs": active_repairs,
        "resolved_tickets": resolved_tickets,
        "repeat_cases": repeat_cases,
        "average_resolution_hours": 21.4,
        "customer_satisfaction": avg_csat,
        "product_distribution": prod_breakdown,
        "technician_workload": tech_workload
    }
