from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.models import (
    User, Customer, Product, Ticket, Technician, Appointment,
    Estimate, Invoice, TicketTimelineEvent, CustomerChatMessage,
    RepairRecord, ResolutionOTP, Notification
)
from app.schemas import (
    TicketCreate, EstimateReview, AppointmentReschedule,
    TicketRatingCreate, ChatMessageCreate, InvoicePay
)
from app.services.auth_service import get_current_user
from app.services.hindsight_service import hindsight_service
from app.services.groq_service import groq_service
from app.services.classifier_service import classify_issue, validate_complaint_input
from app.services.repeat_detector import check_is_repeat_ticket
from app.services.ticket_state_machine import transition_ticket_status
from app.services.notification_service import notification_service

router = APIRouter(prefix="/api/portal", tags=["portal"])

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

    clean_email = user.email.lower().strip()
    cust = db.query(Customer).filter((Customer.email == clean_email) | (Customer.phone == user.phone)).first()
    if not cust:
        cust = Customer(
            name=user.name,
            phone=user.phone or f"+1-555-CUST-{user.id}",
            email=clean_email,
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
            "is_repeat": bool(t.is_repeat),
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

        if t.status in ["RESOLVED", "CANCELLED", "Resolved", "Closed"]:
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

    events = (
        db.query(TicketTimelineEvent)
        .filter(TicketTimelineEvent.ticket_id == ticket.id)
        .order_by(TicketTimelineEvent.created_at.asc())
        .all()
    )

    estimate = db.query(Estimate).filter(Estimate.ticket_id == ticket.id).order_by(Estimate.created_at.desc()).first()
    invoice = db.query(Invoice).filter(Invoice.ticket_id == ticket.id).order_by(Invoice.created_at.desc()).first()
    appointment = db.query(Appointment).filter(Appointment.ticket_id == ticket.id).order_by(Appointment.scheduled_at.desc()).first()
    repairs = [
        {"action": r.action, "outcome": r.outcome, "confirmed_at": r.confirmed_at}
        for r in ticket.repairs
    ]

    stage_keys = [s["key"] for s in TRACKING_STAGES]
    current_stage_idx = stage_keys.index(ticket.stage) if ticket.stage in stage_keys else 0

    # Reveal OTP only to the customer when in PENDING_VERIFICATION
    customer_otp = None
    if ticket.status == "PENDING_VERIFICATION":
        # Customer notification containing the OTP
        notif = (
            db.query(ResolutionOTP)
            .filter(ResolutionOTP.ticket_id == ticket.id, ResolutionOTP.used == False)
            .order_by(ResolutionOTP.created_at.desc())
            .first()
        )
        if notif:
            # Look up recent OTP notification sent to customer
            customer_notif = (
                db.query(Notification)
                .filter(
                    Notification.user_id == current_user.id,
                    Notification.ticket_id == ticket.id,
                    Notification.type == "OTP_ISSUED"
                )
                .order_by(Notification.created_at.desc())
                .first()
            )
            if customer_notif and "code: " in customer_notif.body:
                code_part = customer_notif.body.split("code: ")[1].split(" ")[0]
                customer_otp = code_part

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
        "is_repeat": bool(ticket.is_repeat),
        "is_reopened": bool(ticket.is_reopened),
        "rating": ticket.rating,
        "feedback": ticket.feedback,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "customer_otp": customer_otp,
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
    try:
        validate_complaint_input(payload.issue_description)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    customer = ensure_customer(current_user, db)

    # Product
    model = payload.model or "Model X"
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
            product_type=payload.product_type or "Washing Machine",
            brand=payload.brand or "Apex Appliances",
            model=model,
            serial_number=f"APX-{model[:1]}-{customer.id:04d}"
        )
        db.add(product)
        db.flush()

    category = payload.issue_category
    if not category or category == "General operational issue":
        category = await classify_issue(payload.issue_description, product.product_type, model)

    is_repeat, prior_ticket, repeat_reason = check_is_repeat_ticket(
        db=db,
        customer_id=customer.id,
        product_id=product.id,
        issue_category=category,
        issue_description=payload.issue_description
    )

    ticket = Ticket(
        customer_id=customer.id,
        product_id=product.id,
        issue_description=payload.issue_description,
        issue_category=category,
        status="OPEN",
        stage="complaint_registered",
        priority=payload.priority or ("High" if is_repeat else "Medium"),
        is_repeat=is_repeat,
        is_reopened=is_repeat
    )
    db.add(ticket)
    db.flush()

    ticket.ticket_code = f"TCK-{1000 + ticket.id}"

    ev1 = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="complaint_registered",
        title="Complaint Registered by Customer",
        description=f"Issue logged: '{payload.issue_description}'. Priority: {ticket.priority}." + (f" [Flagged Repeat Issue: {repeat_reason}]" if is_repeat else ""),
        performed_by=customer.name
    )
    db.add(ev1)
    db.commit()
    db.refresh(ticket)

    # Notifications
    notification_service.send_notification(
        db=db,
        user_id=current_user.id,
        ticket_id=ticket.id,
        type="TICKET_CREATED",
        title="Complaint Registered",
        body=f"Your ticket {ticket.ticket_code} for {model} is registered and pending review."
    )
    notification_service.notify_user_by_role(
        db=db,
        role="TECHNICIAN",
        type="TICKET_CREATED",
        title=f"New Ticket: {ticket.ticket_code}",
        body=f"New complaint logged for {model} ({category})." + (" [REPEAT ISSUE]" if is_repeat else ""),
        ticket_id=ticket.id
    )

    return {
        "id": ticket.id,
        "ticket_code": ticket.ticket_code,
        "status": ticket.status,
        "stage": ticket.stage,
        "is_repeat": is_repeat,
        "message": "Complaint successfully registered."
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
        raise HTTPException(status_code=404, detail="No estimate found for this ticket")

    if payload.approved:
        estimate.status = "approved"
        ticket.stage = "repair_in_progress"

        # Auto generate invoice
        invoice = Invoice(
            ticket_id=ticket.id,
            estimate_id=estimate.id,
            invoice_number=f"INV-{ticket.id}-{int(datetime.now().timestamp()) % 10000:04d}",
            amount=estimate.total,
            status="unpaid"
        )
        db.add(invoice)

        ev = TicketTimelineEvent(
            ticket_id=ticket.id,
            stage="estimate_approval",
            title="Estimate Approved by Customer",
            description=f"Quote of ${estimate.total:.2f} approved. Work authorized.",
            performed_by=customer.name
        )
        db.add(ev)
    else:
        estimate.status = "rejected"
        estimate.rejection_reason = payload.rejection_reason or "Customer rejected estimate"
        ticket.stage = "support_review"

        ev = TicketTimelineEvent(
            ticket_id=ticket.id,
            stage="estimate_approval",
            title="Estimate Rejected by Customer",
            description=f"Reason: {estimate.rejection_reason}. Escalated to support.",
            performed_by=customer.name
        )
        db.add(ev)

    db.commit()
    return {"status": estimate.status, "stage": ticket.stage}

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

    scheduled_utc = payload.scheduled_at
    if scheduled_utc.tzinfo is None:
        scheduled_utc = scheduled_utc.replace(tzinfo=timezone.utc)

    # State Machine Transition to RESCHEDULED
    transition_ticket_status(
        db=db,
        ticket=ticket,
        target_status="RESCHEDULED",
        actor=current_user,
        note=f"Customer requested reschedule: {payload.reason or 'Timing conflict'}"
    )

    appointment = db.query(Appointment).filter(Appointment.ticket_id == ticket.id).order_by(Appointment.scheduled_at.desc()).first()
    if appointment:
        appointment.status = "rescheduled"
        appointment.scheduled_at = scheduled_utc
        appointment.reschedule_reason = payload.reason

    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="visit_scheduled",
        title="Visit Rescheduled by Customer",
        description=f"Requested new slot: {scheduled_utc.strftime('%b %d, %Y at %I:%M %p')}. Reason: {payload.reason or 'Timing conflict'}.",
        performed_by=customer.name
    )
    db.add(ev)
    db.commit()
    return {"status": "rescheduled", "new_date": scheduled_utc}

