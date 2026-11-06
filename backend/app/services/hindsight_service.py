import json
import logging
import httpx
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.config import settings
from app.models import MemoryEvent

logger = logging.getLogger("fixloop.hindsight")

class HindsightService:
    """
    Hindsight Experience Memory Integration Service.
    Handles 'retain' (storing confirmed experience/complaints) and
    'recall' (retrieving past context).
    Logs all events transparently to SQLite MemoryEvent table for judge verification.
    """
    def __init__(self):
        self.base_url = settings.HINDSIGHT_BASE_URL.rstrip('/')
        self.api_key = settings.HINDSIGHT_API_KEY
        self.bank_id = settings.HINDSIGHT_BANK_OR_AGENT_ID

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def retain(
        self,
        db: Session,
        entity_type: str,
        entity_id: int,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Retains an experience (complaint or confirmed repair outcome) into Hindsight Cloud.
        """
        payload = {
            "bank_id": self.bank_id,
            "document": content,
            "metadata": {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **(metadata or {})
            }
        }
        
        event = MemoryEvent(
            entity_type=entity_type,
            entity_id=entity_id,
            operation="retain",
            query_or_content=content[:1000]
        )

        if not self.is_configured():
            event.status = "unconfigured"
            event.error_summary = "HINDSIGHT_API_KEY is not configured in backend/.env"
            db.add(event)
            db.commit()
            db.refresh(event)
            return {
                "status": "unconfigured",
                "message": "Hindsight API key not set. Memory event logged locally.",
                "event_id": event.id
            }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                # Hindsight REST endpoint for retaining memories/documents
                url = f"{self.base_url}/v1/banks/{self.bank_id}/memories"
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code in (200, 201):
                    res_json = response.json()
                    provider_ref = res_json.get("id") or res_json.get("memory_id") or str(res_json)
                    event.status = "success"
                    event.provider_ref = str(provider_ref)
                    event.raw_response = json.dumps(res_json)[:2000]
                    db.add(event)
                    db.commit()
                    return {"status": "success", "provider_ref": event.provider_ref, "event_id": event.id}
                else:
                    event.status = "failed"
                    event.error_summary = f"HTTP {response.status_code}: {response.text[:500]}"
                    db.add(event)
                    db.commit()
                    return {"status": "failed", "error": event.error_summary, "event_id": event.id}

        except Exception as e:
            logger.error(f"Error retaining memory: {e}")
            event.status = "failed"
            event.error_summary = str(e)[:500]
            db.add(event)
            db.commit()
            return {"status": "failed", "error": str(e), "event_id": event.id}

    async def recall(
        self,
        db: Session,
        query: str,
        filter_metadata: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Recalls past experiences relevant to the query from Hindsight Cloud.
        """
        event = MemoryEvent(
            entity_type="query",
            operation="recall",
            query_or_content=query[:1000]
        )

        if not self.is_configured():
            event.status = "unconfigured"
            event.error_summary = "HINDSIGHT_API_KEY is not configured in backend/.env"
            db.add(event)
            db.commit()
            db.refresh(event)
            return {
                "status": "unconfigured",
                "memories": [],
                "message": "Hindsight API key not set.",
                "event_id": event.id
            }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                url = f"{self.base_url}/v1/banks/{self.bank_id}/recall"
                payload = {
                    "query": query,
                    "limit": limit,
                    "filter": filter_metadata or {}
                }
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code == 200:
                    res_json = response.json()
                    memories = res_json.get("memories") or res_json.get("results") or []
                    event.status = "success" if memories else "empty"
                    event.raw_response = json.dumps(res_json)[:2000]
                    event.provider_ref = f"recalled_{len(memories)}_items"
                    db.add(event)
                    db.commit()
                    return {
                        "status": event.status,
                        "memories": memories,
                        "event_id": event.id
                    }
                else:
                    event.status = "failed"
                    event.error_summary = f"HTTP {response.status_code}: {response.text[:500]}"
                    db.add(event)
                    db.commit()
                    return {"status": "failed", "memories": [], "error": event.error_summary, "event_id": event.id}

        except Exception as e:
            logger.error(f"Error recalling memory: {e}")
            event.status = "failed"
            event.error_summary = str(e)[:500]
            db.add(event)
            db.commit()
            return {"status": "failed", "memories": [], "error": str(e), "event_id": event.id}

hindsight_service = HindsightService()
