from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Ticket, Followup, PatternAlert, MemoryEvent
from app.schemas import DashboardMetrics
from app.services.pattern_service import pattern_service
from app.services.followup_service import followup_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("", response_model=DashboardMetrics)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    # Refresh pattern and followup states
    pattern_service.scan_and_update_patterns(db)
    followup_service.refresh_statuses(db)

    total_tickets = db.query(Ticket).count()
    open_tickets = db.query(Ticket).filter(Ticket.status.in_(["New", "Open", "In Progress", "Reopened", "Investigate"])).count()
    repeat_cases = db.query(Ticket).filter(Ticket.status == "Reopened").count()
    overdue_followups = db.query(Followup).filter(Followup.status == "overdue").count()
    active_patterns = db.query(PatternAlert).filter(PatternAlert.status == "active").count()

    # Recent tickets
    recent_tickets_q = db.query(Ticket).order_by(Ticket.created_at.desc()).limit(5).all()
    recent_tickets = []
    for t in recent_tickets_q:
        latest_repair = t.repairs[-1] if t.repairs else None
        recent_tickets.append({
            "id": t.id,
            "ticket_code": t.ticket_code or f"TCK-{t.id}",
            "customer_name": t.customer.name if t.customer else "Unknown",
            "model": t.product.model if t.product else "Unknown",
            "issue_category": t.issue_category,
            "status": t.status,
            "priority": t.priority,
            "created_at": t.created_at,
            "latest_outcome": latest_repair.outcome if latest_repair else None
        })

    # Recent memory events
    mem_events_q = db.query(MemoryEvent).order_by(MemoryEvent.created_at.desc()).limit(6).all()
    recent_memories = [
        {
            "id": m.id,
            "operation": m.operation,
            "entity_type": m.entity_type,
            "status": m.status,
            "provider_ref": m.provider_ref,
            "query_or_content": m.query_or_content[:120],
            "created_at": m.created_at
        }
        for m in mem_events_q
    ]

    # Needs attention queue (repeat cases, overdue follow-ups, pattern alerts)
    needs_attention = []
    # 1. Overdue followups
    overdue_f = db.query(Followup).filter(Followup.status == "overdue").limit(3).all()
    for f in overdue_f:
        needs_attention.append({
            "type": "overdue_followup",
            "title": f"Overdue callback for {f.customer.name if f.customer else 'Customer'}",
            "severity": "high",
            "detail": f"Assigned to {f.owner}. Promised: {f.promised_at.strftime('%b %d, %H:%M') if f.promised_at else 'Unknown'}",
            "link_id": f.ticket_id
        })
    # 2. Active pattern alerts
    patterns_q = db.query(PatternAlert).filter(PatternAlert.status == "active").limit(2).all()
    for p in patterns_q:
        needs_attention.append({
            "type": "ripple_pattern",
            "title": f"Ripple Effect: {p.case_count} cases on {p.product_model}",
            "severity": "critical",
            "detail": f"Cluster detected for '{p.issue_category}'. Recommended technical review.",
            "link_id": p.id
        })

    return {
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "repeat_cases": repeat_cases,
        "overdue_followups": overdue_followups,
        "active_patterns": active_patterns,
        "recent_tickets": recent_tickets,
        "recent_memory_events": recent_memories,
        "needs_attention": needs_attention
    }