@router.post("/tickets/{ticket_id}/pay")
def pay_invoice(
    ticket_id: int,
    payload: InvoicePay = InvoicePay(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = ensure_customer(current_user, db)
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id, Ticket.customer_id == customer.id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    invoice = db.query(Invoice).filter(Invoice.ticket_id == ticket.id, Invoice.status == "unpaid").first()
    if not invoice:
        raise HTTPException(status_code=400, detail="No unpaid invoice found for this ticket")

    invoice.status = "paid"
    invoice.paid_at = datetime.now(timezone.utc)
    invoice.payment_method = payload.payment_method

    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="resolved",
        title="Invoice Paid Successfully",
        description=f"Payment of ${invoice.amount:.2f} completed via {payload.payment_method}.",
        performed_by=customer.name
    )
    db.add(ev)
    db.commit()
    return {"status": "paid", "amount": invoice.amount}

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

    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="resolved",
        title=f"Customer Rated Service: {payload.rating} Stars",
        description=payload.feedback or "Customer submitted service rating.",
        performed_by=customer.name
    )
    db.add(ev)
    db.commit()
    return {"status": "rated", "rating": ticket.rating}

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

    # Save customer message
    cust_msg = CustomerChatMessage(
        customer_id=customer.id,
        ticket_id=payload.ticket_id,
        sender="customer",
        message=payload.message
    )
    db.add(cust_msg)
    db.commit()

    # Context query for AI
    query = f"Customer inquiry: {payload.message}"
    recall_res = await hindsight_service.recall(db=db, query=query, limit=3)
    memories = recall_res.get("memories", [])
    memory_context = "\n".join([f"- {m['text']}" for m in memories]) if memories else "No specific past repair recall."

    # Groq assistant prompt
    reply_text = (
        f"Thank you for contacting FixLoop Support, {customer.name}. "
        "Our service team is monitoring your repair progress. "
        "Your technician has been dispatched with diagnostics verified against previous model repair histories."
    )
    client = groq_service.get_client()
    if client:
        try:
            resp = await client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are FixLoop's friendly, reassuring Customer Support AI. "
                            "Help the customer understand their repair status or appliance care. "
                            f"Ground your answer in these memory notes: {memory_context}. "
                            "Keep answers concise, polite, and helpful (max 3 sentences)."
                        )
                    },
                    {"role": "user", "content": payload.message}
                ],
                model=groq_service.model,
                temperature=0.3
            )
            reply_text = resp.choices[0].message.content
        except Exception:
            pass

    ai_msg = CustomerChatMessage(
        customer_id=customer.id,
        ticket_id=payload.ticket_id,
        sender="ai",
        message=reply_text
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    return {
        "message_id": ai_msg.id,
        "reply": ai_msg.message,
        "created_at": ai_msg.created_at
    }
