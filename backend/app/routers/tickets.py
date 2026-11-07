from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.models import (
    Ticket, Customer, Product, RepairRecord, Technician,
    Appointment, Estimate, Invoice, TicketTimelineEvent, User, ResolutionOTP
)
from app.schemas import (
    TicketCreate, TicketOut, AIAnalysisResponse, AppointmentCreate,
    AppointmentReschedule, TicketStartWork, ResolutionVerifyRequest,
    ResolutionRejectRequest, TicketCancelRequest
)
from app.services.hindsight_service import hindsight_service
from app.services.analysis_service import analysis_service
from app.services.auth_service import get_current_user, normalize_role
from app.services.classifier_service import classify_issue, validate_complaint_input
from app.services.repeat_detector import check_is_repeat_ticket
from app.services.ticket_state_machine import transition_ticket_status
from app.services.otp_service import generate_resolution_otp, verify_resolution_otp
from app.services.notification_service import notification_service

router = APIRouter(prefix="/api/tickets", tags=["tickets"])

@router.get("")
def get_tickets(
    status: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role = normalize_role(current_user.role)
    q = db.query(Ticket)

    # RBAC Enforcement:
    # CUSTOMER: sees only own tickets
    # TECHNICIAN: sees assigned tickets OR unassigned queue (technician_id is None)
    # ADMIN: sees all tickets
    if role == "CUSTOMER":
        if not current_user.customer_id:
            return []
        q = q.filter(Ticket.customer_id == current_user.customer_id)
    elif role == "TECHNICIAN":
        tech = current_user.technician_profile
        if tech:
            q = q.filter((Ticket.technician_id == tech.id) | (Ticket.technician_id.is_(None)))
        else:
            q = q.filter(Ticket.technician_id.is_(None))

    if status:
        q = q.filter(Ticket.status == status.upper())
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
            "is_repeat": bool(t.is_repeat),
            "is_reopened": bool(t.is_reopened),
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "latest_action": latest_repair.action if latest_repair else None,
            "latest_outcome": latest_repair.outcome if latest_repair else None
        })
    return results

