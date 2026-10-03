from sqlalchemy.orm import Session

from app.models.notification import Notification


def notify(db: Session, user_type: str, user_id: int, title: str, message: str,
           category: str = "general", related_request_id: int = None) -> None:
    """
    Creates an in-app notification. This stands in for the push
    notifications / SMS / email alerts a production deployment would
    also send through a provider such as Twilio or SendGrid.
    """
    notification = Notification(
        user_type=user_type,
        user_id=user_id,
        title=title,
        message=message,
        category=category,
        related_request_id=related_request_id,
    )
    db.add(notification)
