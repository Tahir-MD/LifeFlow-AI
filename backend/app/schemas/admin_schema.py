from pydantic import BaseModel, EmailStr
from datetime import datetime


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class AdminOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    must_change_password: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AdminChangePassword(BaseModel):
    current_password: str
    new_password: str