@router.post("")
async def create_ticket(
    payload: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a new complaint ticket:
    1. Validates input text (no gibberish, min 10 chars)
    2. Looks up or creates customer & product
    3. Tiered category classification
    4. Accurate Repeat detection within 30-day window
    5. Saves ticket in DB with status OPEN
    6. Emits notifications and logs timeline event
    """
    # 1. Validation
    try:
        validate_complaint_input(payload.issue_description)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Customer Lookup or Link
    role = normalize_role(current_user.role)
    if role == "CUSTOMER":
        if current_user.customer:
            customer = current_user.customer
        else:
            customer = Customer(
                name=current_user.name,
                phone=current_user.phone or f"+1-555-{current_user.id:04d}",
                email=current_user.email,
                address=current_user.address
            )
            db.add(customer)
            db.flush()
            current_user.customer_id = customer.id
            db.commit()
    else:
        # Operations creating on behalf of customer
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

    # 3. Product Lookup or Create
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
                model=model,
                brand=brand,
                serial_number=payload.serial_number or f"SN-{model[:2]}-{customer.id:04d}"
            )
            db.add(product)
            db.commit()
            db.refresh(product)

    # 4. Tiered Classification
    category = payload.issue_category
    if not category or category == "General operational issue":
        category = await classify_issue(payload.issue_description, product.product_type, product.model)

    # 5. Repeat Detection
    is_repeat, prior_ticket, repeat_reason = check_is_repeat_ticket(
        db=db,
        customer_id=customer.id,
        product_id=product.id,
        issue_category=category,
        issue_description=payload.issue_description
    )

    now = datetime.now(timezone.utc)
    sla_hours = 24 if payload.priority == "High" else 48
    sla = now + timedelta(hours=sla_hours)

    ticket = Ticket(
        customer_id=customer.id,
        product_id=product.id,
        issue_description=payload.issue_description,
        issue_category=category,
        status="OPEN",
        stage="complaint_registered",
        priority=payload.priority or ("High" if is_repeat else "Medium"),
        image_url=payload.image_url,
        is_repeat=is_repeat,
        is_reopened=is_repeat,
        sla_deadline=sla
    )
    db.add(ticket)
    db.flush()

    ticket.ticket_code = f"TCK-{1000 + ticket.id}"

    # Timeline event
    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="complaint_registered",
        title="Complaint Registered",
        description=f"Ticket logged for {product.brand} {product.model}: '{payload.issue_description}'. Priority: {ticket.priority}." + (f" [Flagged Repeat Issue: {repeat_reason}]" if is_repeat else ""),
        performed_by=current_user.name
    )
    db.add(ev)
    db.commit()
    db.refresh(ticket)

    # Notify Customer & Technicians
    notification_service.send_notification(
        db=db,
        user_id=current_user.id,
        ticket_id=ticket.id,
        type="TICKET_CREATED",
        title="Complaint Registered",
        body=f"Your complaint for {product.model} has been registered as {ticket.ticket_code}. A specialist will review it shortly."
    )
    notification_service.notify_user_by_role(
        db=db,
        role="TECHNICIAN",
        type="TICKET_CREATED",
        title=f"New Ticket: {ticket.ticket_code}",
        body=f"New complaint logged for {product.model} ({category})." + (" [REPEAT ISSUE]" if is_repeat else ""),
        ticket_id=ticket.id
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
        "is_repeat": is_repeat
    }

@router.get("/{ticket_id}")
def get_ticket_detail(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # RBAC Isolation
    role = normalize_role(current_user.role)
    if role == "CUSTOMER":
        if ticket.customer_id != current_user.customer_id:
            raise HTTPException(status_code=404, detail="Ticket not found or access denied")
    elif role == "TECHNICIAN":
        tech = current_user.technician_profile
        if tech and ticket.technician_id and ticket.technician_id != tech.id:
            raise HTTPException(status_code=403, detail="Ticket is assigned to another technician")

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
    appointment = (
        db.query(Appointment)
        .filter(Appointment.ticket_id == ticket.id)
        .order_by(Appointment.scheduled_at.desc())
        .first()
    )
    estimate = (
        db.query(Estimate)
        .filter(Estimate.ticket_id == ticket.id)
        .order_by(Estimate.created_at.desc())
        .first()
    )
    invoice = (
        db.query(Invoice)
        .filter(Invoice.ticket_id == ticket.id)
        .order_by(Invoice.created_at.desc())
        .first()
    )
    timeline = (
        db.query(TicketTimelineEvent)
        .filter(TicketTimelineEvent.ticket_id == ticket.id)
        .order_by(TicketTimelineEvent.created_at.asc())
        .all()
    )
    events_audit = (
        ticket.events
    )

    # Customer view of OTP: only customer can see plain OTP if ticket is in PENDING_VERIFICATION
    active_otp = None
    if role in ("CUSTOMER", "ADMIN") and ticket.status == "PENDING_VERIFICATION":
        # Check active OTP record
        otp_rec = (
            db.query(ResolutionOTP)
            .filter(ResolutionOTP.ticket_id == ticket.id, ResolutionOTP.used == False)
            .order_by(ResolutionOTP.created_at.desc())
            .first()
        )
        if otp_rec:
            active_otp = {
                "expires_at": otp_rec.expires_at,
                "attempts_remaining": otp_rec.max_attempts - otp_rec.attempts
            }

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
            "reschedule_reason": appointment.reschedule_reason,
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
        "is_repeat": bool(ticket.is_repeat),
        "is_reopened": bool(ticket.is_reopened),
        "rating": ticket.rating,
        "feedback": ticket.feedback,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "resolved_at": ticket.resolved_at,
        "resolved_by": ticket.resolved_by,
        "active_otp": active_otp,
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
        ],
        "events": [
            {
                "id": ev.id,
                "from_status": ev.from_status,
                "to_status": ev.to_status,
                "actor_name": ev.actor_name,
                "actor_role": ev.actor_role,
                "note": ev.note,
                "created_at": ev.created_at
            }
            for ev in events_audit
        ]
    }

# ----------------- FEATURE 2: Scheduling & State Transitions -----------------
@router.post("/{ticket_id}/schedule")
def schedule_service_visit(
    ticket_id: int,
    payload: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role = normalize_role(current_user.role)
    if role not in ("ADMIN", "TECHNICIAN"):
        raise HTTPException(status_code=403, detail="Technician or Admin access required")

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    tech = db.query(Technician).filter(Technician.id == payload.technician_id).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Technician not found")

    # Validation: visit date not in past
    scheduled_utc = payload.scheduled_at
    if scheduled_utc.tzinfo is None:
        scheduled_utc = scheduled_utc.replace(tzinfo=timezone.utc)
    if scheduled_utc < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Service appointment cannot be scheduled in the past.")

    # Validation: no double-booking per technician (within 2-hour window)
    window_start = scheduled_utc - timedelta(hours=1, minutes=59)
    window_end = scheduled_utc + timedelta(hours=1, minutes=59)
    conflict = (
        db.query(Appointment)
        .filter(
            Appointment.technician_id == tech.id,
            Appointment.ticket_id != ticket.id,
            Appointment.status.in_(["scheduled", "rescheduled"]),
            Appointment.scheduled_at >= window_start,
            Appointment.scheduled_at <= window_end
        )
        .first()
    )
    if conflict:
        raise HTTPException(
            status_code=409,
            detail=f"Technician {tech.name} is already booked at {conflict.scheduled_at.strftime('%Y-%m-%d %H:%M UTC')}. Please select another slot."
        )

    # Assign technician & create appointment
    ticket.technician_id = tech.id
    ticket.stage = "visit_scheduled"

    # State Machine Transition: OPEN -> SCHEDULED (or RESCHEDULED -> SCHEDULED)
    transition_ticket_status(
        db=db,
        ticket=ticket,
        target_status="SCHEDULED",
        actor=current_user,
        note=f"Visit scheduled for {tech.name} at {scheduled_utc.strftime('%b %d, %Y %I:%M %p UTC')}"
    )

    appointment = Appointment(
        ticket_id=ticket.id,
        technician_id=tech.id,
        scheduled_at=scheduled_utc,
        status="scheduled",
        notes=payload.notes
    )
    db.add(appointment)

    # Timeline event
    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="visit_scheduled",
        title="Service Visit Scheduled",
        description=f"Technician {tech.name} confirmed for {scheduled_utc.strftime('%b %d, %Y at %I:%M %p')}.",
        performed_by=current_user.name
    )
    db.add(ev)
    db.commit()

    # Customer notification with date/time/technician name
    if ticket.customer and ticket.customer.user:
        notification_service.send_notification(
            db=db,
            user_id=ticket.customer.user.id,
            ticket_id=ticket.id,
            type="VISIT_SCHEDULED",
            title="Service Visit Scheduled",
            body=f"Technician {tech.name} has scheduled your service visit for {scheduled_utc.strftime('%b %d, %Y at %I:%M %p')}."
        )

    return {"status": "SCHEDULED", "appointment_id": appointment.id, "technician": tech.name}

@router.post("/{ticket_id}/reschedule")
def reschedule_service_visit(
    ticket_id: int,
    payload: AppointmentReschedule,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # State machine transition to RESCHEDULED
    transition_ticket_status(
        db=db,
        ticket=ticket,
        target_status="RESCHEDULED",
        actor=current_user,
        note=f"Visit rescheduled. Reason: {payload.reason or 'Customer request'}."
    )

    scheduled_utc = payload.scheduled_at
    if scheduled_utc.tzinfo is None:
        scheduled_utc = scheduled_utc.replace(tzinfo=timezone.utc)

    appointment = (
        db.query(Appointment)
        .filter(Appointment.ticket_id == ticket.id)
        .order_by(Appointment.scheduled_at.desc())
        .first()
    )
    if appointment:
        appointment.status = "rescheduled"
        appointment.reschedule_reason = payload.reason
        appointment.scheduled_at = scheduled_utc
    else:
        appointment = Appointment(
            ticket_id=ticket.id,
            technician_id=ticket.technician_id or 1,
            scheduled_at=scheduled_utc,
            status="rescheduled",
            reschedule_reason=payload.reason
        )
        db.add(appointment)

    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="visit_scheduled",
        title="Visit Rescheduled",
        description=f"Appointment updated to {scheduled_utc.strftime('%b %d, %Y at %I:%M %p')}. Reason: {payload.reason or 'Slot adjustment'}.",
        performed_by=current_user.name
    )
    db.add(ev)
    db.commit()

    # Notify Customer
    if ticket.customer and ticket.customer.user:
        notification_service.send_notification(
            db=db,
            user_id=ticket.customer.user.id,
            ticket_id=ticket.id,
            type="VISIT_RESCHEDULED",
            title="Service Visit Rescheduled",
            body=f"Your repair appointment has been rescheduled to {scheduled_utc.strftime('%b %d, %Y at %I:%M %p')}."
        )

    return {"status": "RESCHEDULED", "new_date": scheduled_utc}

@router.post("/{ticket_id}/start-work")
def start_ticket_work(
    ticket_id: int,
    payload: TicketStartWork,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role = normalize_role(current_user.role)
    if role not in ("ADMIN", "TECHNICIAN"):
        raise HTTPException(status_code=403, detail="Technician or Admin access required")

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    transition_ticket_status(
        db=db,
        ticket=ticket,
        target_status="IN_PROGRESS",
        actor=current_user,
        note=f"Work started by {current_user.name}. Action: {payload.action}. Parts: {payload.parts_used or 'None'}."
    )
    ticket.stage = "repair_in_progress"

    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="repair_in_progress",
        title="Repair Work In Progress",
        description=f"Technician {current_user.name} started work: {payload.action}." + (f" Parts used: {payload.parts_used}" if payload.parts_used else ""),
        performed_by=current_user.name
    )
    db.add(ev)
    db.commit()

    if ticket.customer and ticket.customer.user:
        notification_service.send_notification(
            db=db,
            user_id=ticket.customer.user.id,
            ticket_id=ticket.id,
            type="WORK_STARTED",
            title="Technician Started Work",
            body=f"Technician has begun repair diagnostics on your {ticket.product.model}."
        )

    return {"status": "IN_PROGRESS", "stage": ticket.stage}

# ----------------- FEATURE 3: Two-Step OTP Resolution -----------------
@router.post("/{ticket_id}/request-resolution")
def request_resolution(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Technician clicks 'Mark as Solved' -> Status transitions to PENDING_VERIFICATION.
    Backend generates a secure 6-digit OTP, stores only the SHA-256 hash.
    OTP is sent ONLY to the customer (in-app notification).
    Never exposed in technician responses.
    """
    role = normalize_role(current_user.role)
    if role not in ("ADMIN", "TECHNICIAN"):
        raise HTTPException(status_code=403, detail="Technician or Admin access required")

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    transition_ticket_status(
        db=db,
        ticket=ticket,
        target_status="PENDING_VERIFICATION",
        actor=current_user,
        note="Technician marked work as completed; awaiting customer OTP verification."
    )
    ticket.stage = "quality_check"

    # Generate OTP
    plain_otp, _ = generate_resolution_otp(db, ticket.id)

    # Log timeline event (WITHOUT the OTP)
    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="quality_check",
        title="Repair Completed — Awaiting Verification",
        description="Technician completed physical repairs. Verification code generated for customer sign-off.",
        performed_by=current_user.name
    )
    db.add(ev)
    db.commit()

    # Deliver OTP ONLY to the customer via notification
    if ticket.customer and ticket.customer.user:
        notification_service.send_notification(
            db=db,
            user_id=ticket.customer.user.id,
            ticket_id=ticket.id,
            type="OTP_ISSUED",
            title="Service Verification Code",
            body=f"Your technician has finished the repair on {ticket.product.model}. Please provide verification code: {plain_otp} to confirm resolution."
        )

    return {
        "status": "PENDING_VERIFICATION",
        "message": "Resolution initiated. Customer has been sent a 6-digit verification code."
    }

