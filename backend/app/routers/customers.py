from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Customer, Product, Ticket, RepairRecord, Followup
from app.schemas import CustomerCreate, CustomerOut

router = APIRouter(prefix="/api/customers", tags=["customers"])

@router.get("", response_model=List[CustomerOut])
def get_customers(query: Optional[str] = Query(None), db: Session = Depends(get_db)):
    q = db.query(Customer)
    if query:
        q = q.filter(Customer.name.ilike(f"%{query}%") | Customer.phone.ilike(f"%{query}%"))
    return q.all()

@router.post("", response_model=CustomerOut)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    existing = db.query(Customer).filter(Customer.phone == payload.phone).first()
    if existing:
        return existing
    customer = Customer(name=payload.name, phone=payload.phone, email=payload.email)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

@router.get("/{customer_id}")
def get_customer_profile(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    products = [
        {
            "id": p.id,
            "product_type": p.product_type,
            "brand": p.brand,
            "model": p.model,
            "serial_number": p.serial_number,
            "created_at": p.created_at
        }
        for p in customer.products
    ]
    return {
        "id": customer.id,
        "name": customer.name,
        "phone": customer.phone,
        "email": customer.email,
        "created_at": customer.created_at,
        "products": products
    }

@router.get("/{customer_id}/history")
def get_customer_history(customer_id: int, db: Session = Depends(get_db)):
    """
    Customer 360 Timeline:
    Returns chronological timeline of complaints, repairs, confirmed outcomes, and follow-ups.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    timeline = []
    for t in customer.tickets:
        timeline.append({
            "type": "ticket_created",
            "date": t.created_at,
            "ticket_id": t.id,
            "ticket_code": t.ticket_code or f"TCK-{t.id}",
            "title": f"Complaint: {t.issue_category}",
            "description": t.issue_description,
            "product": f"{t.product.brand} {t.product.model} ({t.product.product_type})",
            "status": t.status,
            "priority": t.priority
        })
        for r in t.repairs:
            timeline.append({
                "type": "repair_performed",
                "date": r.confirmed_at or r.created_at,
                "ticket_id": t.id,
                "ticket_code": t.ticket_code or f"TCK-{t.id}",
                "title": f"Repair: {r.action}",
                "description": r.technician_notes or "Repair recorded.",
                "outcome": r.outcome,
                "confirmed_by": r.confirmed_by
            })

    for f in customer.followups:
        timeline.append({
            "type": "followup_scheduled",
            "date": f.created_at,
            "ticket_id": f.ticket_id,
            "ticket_code": f.ticket.ticket_code if f.ticket else f"TCK-{f.ticket_id}",
            "title": f"Follow-up: {f.owner}",
            "description": f.notes or "Scheduled customer check-in.",
            "promised_at": f.promised_at,
            "status": f.status,
            "completed_at": f.completed_at
        })

    # Sort chronological descending
    timeline.sort(key=lambda x: str(x["date"]), reverse=True)
    return {
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "email": customer.email
        },
        "timeline": timeline
    }
