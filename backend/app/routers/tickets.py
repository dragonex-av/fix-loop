from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.models import Ticket, Customer, Product, RepairRecord, Technician, Appointment, Estimate, Invoice, TicketTimelineEvent
from app.schemas import TicketCreate, TicketOut, AIAnalysisResponse
from app.services.hindsight_service import hindsight_service
from app.services.analysis_service import analysis_service

router = APIRouter(prefix="/api/tickets", tags=["tickets"])

def normalize_category(issue: str) -> str:
    """Rule-based normalization for MVP"""
    text = issue.lower()
    if any(k in text for k in ["drain", "water leak", "pump", "pipe", "clog"]):
        return "Drainage issue"
    elif any(k in text for k in ["cool", "ice", "frost", "compressor", "freeze"]):
        return "Cooling issue"
    elif any(k in text for k in ["spin", "motor", "noise", "vibrate", "drum"]):
        return "Spin & Motor issue"
    elif any(k in text for k in ["heat", "warm", "thermostat", "element"]):
        return "Heating issue"
    elif any(k in text for k in ["power", "turn on", "dead", "switch"]):
        return "Power & Electrical issue"
    return "General operational issue"

@router.get("")
def get_tickets(
    status: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    q = db.query(Ticket)
    if status:
        q = q.filter(Ticket.status == status)
    if stage:
        q = q.filter(Ticket.stage == stage)
    if category:
        q = q.filter(Ticket.issue_category == category)
    if model:
        q = q.join(Product).filter(Product.model == model)

    tickets = q.order_by(Ticket.created_at.desc()).all()
    results = []
    for t in tickets:
        latest_repair = t.repairs[-1] if t.repairs else None
        tech = t.technician
        results.append({
            "id": t.id,
            "ticket_code": t.ticket_code or f"TCK-{t.id}",
            "customer_id": t.customer_id,
            "customer_name": t.customer.name if t.customer else "Unknown",
            "customer_phone": t.customer.phone if t.customer else "",
            "customer_address": t.customer.address if t.customer else "",
            "product_id": t.product_id,
            "product_model": t.product.model if t.product else "Unknown",
            "product_type": t.product.product_type if t.product else "Unknown",
            "issue_description": t.issue_description,
            "issue_category": t.issue_category,
            "status": t.status,
            "stage": t.stage,
            "priority": t.priority,
            "technician_name": tech.name if tech else "Unassigned",
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "latest_action": latest_repair.action if latest_repair else None,
            "latest_outcome": latest_repair.outcome if latest_repair else None
        })
    return results

@router.post("")
async def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    """
    Creates a new complaint ticket:
    1. Looks up or creates customer
    2. Looks up or creates product
    3. Normalizes category
    4. Saves ticket in DB
    5. Retains the initial complaint experience into Hindsight Cloud
    """
    customer = None
    if payload.customer_id:
        customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    elif payload.customer_phone:
        customer = db.query(Customer).filter(Customer.phone == payload.customer_phone).first()

    if not customer:
        name = payload.customer_name or "New Customer"
        phone = payload.customer_phone or f"+1-555-{int(datetime.now().timestamp()) % 10000:04d}"
        customer = Customer(
            name=name,
            phone=phone,
            email=payload.customer_email,
            address=payload.customer_address
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

    product = None
    if payload.product_id:
        product = db.query(Product).filter(Product.id == payload.product_id).first()
    
    if not product:
        model = payload.model or "Model X"
        p_type = payload.product_type or "Washing Machine"
        brand = payload.brand or "Apex Appliances"
        product = (
            db.query(Product)
            .filter(
                Product.customer_id == customer.id,
                Product.model == model
            )
            .first()
        )
        if not product:
            product = Product(
                customer_id=customer.id,
                product_type=p_type,
                brand=brand,
                model=model,
                serial_number=payload.serial_number or f"SN-{model[:2]}-{customer.id:04d}"
            )
            db.add(product)
            db.commit()
            db.refresh(product)

    category = payload.issue_category or normalize_category(payload.issue_description)

    prior_tickets_count = (
        db.query(Ticket)
        .filter(
            Ticket.customer_id == customer.id,
            Ticket.product_id == product.id
        )
        .count()
    )
    is_repeat = prior_tickets_count > 0
    initial_status = "Reopened" if is_repeat else "New"
    initial_stage = "support_review" if is_repeat else "complaint_registered"

    now = datetime.now(timezone.utc)
    sla_hours = 24 if payload.priority == "High" else 48
    sla = now + timedelta(hours=sla_hours)

    ticket = Ticket(
        customer_id=customer.id,
        product_id=product.id,
        issue_description=payload.issue_description,
        issue_category=category,
        status=initial_status,
        stage=initial_stage,
        priority=payload.priority or "Medium",
        image_url=payload.image_url,
        is_reopened=is_repeat,
        sla_deadline=sla
    )
    db.add(ticket)
    db.flush()

    ticket.ticket_code = f"TCK-{1000 + ticket.id}"
    
    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage=initial_stage,
        title="Complaint Registered",
        description=f"Ticket logged for {product.brand} {product.model}: '{payload.issue_description}'.",
        performed_by="Staff Intake"
    )
    db.add(ev)
    db.commit()
    db.refresh(ticket)

    # Hindsight Retain
    complaint_summary = (
        f"Customer {customer.name} (ID: {customer.id}) reported {category} on {product.brand} {product.model}: "
        f"'{payload.issue_description}' (Ticket: {ticket.ticket_code})"
    )
    retain_res = await hindsight_service.retain(
        db=db,
        entity_type="ticket",
        entity_id=ticket.id,
        content=complaint_summary,
        metadata={
            "ticket_code": ticket.ticket_code,
            "product_model": product.model,
            "category": category,
            "is_repeat": is_repeat
        }
    )

    return {
        "id": ticket.id,
        "ticket_code": ticket.ticket_code,
        "customer_id": customer.id,
        "customer_name": customer.name,
        "product_id": product.id,
        "product_model": product.model,
        "issue_description": ticket.issue_description,
        "issue_category": ticket.issue_category,
        "status": ticket.status,
        "stage": ticket.stage,
        "priority": ticket.priority,
        "created_at": ticket.created_at,
        "is_repeat": is_repeat,
        "hindsight_retain_status": retain_res.get("status")
    }

@router.get("/{ticket_id}")
def get_ticket_detail(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    repairs = [
        {
            "id": r.id,
            "action": r.action,
            "outcome": r.outcome,
            "technician_notes": r.technician_notes,
            "confirmed_by": r.confirmed_by,
            "confirmed_at": r.confirmed_at,
            "created_at": r.created_at
        }
        for r in ticket.repairs
    ]

    followups = [
        {
            "id": f.id,
            "promised_at": f.promised_at,
            "owner": f.owner,
            "status": f.status,
            "notes": f.notes,
            "completed_at": f.completed_at
        }
        for f in ticket.followups
    ]

    tech = ticket.technician
    appointment = db.query(Appointment).filter(Appointment.ticket_id == ticket.id).order_by(Appointment.scheduled_at.desc()).first()
    estimate = db.query(Estimate).filter(Estimate.ticket_id == ticket.id).order_by(Estimate.created_at.desc()).first()
    invoice = db.query(Invoice).filter(Invoice.ticket_id == ticket.id).order_by(Invoice.created_at.desc()).first()
    timeline = db.query(TicketTimelineEvent).filter(TicketTimelineEvent.ticket_id == ticket.id).order_by(TicketTimelineEvent.created_at.asc()).all()

    return {
        "id": ticket.id,
        "ticket_code": ticket.ticket_code or f"TCK-{ticket.id}",
        "customer": {
            "id": ticket.customer.id,
            "name": ticket.customer.name,
            "phone": ticket.customer.phone,
            "email": ticket.customer.email,
            "address": ticket.customer.address
        },
        "product": {
            "id": ticket.product.id,
            "product_type": ticket.product.product_type,
            "brand": ticket.product.brand,
            "model": ticket.product.model,
            "serial_number": ticket.product.serial_number
        },
        "technician": {
            "id": tech.id,
            "name": tech.name,
            "phone": tech.phone,
            "rating": tech.rating,
            "specialization": tech.specialization
        } if tech else None,
        "appointment": {
            "id": appointment.id,
            "scheduled_at": appointment.scheduled_at,
            "status": appointment.status,
            "notes": appointment.notes
        } if appointment else None,
        "estimate": {
            "id": estimate.id,
            "parts_cost": estimate.parts_cost,
            "labor_cost": estimate.labor_cost,
            "tax": estimate.tax,
            "total": estimate.total,
            "items_breakdown": estimate.items_breakdown,
            "description": estimate.description,
            "status": estimate.status,
            "rejection_reason": estimate.rejection_reason
        } if estimate else None,
        "invoice": {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "amount": invoice.amount,
            "status": invoice.status,
            "payment_method": invoice.payment_method,
            "paid_at": invoice.paid_at
        } if invoice else None,
        "issue_description": ticket.issue_description,
        "issue_category": ticket.issue_category,
        "status": ticket.status,
        "stage": ticket.stage or "complaint_registered",
        "priority": ticket.priority,
        "image_url": ticket.image_url,
        "is_reopened": ticket.is_reopened,
        "rating": ticket.rating,
        "feedback": ticket.feedback,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "repairs": repairs,
        "followups": followups,
        "timeline": [
            {
                "id": ev.id,
                "stage": ev.stage,
                "title": ev.title,
                "description": ev.description,
                "performed_by": ev.performed_by,
                "created_at": ev.created_at
            }
            for ev in timeline
        ]
    }

@router.post("/{ticket_id}/analyze", response_model=AIAnalysisResponse)
async def analyze_ticket_case(ticket_id: int, db: Session = Depends(get_db)):
    """
    Triggers the Hindsight Recall + Groq Reasoning Loop for a ticket.
    """
    try:
        result = await analysis_service.analyze_ticket(ticket_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