@router.post("/{ticket_id}/verify-resolution")
async def verify_resolution(
    ticket_id: int,
    payload: ResolutionVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Technician submits the 6-digit OTP provided by customer.
    On success:
    - Status -> RESOLVED
    - Sets resolved_at & resolved_by
    - Retains confirmed outcome into live Hindsight Cloud
    - Schedules 5-day rescue follow-up
    - Notifies BOTH customer and technician
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.status != "PENDING_VERIFICATION":
        raise HTTPException(status_code=400, detail="Ticket is not pending verification.")

    is_valid, msg = verify_resolution_otp(db, ticket.id, payload.code)
    if not is_valid:
        raise HTTPException(status_code=400, detail=msg)

    # Successful Verification!
    now = datetime.now(timezone.utc)
    transition_ticket_status(
        db=db,
        ticket=ticket,
        target_status="RESOLVED",
        actor=current_user,
        note=f"Verified with customer OTP sign-off by {current_user.name}."
    )
    ticket.stage = "resolved"
    ticket.resolved_at = now
    ticket.resolved_by = current_user.name

    # Create RepairRecord marked as successful if not present
    existing_repair = (
        db.query(RepairRecord)
        .filter(RepairRecord.ticket_id == ticket.id)
        .order_by(RepairRecord.created_at.desc())
        .first()
    )
    if not existing_repair:
        repair = RepairRecord(
            ticket_id=ticket.id,
            action="Verified Component Diagnostics & Part Service",
            outcome="successful",
            technician_notes="Customer verified resolution via OTP sign-off.",
            confirmed_by=current_user.name,
            confirmed_at=now
        )
        db.add(repair)
        db.flush()
    else:
        existing_repair.outcome = "successful"
        existing_repair.confirmed_by = current_user.name
        existing_repair.confirmed_at = now

    # Add Timeline Event
    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="resolved",
        title="Service Ticket Resolved & Closed",
        description="Customer confirmed repair with OTP sign-off. Ticket successfully closed.",
        performed_by="Customer & Technician"
    )
    db.add(ev)

    # Schedule 5-day rescue follow-up
    from app.models import Followup
    followup = Followup(
        customer_id=ticket.customer_id,
        ticket_id=ticket.id,
        promised_at=now + timedelta(days=5),
        owner=current_user.name,
        status="upcoming",
        notes="Post-repair 5-day check-in to confirm permanent resolution."
    )
    db.add(followup)
    db.commit()

    # Retain the confirmed outcome into Hindsight Cloud (exactly ONE retain event)
    outcome_exp_text = (
        f"CONFIRMED REPAIR RESOLUTION for {ticket.product.model} ({ticket.issue_category}): "
        f"Verified action completed and confirmed successful with customer OTP sign-off. "
        f"Resolved by {current_user.name}. Original complaint: '{ticket.issue_description}'. "
        f"Ticket: {ticket.ticket_code}."
    )
    await hindsight_service.retain(
        db=db,
        entity_type="repair_resolution",
        entity_id=ticket.id,
        content=outcome_exp_text,
        metadata={
            "ticket_code": ticket.ticket_code,
            "product_model": ticket.product.model,
            "category": ticket.issue_category,
            "outcome": "successful",
            "verified": True
        }
    )

    # Notify BOTH customer and technician
    if ticket.customer and ticket.customer.user:
        notification_service.send_notification(
            db=db,
            user_id=ticket.customer.user.id,
            ticket_id=ticket.id,
            type="TICKET_RESOLVED",
            title="Repair Resolved & Closed",
            body=f"Your repair for {ticket.product.model} (Ticket {ticket.ticket_code}) has been verified and successfully resolved. Thank you!"
        )
    notification_service.send_notification(
        db=db,
        user_id=current_user.id,
        ticket_id=ticket.id,
        type="TICKET_RESOLVED",
        title=f"Ticket {ticket.ticket_code} Resolved",
        body="Resolution confirmed by customer OTP. Retained into Hindsight experience bank."
    )

    return {
        "status": "RESOLVED",
        "ticket_code": ticket.ticket_code,
        "resolved_at": ticket.resolved_at,
        "message": "Ticket resolved successfully and confirmed outcome retained into Hindsight Cloud."
    }

