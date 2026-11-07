from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import Notification, User

class NotificationService:
    """
    Manages in-app notifications for Customers, Technicians, and Admins.
    Types: TICKET_CREATED, TICKET_ASSIGNED, VISIT_SCHEDULED, VISIT_RESCHEDULED,
           WORK_STARTED, OTP_ISSUED, TICKET_RESOLVED, TICKET_CANCELLED.
    """
    def send_notification(
        self,
        db: Session,
        user_id: int,
        type: str,
        title: str,
        body: str,
        ticket_id: Optional[int] = None
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            ticket_id=ticket_id,
            type=type,
            title=title,
            body=body,
            is_read=False
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif

    def notify_user_by_role(
        self,
        db: Session,
        role: str,
        type: str,
        title: str,
        body: str,
        ticket_id: Optional[int] = None
    ) -> List[Notification]:
        users = db.query(User).filter(User.role == role, User.is_active == True).all()
        created = []
        for u in users:
            n = Notification(
                user_id=u.id,
                ticket_id=ticket_id,
                type=type,
                title=title,
                body=body,
                is_read=False
            )
            db.add(n)
            created.append(n)
        db.commit()
        return created

    def get_user_notifications(
        self,
        db: Session,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        q = db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            q = q.filter(Notification.is_read == False)
        return q.order_by(Notification.created_at.desc()).limit(limit).all()

    def get_unread_count(self, db: Session, user_id: int) -> int:
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()

    def mark_as_read(self, db: Session, notification_id: int, user_id: int) -> bool:
        notif = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        if notif:
            notif.is_read = True
            db.commit()
            return True
        return False

    def mark_all_as_read(self, db: Session, user_id: int) -> int:
        count = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .update({"is_read": True})
        )
        db.commit()
        return count

notification_service = NotificationService()
