from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime

from app.database import Base


class Admin(Base):
    """
    The LifeFlow admin account. Admins can see every donor, hospital,
    and receiver's full history (requests, donations, notifications) --
    kept separate from the individual histories those users see for
    themselves.

    must_change_password starts True: every fresh install is seeded
    with the same default email/password (see main.py), and since
    each hospital deployment would otherwise reuse that same default,
    the admin is forced to set their own password the first time they
    log in, before they can reach the dashboard.
    """
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    must_change_password = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
