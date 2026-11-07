from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import Ticket, Product, RepairRecord
from app.config import settings

def check_is_repeat_ticket(
    db: Session,
    customer_id: int,
    product_id: int,
    issue_category: str,
    issue_description: str,
    current_ticket_id: Optional[int] = None,
    window_days: Optional[int] = None
) -> Tuple[bool, Optional[Ticket], Optional[str]]:
    """
    Determines if a ticket is a repeat case:
    A ticket is a repeat if the same customer + same product/model has a previous ticket
    with a similar issue (error code, category match, or semantic keywords) within a
    configurable window (default 30 days) AND that earlier repair was not confirmed 'successful'.
    
    Returns: (is_repeat, prior_ticket, reason)
    """
    days = window_days or settings.REPEAT_WINDOW_DAYS
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # 1. Fetch previous tickets for the same customer and product created within the window
    query = (
        db.query(Ticket)
        .filter(
            Ticket.customer_id == customer_id,
            Ticket.product_id == product_id,
            Ticket.created_at >= cutoff
        )
    )
    if current_ticket_id:
        query = query.filter(Ticket.id != current_ticket_id)

    prior_tickets = query.order_by(Ticket.created_at.desc()).all()
    if not prior_tickets:
        return False, None, None

    # Check each prior ticket
    for prior in prior_tickets:
        # Check issue similarity (category match or common keywords like e20, drain, cooling)
        category_match = (
            prior.issue_category.lower() == issue_category.lower()
            or (prior.issue_category != "Other" and prior.issue_category in issue_category)
        )
        
        # Keyword/error code match
        common_error_codes = ["e20", "oe", "e30", "ue", "e4"]
        desc_lower = issue_description.lower()
        prior_desc_lower = prior.issue_description.lower()
        code_match = any(code in desc_lower and code in prior_desc_lower for code in common_error_codes)

        if not (category_match or code_match):
            continue

        # Check earlier repairs: was any repair confirmed 'successful'?
        has_successful_repair = any(r.outcome == "successful" for r in prior.repairs)
        
        if not has_successful_repair:
            # If outcome was 'temporary', 'unsuccessful', or unresolved/pending -> REPEAT!
            last_repair = prior.repairs[-1] if prior.repairs else None
            outcome_str = last_repair.outcome if last_repair else "unresolved"
            reason = (
                f"Prior ticket {prior.ticket_code or prior.id} for {issue_category} "
                f"was recorded within {days} days with outcome '{outcome_str}' (not permanently resolved)."
            )
            return True, prior, reason

    return False, None, None
