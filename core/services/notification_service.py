from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from core.database import get_db
from core.models.notification import Notification
from core.models.user import User


class NotificationService:
    """Service for creating and fetching user notifications."""

    def __init__(self) -> None:
        pass

    def _resolve_user_id(self, db: Session, telegram_id_or_user_id: int) -> Optional[int]:
        """Accepts Telegram id or internal user id and returns internal id."""
        user = (
            db.query(User)
            .filter((User.id == telegram_id_or_user_id) | (User.tg_user_id == telegram_id_or_user_id))
            .first()
        )
        return user.id if user else None

    def create_notification(
        self,
        user_id_or_tg: int,
        title: str,
        message: str,
        *,
        type: str = "info",
        metadata: Optional[str] = None,
    ) -> Optional[int]:
        with get_db() as db:
            resolved_user_id = self._resolve_user_id(db, user_id_or_tg)
            if not resolved_user_id:
                return None

            notif = Notification(
                user_id=resolved_user_id,
                title=title,
                message=message,
                type=type,
                metadata=metadata,
            )
            db.add(notif)
            db.commit()
            db.refresh(notif)
            return notif.id

    def list_notifications(
        self,
        user_id_or_tg: int,
        *,
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False,
    ) -> List[Dict[str, Any]]:
        with get_db() as db:
            resolved_user_id = self._resolve_user_id(db, user_id_or_tg)
            if not resolved_user_id:
                return []

            query = db.query(Notification).filter(Notification.user_id == resolved_user_id)
            if unread_only:
                query = query.filter(Notification.is_read.is_(False))

            items = (
                query.order_by(Notification.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": n.id,
                    "title": n.title,
                    "message": n.message,
                    "type": n.type,
                    "is_read": bool(n.is_read),
                    "created_at": n.created_at,
                    "read_at": n.read_at,
                }
                for n in items
            ]

    def count_notifications(self, user_id_or_tg: int, *, unread_only: bool = False) -> int:
        with get_db() as db:
            resolved_user_id = self._resolve_user_id(db, user_id_or_tg)
            if not resolved_user_id:
                return 0

            query = db.query(Notification).filter(Notification.user_id == resolved_user_id)
            if unread_only:
                query = query.filter(Notification.is_read.is_(False))
            return query.count()

    def mark_read(self, user_id_or_tg: int, notification_id: int) -> bool:
        with get_db() as db:
            resolved_user_id = self._resolve_user_id(db, user_id_or_tg)
            if not resolved_user_id:
                return False

            notif = (
                db.query(Notification)
                .filter(Notification.id == notification_id, Notification.user_id == resolved_user_id)
                .first()
            )
            if not notif:
                return False

            notif.is_read = True
            notif.read_at = datetime.utcnow()
            db.commit()
            return True


notification_service = NotificationService()


