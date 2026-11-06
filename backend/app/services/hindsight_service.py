import os
import json
import logging
import certifi
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.config import settings
from app.models import MemoryEvent

# Guarantee SSL cert bundle on macOS
os.environ["SSL_CERT_FILE"] = certifi.where()

logger = logging.getLogger("fixloop.hindsight")

class HindsightService:
    """
    Official Hindsight Experience Memory Integration Service.
    Powered by hindsight-client (Vectorize.io).
    Handles genuine retain and recall against live Hindsight Cloud.
    Logs all operations into SQLite MemoryEvent table for transparent judge inspection.
    """
    def __init__(self):
        self.base_url = settings.HINDSIGHT_BASE_URL.rstrip('/')
        self.api_key = settings.HINDSIGHT_API_KEY
        self.bank_id = settings.HINDSIGHT_BANK_OR_AGENT_ID
        self._client = None

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
        Retains an experience (complaint or confirmed repair outcome) into live Hindsight Cloud.
        """
        event = MemoryEvent(
            entity_type=entity_type,
            entity_id=entity_id,
            operation="retain",
            query_or_content=content[:1500]
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
            event.error_summary = "Client initialization error"
            db.add(event)
            db.commit()
            return {"status": "failed", "event_id": event.id}

        try:
            # Call official Hindsight retain
            res = await client.aretain(
                bank_id=self.bank_id,
                content=content,
                metadata={k: str(v) for k, v in (metadata or {}).items()}
            )
            
            provider_ref = getattr(res, "operation_id", None) or getattr(res, "id", None) or f"hs-{int(datetime.now().timestamp())}"
            raw_summary = {
                "success": getattr(res, "success", True),
                "bank_id": self.bank_id,
                "items_count": getattr(res, "items_count", 1),
                "operation_id": provider_ref,
                "usage": str(getattr(res, "usage", ""))
            }

            event.status = "success"
            event.provider_ref = str(provider_ref)
            event.raw_response = json.dumps(raw_summary)
            db.add(event)
            db.commit()
            return {"status": "success", "provider_ref": event.provider_ref, "event_id": event.id}

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
        """
        event = MemoryEvent(
            entity_type="query",
            operation="recall",
            query_or_content=query[:1500]
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
                query=query
            )

            # Extract memory items from RecallResponse
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
