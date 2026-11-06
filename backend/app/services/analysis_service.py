from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models import Ticket, Customer, Product, RepairRecord
from app.services.hindsight_service import hindsight_service
from app.services.groq_service import groq_service
from app.services.pattern_service import pattern_service

class AnalysisService:
    """
    Coordinates Flow B:
    1. Loads ticket and customer history from SQLite.
    2. Calls Hindsight recall for semantic memory.
    3. Sends synthesized context to Groq LLM.
    4. Formats structured, evidence-backed advisory output.
    """
    async def analyze_ticket(self, ticket_id: int, db: Session) -> Dict[str, Any]:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise ValueError(f"Ticket #{ticket_id} not found.")

        customer = ticket.customer
        product = ticket.product

        # 1. Fetch customer's previous tickets and repairs from SQLite
        past_tickets = (
            db.query(Ticket)
            .filter(
                Ticket.customer_id == customer.id,
                Ticket.id != ticket.id
            )
            .order_by(Ticket.created_at.asc())
            .all()
        )

        customer_history = []
        for pt in past_tickets:
            repairs_list = []
            for r in pt.repairs:
                repairs_list.append({
                    "action": r.action,
                    "outcome": r.outcome,
                    "technician_notes": r.technician_notes,
                    "confirmed_at": str(r.confirmed_at)
                })
            customer_history.append({
                "ticket_id": pt.id,
                "ticket_code": pt.ticket_code or f"TCK-{pt.id}",
                "issue_description": pt.issue_description,
                "issue_category": pt.issue_category,
                "status": pt.status,
                "created_at": str(pt.created_at),
                "repairs": repairs_list
            })

        # 2. Call Hindsight Recall
        recall_query = f"{product.model} {ticket.issue_category}: {ticket.issue_description}"
        recall_res = await hindsight_service.recall(
            db=db,
            query=recall_query,
            filter_metadata={"product_model": product.model}
        )
        recalled_memories = recall_res.get("memories", [])

        # 3. Check for existing cross-customer pattern for this model & issue
        patterns = pattern_service.get_all_patterns(db)
        relevant_patterns = [
            p for p in patterns 
            if p["product_model"].lower() == product.model.lower() 
            and p["issue_category"].lower() == ticket.issue_category.lower()
        ]

        # 4. Reason with Groq
        ai_result = await groq_service.analyze_repair(
            complaint_text=ticket.issue_description,
            issue_category=ticket.issue_category,
            product_model=product.model,
            product_type=product.product_type,
            customer_history=customer_history,
            recalled_memories=recalled_memories,
            cross_customer_patterns=relevant_patterns
        )

        return {
            "ticket_id": ticket.id,
            "repeat_issue": ai_result.get("repeat_issue", False),
            "repeat_reason": ai_result.get("repeat_reason"),
            "previous_repair_summary": ai_result.get("previous_repair_summary"),
            "previous_outcome": ai_result.get("previous_outcome"),
            "suggested_inspection_areas": ai_result.get("suggested_inspection_areas", []),
            "explanation": ai_result.get("explanation", ""),
            "supporting_evidence": ai_result.get("supporting_evidence", []),
            "limitations": ai_result.get("limitations", []),
            "recalled_memories_count": len(recalled_memories),
            "hindsight_status": recall_res.get("status", "unknown")
        }

analysis_service = AnalysisService()
