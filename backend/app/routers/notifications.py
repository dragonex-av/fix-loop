from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.database import get_db
from app.models import Notification, User
from app.schemas import NotificationOut
from app.services.auth_service import get_current_user
from app.services.notification_service import notification_service

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

@router.get("", response_model=List[NotificationOut])
def get_my_notifications(
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return notification_service.get_user_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only
    )

@router.get("/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = notification_service.get_unread_count(db=db, user_id=current_user.id)
    return {"unread_count": count}

@router.patch("/{notification_id}/read")
def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = notification_service.mark_as_read(db=db, notification_id=notification_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "read"}

@router.post("/mark-all-read")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = notification_service.mark_all_as_read(db=db, user_id=current_user.id)
    return {"marked_read": count}