@router.post("/{ticket_id}/reject-resolution")
def reject_resolution(
    ticket_id: int,
    payload: ResolutionRejectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Customer rejects resolution -> Status reverts to IN_PROGRESS."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.status != "PENDING_VERIFICATION":
        raise HTTPException(status_code=400, detail="Ticket is not pending verification.")

    transition_ticket_status(
        db=db,
        ticket=ticket,
        target_status="IN_PROGRESS",
        actor=current_user,
        note=f"Customer rejected resolution: {payload.reason}"
    )
    ticket.stage = "repair_in_progress"

    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="repair_in_progress",
        title="Resolution Rejected by Customer",
        description=f"Reason: {payload.reason}. Technician to perform further diagnostics.",
        performed_by=current_user.name
    )
    db.add(ev)
    db.commit()

    if ticket.technician and ticket.technician.user_id:
        notification_service.send_notification(
            db=db,
            user_id=ticket.technician.user_id,
            ticket_id=ticket.id,
            type="WORK_STARTED",
            title=f"Verification Rejected: {ticket.ticket_code}",
            body=f"Customer stated issue is not fully resolved: '{payload.reason}'."
        )

    return {"status": "IN_PROGRESS", "message": "Resolution rejected. Ticket returned to In Progress."}

@router.post("/{ticket_id}/cancel")
def cancel_ticket(
    ticket_id: int,
    payload: TicketCancelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    transition_ticket_status(
        db=db,
        ticket=ticket,
        target_status="CANCELLED",
        actor=current_user,
        note=f"Cancelled: {payload.reason}"
    )
    ticket.cancellation_reason = payload.reason
    ticket.cancelled_at = datetime.now(timezone.utc)
    ticket.cancelled_by = current_user.name

    ev = TicketTimelineEvent(
        ticket_id=ticket.id,
        stage="complaint_registered",
        title="Ticket Cancelled",
        description=f"Reason: {payload.reason}",
        performed_by=current_user.name
    )
    db.add(ev)
    db.commit()

    if ticket.customer and ticket.customer.user:
        notification_service.send_notification(
            db=db,
            user_id=ticket.customer.user.id,
            ticket_id=ticket.id,
            type="TICKET_CANCELLED",
            title=f"Ticket Cancelled: {ticket.ticket_code}",
            body=f"Your ticket has been cancelled. Reason: {payload.reason}"
        )

    return {"status": "CANCELLED"}

@router.post("/{ticket_id}/analyze", response_model=AIAnalysisResponse)
async def analyze_ticket_case(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Triggers Hindsight Recall + Groq Reasoning Loop."""
    try:
        result = await analysis_service.analyze_ticket(ticket_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
