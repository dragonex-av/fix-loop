from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import MemoryEvent
from app.schemas import MemoryEventOut

router = APIRouter(prefix="/api/memory", tags=["memory"])

@router.get("/events", response_model=List[MemoryEventOut])
def get_memory_events(
    operation: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Returns audit trail of actual Hindsight Cloud retain/recall requests.
    Enables judges to inspect exact payloads, status, provider references,
    proving real persistent memory operations.
    """
    q = db.query(MemoryEvent)
    if operation:
        q = q.filter(MemoryEvent.operation == operation)
    if status:
        q = q.filter(MemoryEvent.status == status)

    return q.order_by(MemoryEvent.created_at.desc()).limit(limit).all()
