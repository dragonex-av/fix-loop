from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.models import User, Customer, Product, Ticket, Technician, Appointment, Estimate, Invoice, TicketTimelineEvent, CustomerChatMessage, RepairRecord
from app.schemas import TicketCreate, EstimateReview, AppointmentReschedule, TicketRatingCreate, ChatMessageCreate, InvoicePay
from app.services.auth_service import get_current_user, require_roles
from app.services.hindsight_service import hindsight_service
from app.services.groq_service import groq_service

router = APIRouter(prefix="/api/portal", tags=["portal"])

# Customer tracking stage definitions in chronological order
TRACKING_STAGES = [
    {"key": "complaint_registered", "label": "Complaint Registered", "icon": "file-text"},
    {"key": "support_review", "label": "Support Review", "icon": "clipboard-check"},
    {"key": "technician_assigned", "label": "Technician Assigned", "icon": "user-check"},
    {"key": "visit_scheduled", "label": "Visit Scheduled", "icon": "calendar"},
    {"key": "diagnosis_completed", "label": "Diagnosis Completed", "icon": "search"},
    {"key": "estimate_approval", "label": "Estimate Approval", "icon": "dollar-sign"},
    {"key": "repair_in_progress", "label": "Repair In Progress", "icon": "tool"},
    {"key": "quality_check", "label": "Quality Check", "icon": "shield-check"},
    {"key": "resolved", "label": "Resolved & Closed", "icon": "check-circle"}
]

def ensure_customer(user: User, db: Session) -> Customer:
    """Enforce data isolation: maps logged-in user to their specific Customer profile."""
    if user.customer_id:
        cust = db.query(Customer).filter(Customer.id == user.customer_id).first()
        if cust:
            return cust
    
    # If not linked, check by email/phone
    cust = db.query(Customer).filter((Customer.email == user.email) | (Customer.phone == user.phone)).first()
    if not cust:
        cust = Customer(
            name=user.name,
            phone=user.phone or f"+1-555-CUST-{user.id}",
            email=user.email,
            address=user.address
        )
        db.add(cust)
        db.flush()
    user.customer_id = cust.id
    db.commit()
    return cust

@router.get("/my-tickets")
def get_my_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = ensure_customer(current_user, db)
    tickets = db.query(Ticket).filter(Ticket.customer_id == customer.id).order_by(Ticket.created_at.desc()).all()
    
    active_repairs = []
    past_services = []

    for t in tickets:
        tech = t.technician
        appointment = db.query(Appointment).filter(Appointment.ticket_id == t.id).order_by(Appointment.scheduled_at.desc()).first()
        estimate = db.query(Estimate).filter(Estimate.ticket_id == t.id).order_by(Estimate.created_at.desc()).first()
        invoice = db.query(Invoice).filter(Invoice.ticket_id == t.id).first()

        item = {
            "id": t.id,
            "ticket_code": t.ticket_code or f"TCK-{t.id}",
            "product_model": t.product.model if t.product else "Appliance",
            "product_type": t.product.product_type if t.product else "Appliance",
            "issue_category": t.issue_category,
            "issue_description": t.issue_description,
            "status": t.status,
            "stage": t.stage or "complaint_registered",
            "priority": t.priority,
            "image_url": t.image_url,
            "is_reopened": t.is_reopened,
            "rating": t.rating,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
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
                "total": estimate.total,
                "status": estimate.status,
                "description": estimate.description
            } if estimate else None,
            "invoice": {
                "id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "amount": invoice.amount,
                "status": invoice.status
            } if invoice else None
        }

        if t.status in ["Resolved", "Closed"]:
            past_services.append(item)
        else:
            active_repairs.append(item)

    return {
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "email": customer.email,
            "address": customer.address
        },
        "active_repairs": active_repairs,
        "past_services": past_services,
        "total_active": len(active_repairs),
        "total_completed": len(past_services)
    }

