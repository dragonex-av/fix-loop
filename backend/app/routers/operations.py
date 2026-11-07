from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.models import (
    User, Customer, Product, Ticket, Technician, Appointment,
    Estimate, Invoice, TicketTimelineEvent, RepairRecord
)
from app.schemas import TechnicianOut, TechnicianAssign, AppointmentCreate, EstimateCreate
from app.services.auth_service import get_current_user, require_roles, normalize_role
from app.services.ticket_state_machine import transition_ticket_status

router = APIRouter(prefix="/api/operations", tags=["operations"])

@router.get("/technicians", response_model=List[TechnicianOut])
def get_technicians(
    current_user: User = Depends(require_roles(["ADMIN", "TECHNICIAN"])),
    db: Session = Depends(get_db)
):
    techs = db.query(Technician).order_by(Technician.active_tickets_count.asc()).all()
    return techs

@router.get("/technician-dashboard")
def get_technician_dashboard(
    current_user: User = Depends(require_roles(["TECHNICIAN", "ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Technician dashboard view:
    - Today's schedule
    - Assigned queue
    - Pending verifications
    """
    tech = current_user.technician_profile
    tech_id = tech.id if tech else None

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    # 1. Today's appointments
    appt_q = db.query(Appointment).filter(
        Appointment.status.in_(["scheduled", "rescheduled"]),
        Appointment.scheduled_at >= today_start,
        Appointment.scheduled_at < today_end
    )
    if tech_id:
        appt_q = appt_q.filter(Appointment.technician_id == tech_id)
    today_appointments = []
    for a in appt_q.order_by(Appointment.scheduled_at.asc()).all():
        t = a.ticket
        today_appointments.append({
            "id": a.id,
            "ticket_id": a.ticket_id,
            "ticket_code": t.ticket_code if t else f"TCK-{a.ticket_id}",
            "customer_name": t.customer.name if t and t.customer else "Customer",
            "customer_phone": t.customer.phone if t and t.customer else "",
            "customer_address": t.customer.address if t and t.customer else "",
            "product": f"{t.product.brand} {t.product.model}" if t and t.product else "Appliance",
            "scheduled_at": a.scheduled_at,
            "notes": a.notes
        })

    # 2. Assigned queue
    assigned_q = db.query(Ticket).filter(
        Ticket.status.in_(["OPEN", "SCHEDULED", "IN_PROGRESS", "RESCHEDULED"])
    )
    if tech_id:
        assigned_q = assigned_q.filter((Ticket.technician_id == tech_id) | (Ticket.technician_id.is_(None)))
    assigned_queue = []
    for t in assigned_q.order_by(Ticket.created_at.desc()).all():
        assigned_queue.append({
            "id": t.id,
            "ticket_code": t.ticket_code or f"TCK-{t.id}",
            "customer_name": t.customer.name if t.customer else "Customer",
            "model": t.product.model if t.product else "Appliance",
            "issue_category": t.issue_category,
            "status": t.status,
            "priority": t.priority,
            "is_repeat": bool(t.is_repeat),
            "created_at": t.created_at
        })

    # 3. Pending verifications (awaiting customer OTP)
    pv_q = db.query(Ticket).filter(Ticket.status == "PENDING_VERIFICATION")
    if tech_id:
        pv_q = pv_q.filter(Ticket.technician_id == tech_id)
    pending_verifications = []
    for t in pv_q.order_by(Ticket.updated_at.desc()).all():
        pending_verifications.append({
            "id": t.id,
            "ticket_code": t.ticket_code or f"TCK-{t.id}",
            "customer_name": t.customer.name if t.customer else "Customer",
            "customer_phone": t.customer.phone if t.customer else "",
            "model": t.product.model if t.product else "Appliance",
            "issue_category": t.issue_category,
            "updated_at": t.updated_at
        })

    return {
        "today_schedule": today_appointments,
        "assigned_queue": assigned_queue,
        "pending_verifications": pending_verifications
    }

@router.post("/tickets/{ticket_id}/assign-technician")
def assign_technician(
    ticket_id: int,
    payload: TechnicianAssign,
    current_user: User = Depends(require_roles(["ADMIN", "TECHNICIAN"])),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    tech = db.query(Technician).filter(Technician.id == payload.technician_id).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Technician not found")

    ticket.technician_id = tech.id
    ticket.stage = "technician_assigned"
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

@router.post("/tickets/{ticket_id}/estimate")
def create_estimate(
    ticket_id: int,
    payload: EstimateCreate,
    current_user: User = Depends(require_roles(["ADMIN", "TECHNICIAN"])),
    db: Session = Depends(get_db)
):
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
    current_user: User = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    total_tickets = db.query(Ticket).count()
    active_repairs = db.query(Ticket).filter(
        Ticket.status.in_(["OPEN", "SCHEDULED", "IN_PROGRESS", "PENDING_VERIFICATION", "RESCHEDULED"])
    ).count()
    resolved_tickets = db.query(Ticket).filter(Ticket.status == "RESOLVED").count()
    repeat_cases = db.query(Ticket).filter(Ticket.is_repeat == True).count()

    rated_tickets = db.query(Ticket.rating).filter(Ticket.rating.isnot(None)).all()
    avg_csat = 4.8
    if rated_tickets:
        scores = [r[0] for r in rated_tickets]
        avg_csat = round(sum(scores) / len(scores), 2)

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
        "technician_workload": tech_workload
    }
