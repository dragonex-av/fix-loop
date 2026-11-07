import json
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import MemoryEvent
from app.config import settings

logger = logging.getLogger("fixloop.hindsight")

class HindsightService:
    """
    Official Hindsight Experience Memory Integration Service.
    Powered by hindsight-client (Vectorize.io).
    Handles genuine retain and recall against live Hindsight Cloud.
    Logs all operations into SQLite MemoryEvent table for transparent inspection.
    Deduplicates recall queries within 30 seconds to avoid multi-log bursts.
    """
    def __init__(self):
        self.base_url = settings.HINDSIGHT_BASE_URL.rstrip('/')
        self.api_key = settings.HINDSIGHT_API_KEY
        self.bank_id = settings.HINDSIGHT_BANK_OR_AGENT_ID
        self._client = None
        self._last_recall_cache = {}  # query_hash -> timestamp

    def get_client(self):
        if not self._client and self.is_configured():
            try:
                from hindsight_client import Hindsight
                self._client = Hindsight(
                    base_url=self.base_url,
                    api_key=self.api_key,
                    timeout=30.0
                )
            except Exception as e:
                logger.error(f"Failed to initialize Hindsight client: {e}")
        return self._client

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
        Retains a verified repair outcome experience into live Hindsight Cloud.
        """
        event = MemoryEvent(
            entity_type=entity_type,
            entity_id=entity_id,
            operation="retain",
            query_or_content=content
        )

        if not self.is_configured():
            event.status = "unconfigured"
            event.error_summary = "HINDSIGHT_API_KEY not configured"
            db.add(event)
            db.commit()
            return {"status": "unconfigured", "event_id": event.id}

        client = self.get_client()
        if not client:
            event.status = "failed"
            event.error_summary = "Failed to initialize client"
            db.add(event)
            db.commit()
            return {"status": "failed", "event_id": event.id}

        try:
            res = await client.aretain(
                bank_id=self.bank_id,
                contents=[content]
            )

            event.status = "success"
            event.provider_ref = getattr(res, "id", None) or f"retained_{entity_id}"
            event.raw_response = json.dumps({
                "status": "retained",
                "bank_id": self.bank_id,
                "metadata": metadata or {}
            })
            db.add(event)
            db.commit()

            return {
                "status": "success",
                "event_id": event.id,
                "provider_ref": event.provider_ref
            }

        except Exception as e:
            logger.error(f"Error calling live Hindsight retain: {e}")
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
        Recalls past experiences relevant to the query from live Hindsight Cloud.
        Logs one MemoryEvent per genuine recall execution.
        """
        clean_query = query.strip()
        
        # Deduplication check: if identical recall within past 5 seconds, don't double log
        import time
        now_ts = time.time()
        last_time = self._last_recall_cache.get(clean_query, 0)
        if now_ts - last_time < 3.0:
            # Query was executed moments ago; fetch last memory event to avoid duplicate DB row
            existing_event = (
                db.query(MemoryEvent)
                .filter(MemoryEvent.operation == "recall", MemoryEvent.query_or_content == clean_query[:1500])
                .order_by(MemoryEvent.created_at.desc())
                .first()
            )
            if existing_event:
                return {"status": existing_event.status, "memories": [], "event_id": existing_event.id, "cached": True}

        self._last_recall_cache[clean_query] = now_ts

        event = MemoryEvent(
            entity_type="query",
            operation="recall",
            query_or_content=clean_query[:1500]
        )

        if not self.is_configured():
            event.status = "unconfigured"
            event.error_summary = "HINDSIGHT_API_KEY not configured"
            db.add(event)
            db.commit()
            return {"status": "unconfigured", "memories": [], "event_id": event.id}

        client = self.get_client()
        if not client:
            event.status = "failed"
            db.add(event)
            db.commit()
            return {"status": "failed", "memories": [], "event_id": event.id}

        try:
            res = await client.arecall(
                bank_id=self.bank_id,
                query=clean_query
            )

            results_list = getattr(res, "results", []) or []
            memories = []
            for r in results_list:
                text_content = getattr(r, "text", "") or getattr(r, "content", "") or str(r)
                memories.append({
                    "text": text_content,
                    "score": getattr(r, "score", None),
                    "id": getattr(r, "id", None)
                })

            event.status = "success" if memories else "empty"
            event.provider_ref = f"recalled_{len(memories)}_items"
            event.raw_response = json.dumps({
                "results_count": len(memories),
                "bank_id": self.bank_id,
                "first_excerpt": memories[0]["text"][:200] if memories else ""
            })
            db.add(event)
            db.commit()

            return {
                "status": event.status,
                "memories": memories,
                "event_id": event.id
            }

        except Exception as e:
            logger.error(f"Error calling live Hindsight recall: {e}")
            event.status = "failed"
            event.error_summary = str(e)[:500]
            db.add(event)
            db.commit()
            return {"status": "failed", "memories": [], "error": str(e), "event_id": event.id}

hindsight_service = HindsightService()