@router.get("/tickets/{ticket_id}")
def get_ticket_tracking_detail(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = ensure_customer(current_user, db)
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id, Ticket.customer_id == customer.id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Service ticket not found or access denied")

    # Tracking timeline events
    events = (
        db.query(TicketTimelineEvent)
        .filter(TicketTimelineEvent.ticket_id == ticket.id)
        .order_by(TicketTimelineEvent.created_at.asc())
        .all()
    )

    # Estimate, Invoice, Appointment, Repairs
    estimate = db.query(Estimate).filter(Estimate.ticket_id == ticket.id).order_by(Estimate.created_at.desc()).first()
    invoice = db.query(Invoice).filter(Invoice.ticket_id == ticket.id).order_by(Invoice.created_at.desc()).first()
    appointment = db.query(Appointment).filter(Appointment.ticket_id == ticket.id).order_by(Appointment.scheduled_at.desc()).first()
    repairs = [
        {"action": r.action, "outcome": r.outcome, "confirmed_at": r.confirmed_at}
        for r in ticket.repairs
    ]

    # Calculate active stage index for Swiggy/Zomato style progress bar
    stage_keys = [s["key"] for s in TRACKING_STAGES]
    current_stage_idx = stage_keys.index(ticket.stage) if ticket.stage in stage_keys else 0

    return {
        "id": ticket.id,
        "ticket_code": ticket.ticket_code or f"TCK-{ticket.id}",
        "product": {
            "model": ticket.product.model,
            "type": ticket.product.product_type,
            "brand": ticket.product.brand,
            "serial": ticket.product.serial_number
        },
        "issue_category": ticket.issue_category,
        "issue_description": ticket.issue_description,
        "status": ticket.status,
        "stage": ticket.stage,
        "current_stage_index": current_stage_idx,
        "all_stages": TRACKING_STAGES,
        "priority": ticket.priority,
        "image_url": ticket.image_url,
        "is_reopened": ticket.is_reopened,
        "rating": ticket.rating,
        "feedback": ticket.feedback,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "technician": {
            "id": ticket.technician.id,
            "name": ticket.technician.name,
            "phone": ticket.technician.phone,
            "rating": ticket.technician.rating,
            "specialization": ticket.technician.specialization
        } if ticket.technician else None,
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
        "repairs": repairs,
        "timeline": [
            {
                "id": ev.id,
                "stage": ev.stage,
                "title": ev.title,
                "description": ev.description,
                "performed_by": ev.performed_by,
                "created_at": ev.created_at
            }
            for ev in events
        ]
    }

@router.post("/tickets")
async def create_customer_ticket(
    payload: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = ensure_customer(current_user, db)

    # 1. Product lookup or create
    model = payload.model or "Model X"
    p_type = payload.product_type or "Washing Machine"
    brand = payload.brand or "Apex Appliances"

    product = (
        db.query(Product)
        .filter(Product.customer_id == customer.id, Product.model == model)
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
        db.flush()

    # 2. Check for repeat complaint
    from app.routers.tickets import normalize_category
    category = payload.issue_category or normalize_category(payload.issue_description)

    prior_tickets_count = (
        db.query(Ticket)
        .filter(Ticket.customer_id == customer.id, Ticket.product_id == product.id)
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

    # Log initial timeline event
    ev1 = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="complaint_registered",
        title="Complaint Registered by Customer",
        description=f"Issue logged: '{payload.issue_description}'. Priority: {ticket.priority}.",
        performed_by=customer.name
    )
    db.add(ev1)
    db.commit()
    db.refresh(ticket)

    # Retain complaint experience in Hindsight
    await hindsight_service.retain(
        db=db,
        entity_type="ticket",
        entity_id=ticket.id,
        content=f"Customer {customer.name} (ID: {customer.id}) reported {category} on {model}: '{payload.issue_description}'. Ticket: {ticket.ticket_code}.",
        metadata={"ticket_code": ticket.ticket_code, "model": model, "is_repeat": is_repeat}
    )

    return {
        "id": ticket.id,
        "ticket_code": ticket.ticket_code,
        "status": ticket.status,
        "stage": ticket.stage,
        "is_repeat": is_repeat,
        "message": "Complaint successfully registered. Assigned to Support Review."
    }

@router.post("/tickets/{ticket_id}/estimate")
def review_estimate(
    ticket_id: int,
    payload: EstimateReview,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = ensure_customer(current_user, db)
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id, Ticket.customer_id == customer.id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    estimate = db.query(Estimate).filter(Estimate.ticket_id == ticket.id).order_by(Estimate.created_at.desc()).first()
    if not estimate:
        raise HTTPException(status_code=400, detail="No estimate generated for this ticket yet")

    estimate.status = payload.status
    if payload.status == "approved":
        ticket.stage = "repair_in_progress"
        ticket.status = "In Progress"
        
        # Create invoice
        inv_num = f"INV-{ticket.id}-{int(datetime.now().timestamp()) % 10000}"
        invoice = Invoice(
            ticket_id=ticket.id,
            estimate_id=estimate.id,
            invoice_number=inv_num,
            amount=estimate.total,
            status="unpaid"
        )
        db.add(invoice)

        ev = TicketTimelineEvent(
            ticket_id=ticket.id,
            stage="estimate_approval",
            title="Estimate Approved by Customer",
            description=f"Customer approved repair cost of ${estimate.total:.2f}. Proceeding with repair.",
            performed_by=customer.name
        )
        db.add(ev)
    else:
        estimate.rejection_reason = payload.rejection_reason
        ev = TicketTimelineEvent(
            ticket_id=ticket.id,
            stage="estimate_approval",
            title="Estimate Rejected by Customer",
            description=f"Reason: {payload.rejection_reason or 'Customer declined repair costs'}.",
            performed_by=customer.name
        )
        db.add(ev)

    db.commit()
    return {"status": estimate.status, "message": f"Estimate successfully {payload.status}."}

@router.post("/tickets/{ticket_id}/appointment/reschedule")
def reschedule_appointment(
    ticket_id: int,
    payload: AppointmentReschedule,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = ensure_customer(current_user, db)
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id, Ticket.customer_id == customer.id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    appointment = db.query(Appointment).filter(Appointment.ticket_id == ticket.id).order_by(Appointment.scheduled_at.desc()).first()
    if not appointment:
        raise HTTPException(status_code=400, detail="No active appointment found to reschedule")

    appointment.scheduled_at = payload.scheduled_at
    appointment.status = "rescheduled"
    appointment.notes = f"Rescheduled by customer. Reason: {payload.reason or 'Customer request'}."

    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="visit_scheduled",
        title="Technician Appointment Rescheduled",
        description=f"New appointment set for {payload.scheduled_at.strftime('%b %d, %Y at %I:%M %p')}.",
        performed_by=customer.name
    )
    db.add(ev)
    db.commit()
    return {"status": "rescheduled", "new_time": appointment.scheduled_at}

@router.post("/tickets/{ticket_id}/pay")
def pay_invoice(
    ticket_id: int,
    payload: InvoicePay,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = ensure_customer(current_user, db)
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id, Ticket.customer_id == customer.id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    invoice = db.query(Invoice).filter(Invoice.ticket_id == ticket.id).order_by(Invoice.created_at.desc()).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice.status = "paid"
    invoice.paid_at = datetime.now(timezone.utc)
    invoice.payment_method = payload.payment_method

    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="resolved",
        title="Payment Received",
        description=f"Payment of ${invoice.amount:.2f} processed via {payload.payment_method}.",
        performed_by="Customer"
    )
    db.add(ev)
    db.commit()
    return {"status": "paid", "invoice_number": invoice.invoice_number, "amount": invoice.amount}

@router.post("/tickets/{ticket_id}/rate")
def rate_service(
    ticket_id: int,
    payload: TicketRatingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = ensure_customer(current_user, db)
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id, Ticket.customer_id == customer.id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.rating = payload.rating
    ticket.feedback = payload.feedback

    # Update technician average rating if assigned
    if ticket.technician:
        all_tech_ratings = (
            db.query(Ticket.rating)
            .filter(Ticket.technician_id == ticket.technician.id, Ticket.rating.isnot(None))
            .all()
        )
        if all_tech_ratings:
            scores = [r[0] for r in all_tech_ratings]
            ticket.technician.rating = round(sum(scores) / len(scores), 1)

    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="resolved",
        title="Customer Rating & Feedback Submitted",
        description=f"Rated {payload.rating}/5 stars. Feedback: '{payload.feedback or 'No comment'}'.",
        performed_by=customer.name
    )
    db.add(ev)
    db.commit()
    return {"rating": ticket.rating, "feedback": ticket.feedback}

@router.post("/tickets/{ticket_id}/reopen")
async def reopen_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = ensure_customer(current_user, db)
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id, Ticket.customer_id == customer.id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = "Reopened"
    ticket.stage = "support_review"
    ticket.is_reopened = True
    ticket.updated_at = datetime.now(timezone.utc)

    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="support_review",
        title="Ticket Reopened by Customer",
        description="Customer indicated that the same problem recurred. Priority escalated to High.",
        performed_by=customer.name
    )
    db.add(ev)
    db.commit()

    # Retain the recurrence event in Hindsight
    await hindsight_service.retain(
        db=db,
        entity_type="ticket_recurrence",
        entity_id=ticket.id,
        content=f"REPEAT COMPLAINT REOPENED: Customer {customer.name} reopened ticket {ticket.ticket_code} for {ticket.product.model}. Previous fix did not hold permanently.",
        metadata={"ticket_code": ticket.ticket_code, "model": ticket.product.model, "reopened": True}
    )

    return {"status": ticket.status, "stage": ticket.stage, "message": "Ticket reopened. Support and engineering alerted."}

# ----------------- Customer AI Support Chat -----------------
@router.get("/chat")
def get_chat_history(
    ticket_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = ensure_customer(current_user, db)
    q = db.query(CustomerChatMessage).filter(CustomerChatMessage.customer_id == customer.id)
    if ticket_id:
        q = q.filter(CustomerChatMessage.ticket_id == ticket_id)
    messages = q.order_by(CustomerChatMessage.created_at.asc()).limit(50).all()
    return [
        {
            "id": m.id,
            "sender": m.sender,
            "message": m.message,
            "ticket_id": m.ticket_id,
            "created_at": m.created_at
        }
        for m in messages
    ]

@router.post("/chat")
async def send_chat_message(
    payload: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = ensure_customer(current_user, db)
    
    # 1. Save customer's message
    cust_msg = CustomerChatMessage(
        customer_id=customer.id,
        ticket_id=payload.ticket_id,
        sender="customer",
        message=payload.message
    )
    db.add(cust_msg)
    db.commit()

    # 2. Gather customer context (DATA ISOLATION: strictly only this customer's tickets)
    active_tickets = db.query(Ticket).filter(Ticket.customer_id == customer.id).all()
    ticket_summaries = [
        f"{t.ticket_code}: {t.product.brand} {t.product.model} ({t.issue_category}) - Status: {t.status}, Stage: {t.stage}"
        for t in active_tickets
    ]

    # 3. Recall relevant experience from Hindsight
    query = f"{customer.name} {payload.message}"
    recall_res = await hindsight_service.recall(db=db, query=query, limit=3)
    memories = recall_res.get("memories", [])
    memory_text = "\n".join([m.get("text", "") for m in memories])

    # 4. Generate AI response using Groq
    system_prompt = f"""You are the friendly, helpful FixLoop AI Customer Support Assistant.
You are helping customer {customer.name}.
Customer's registered appliances and tickets:
{chr(10).join(ticket_summaries) if ticket_summaries else 'No tickets currently registered.'}

Relevant knowledge from FixLoop memory:
{memory_text if memory_text else 'Standard appliance operations.'}

RULES:
- Be polite, concise, empathetic, and professional.
- Help the customer understand their repair status, scheduled appointment, or safety steps (e.g. turning off main water inlet, power cord safety).
- NEVER disclose other customers' names, tickets, or internal engineering secrets.
- If a technician is assigned, reassure them that our authorized expert is on it.
"""
    ai_reply = "Thank you for reaching out! Your service request has been reviewed, and our operations team is actively coordinating your visit. Please let us know if you need to adjust your schedule."

    if groq_service.is_configured():
        client = groq_service.get_client()
        if client:
            try:
                completion = await client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": payload.message}
                    ],
                    model=groq_service.model,
                    temperature=0.3,
                    max_tokens=250
                )
                ai_reply = completion.choices[0].message.content
            except Exception as e:
                pass

    # Save AI message
    ai_msg = CustomerChatMessage(
        customer_id=customer.id,
        ticket_id=payload.ticket_id,
        sender="ai",
        message=ai_reply
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    return {
        "reply": ai_reply,
        "message_id": ai_msg.id,
        "created_at": ai_msg.created_at
    }
