from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Ticket, Product, PatternAlert, PatternAlertCase
from app.config import settings

class PatternService:
    """
    Business Intelligence: The Ripple Effect.
    Detects cross-customer failure clusters sharing the same product model + issue category.
    Counts DISTINCT customers (not raw tickets).
    """
    def scan_and_update_patterns(self, db: Session) -> List[PatternAlert]:
        """
        Scans all tickets in the system, groups by (product.model, ticket.issue_category)
        across DISTINCT customer_id, and creates/updates PatternAlerts when threshold is met.
        """
        threshold = settings.RIPPLE_THRESHOLD

        # Query distinct customer counts grouped by model and issue_category
        clusters = (
            db.query(
                Product.model.label("model"),
                Ticket.issue_category.label("category"),
                func.count(func.distinct(Ticket.customer_id)).label("unique_customers"),
                func.count(Ticket.id).label("total_tickets")
            )
            .join(Product, Ticket.product_id == Product.id)
            .group_by(Product.model, Ticket.issue_category)
            .all()
        )

        active_alerts = []
        for cluster in clusters:
            if cluster.unique_customers >= threshold:
                alert = (
                    db.query(PatternAlert)
                    .filter(
                        PatternAlert.product_model == cluster.model,
                        PatternAlert.issue_category == cluster.category
                    )
                    .first()
                )

                if not alert:
                    alert = PatternAlert(
                        product_model=cluster.model,
                        issue_category=cluster.category,
                        case_count=cluster.unique_customers,
                        status="active",
                        staff_notes=f"Cluster detected: {cluster.unique_customers} distinct customers reported '{cluster.category}' on {cluster.model}."
                    )
                    db.add(alert)
                    db.flush()
                else:
                    alert.case_count = cluster.unique_customers

                # Link supporting tickets
                matching_tickets = (
                    db.query(Ticket)
                    .join(Product, Ticket.product_id == Product.id)
                    .filter(
                        Product.model == cluster.model,
                        Ticket.issue_category == cluster.category
                    )
                    .all()
                )

                # Clear and re-populate link table
                db.query(PatternAlertCase).filter(PatternAlertCase.alert_id == alert.id).delete()
                for t in matching_tickets:
                    alert_case = PatternAlertCase(alert_id=alert.id, ticket_id=t.id)
                    db.add(alert_case)

                active_alerts.append(alert)

        db.commit()
        return active_alerts

    def get_all_patterns(self, db: Session) -> List[Dict[str, Any]]:
        self.scan_and_update_patterns(db)
        alerts = db.query(PatternAlert).order_by(PatternAlert.case_count.desc()).all()
        
        results = []
        for a in alerts:
            cases = []
            for pac in a.cases:
                t = pac.ticket
                if t:
                    cases.append({
                        "id": t.id,
                        "ticket_code": t.ticket_code or f"TCK-{t.id}",
                        "customer_name": t.customer.name if t.customer else "Unknown",
                        "customer_id": t.customer_id,
                        "status": t.status,
                        "description": t.issue_description,
                        "created_at": t.created_at
                    })

            results.append({
                "id": a.id,
                "product_model": a.product_model,
                "issue_category": a.issue_category,
                "case_count": a.case_count,  # distinct customer count
                "status": a.status,
                "staff_notes": a.staff_notes,
                "cases": cases
            })
        return results

pattern_service = PatternService()
