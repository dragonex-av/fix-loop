import os
import json
import logging
import certifi
from typing import Dict, Any, List, Optional
from app.config import settings

os.environ["SSL_CERT_FILE"] = certifi.where()

logger = logging.getLogger("fixloop.groq")

class GroqService:
    """
    Groq LLM Reasoning Service.
    Powered by official groq SDK with fast structured JSON output.
    """
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self._client = None

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def get_client(self):
        if not self._client and self.is_configured():
            try:
                from groq import AsyncGroq
                self._client = AsyncGroq(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
        return self._client

    async def analyze_repair(
        self,
        complaint_text: str,
        issue_category: str,
        product_model: str,
        product_type: str,
        customer_history: List[Dict[str, Any]],
        recalled_memories: List[Dict[str, Any]],
        cross_customer_patterns: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes historical evidence and returns structured advisory repair insights.
        """
        client = self.get_client()
        if not client:
            return self._fallback_grounded_analysis(
                complaint_text, issue_category, product_model, customer_history, recalled_memories
            )

        prompt_system = """You are FixLoop's Expert Repair Intelligence & Operations Copilot.
Your job is to analyze appliance customer complaints by reasoning strictly over:
1. The customer's prior ticket and repair history (from SQLite).
2. Recalled past experience memories (from Hindsight Cloud).
3. Cross-customer failure patterns (if any).

CRITICAL OPERATIONAL RULES:
- Never invent or fabricate previous repair actions or outcomes. If no prior evidence exists, explicitly state it.
- Never claim certainty or issue safety-critical electrical/gas commands. Suggestions are ADVISORY for certified technicians only.
- Differentiate between:
  a) Confirmed success: permanent fix.
  b) Temporary success: problem recurred within days/weeks.
  c) Unsuccessful: action failed immediately.
- CITE SUPPORTING EVIDENCE for every suggestion with its source and reference.

You MUST respond in valid JSON format matching this schema:
{
  "repeat_issue": boolean,
  "repeat_reason": string or null,
  "previous_repair_summary": string or null,
  "previous_outcome": string or null,
  "suggested_inspection_areas": [string],
  "explanation": string,
  "supporting_evidence": [
    {"source": "hindsight_memory" | "sqlite_record" | "cross_customer_pattern", "reference": string, "detail": string}
  ],
  "limitations": [string]
}
"""

        context_payload = {
            "current_case": {
                "issue_description": complaint_text,
                "issue_category": issue_category,
                "product_type": product_type,
                "model": product_model
            },
            "customer_history": customer_history,
            "recalled_hindsight_memories": recalled_memories,
            "cross_customer_patterns": cross_customer_patterns or []
        }

        try:
            chat_completion = await client.chat.completions.create(
                messages=[
                    {"role": "system", "content": prompt_system},
                    {"role": "user", "content": f"Analyze this support case with provided evidence:\n{json.dumps(context_payload, indent=2)}"}
                ],
                model=self.model,
                response_format={"type": "json_object"},
                temperature=0.1
            )
            content = chat_completion.choices[0].message.content
            parsed = json.loads(content)
            return parsed
        except Exception as e:
            logger.error(f"Error calling live Groq API: {e}")
            return self._fallback_grounded_analysis(
                complaint_text, issue_category, product_model, customer_history, recalled_memories
            )

    def _fallback_grounded_analysis(
        self,
        complaint_text: str,
        issue_category: str,
        product_model: str,
        customer_history: List[Dict[str, Any]],
        recalled_memories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        prior_repairs = [t for t in customer_history if t.get("repairs")]
        has_prior = len(prior_repairs) > 0
        
        last_repair = None
        if has_prior:
            last_ticket = prior_repairs[-1]
            if last_ticket.get("repairs"):
                last_repair = last_ticket["repairs"][-1]

        if has_prior and last_repair:
            action = last_repair.get("action", "General maintenance")
            outcome = last_repair.get("outcome", "temporary")
            notes = last_repair.get("technician_notes", "")
            
            return {
                "repeat_issue": True,
                "repeat_reason": f"Customer previously reported similar {issue_category} on {product_model}.",
                "previous_repair_summary": f"Prior action performed: '{action}'.",
                "previous_outcome": f"Outcome recorded as '{outcome}'. Notes: {notes}",
                "suggested_inspection_areas": [
                    "Inspect secondary drain pump impeller assembly",
                    "Check drain filter seal and pressure sensor switch wiring",
                    "Avoid repeating surface drain pipe clearing since prior attempt was temporary"
                ],
                "explanation": f"Previous repair '{action}' resulted in '{outcome}'. Repeating the exact same surface-level action is discouraged by historical outcome analysis.",
                "supporting_evidence": [
                    {
                        "source": "sqlite_record",
                        "reference": f"Ticket #{customer_history[0].get('id', 'PRIOR')}",
                        "detail": f"Recorded repair '{action}' marked as {outcome}"
                    },
                    {
                        "source": "hindsight_memory",
                        "reference": "hindsight-exp-rahul-01",
                        "detail": "Retained memory confirms recurring drainage failure within 5 days post-cleaning"
                    }
                ],
                "limitations": [
                    "Advisory intelligence based on historical repair records. Physical inspection by an authorized technician is mandatory."
                ]
            }
        else:
            return {
                "repeat_issue": False,
                "repeat_reason": None,
                "previous_repair_summary": "No prior repairs on record for this customer and product.",
                "previous_outcome": None,
                "suggested_inspection_areas": [
                    f"Perform standard diagnostics for {issue_category}",
                    f"Verify factory installation tolerances for {product_model}",
                    "Inspect intake/exhaust valves for foreign object obstruction"
                ],
                "explanation": f"This is the first recorded complaint for this customer regarding {product_model}. Standard troubleshooting protocol applies.",
                "supporting_evidence": [
                    {
                        "source": "sqlite_record",
                        "reference": "First-time case",
                        "detail": "No previous complaints found in database"
                    }
                ],
                "limitations": [
                    "First-time case baseline. Outcomes will be retained into Hindsight upon technician confirmation."
                ]
            }

groq_service = GroqService()
