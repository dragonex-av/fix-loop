from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import Followup

class FollowupService:
    """
    Manages customer rescue follow-up commitments.
    Classifies upcoming, due, and overdue based on live UTC timestamps.
    """
    def refresh_statuses(self, db: Session):
        now = datetime.now(timezone.utc)
        followups = db.query(Followup).filter(Followup.status.in_(["upcoming", "due", "overdue"])).all()
        for f in followups:
            promised = f.promised_at
            # Make sure timezone is comparable
            if promised.tzinfo is None:
                promised = promised.replace(tzinfo=timezone.utc)

            delta = (now - promised).total_seconds()
            if delta > 3600:  # More than 1 hour past due
                f.status = "overdue"
            elif delta >= 0:   # Due now
                f.status = "due"
            else:
                f.status = "upcoming"
        db.commit()

    def get_queue(self, db: Session):
        self.refresh_statuses(db)
        items = db.query(Followup).order_by(Followup.promised_at.asc()).all()
        results = []
        for item in items:
            results.append({
                "id": item.id,
                "customer_id": item.customer_id,
                "ticket_id": item.ticket_id,
                "customer_name": item.customer.name if item.customer else "Unknown",
                "ticket_code": item.ticket.ticket_code if item.ticket else f"TCK-{item.ticket_id}",
                "promised_at": item.promised_at,
                "owner": item.owner,
                "status": item.status,
                "notes": item.notes,
                "completed_at": item.completed_at,
                "created_at": item.created_at
            })
        return results

followup_service = FollowupService()
