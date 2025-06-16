from pydantic import BaseModel, constr
from enum import Enum
from datetime import datetime


class RoleEnum(str, Enum):
    user = "user"
    admin = "admin"


class UserCreate(BaseModel):
    login: constr(min_length=3, max_length=50)
    password: constr(min_length=6)
    full_name: str | None = None


class UserLogin(BaseModel):
    login: str
    password: str


class UserOut(BaseModel):
    id: int
    login: str
    full_name: str | None = None
    role: RoleEnum
    created_at: datetime

    class Config:
        orm_mode = True
