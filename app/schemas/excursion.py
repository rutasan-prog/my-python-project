from pydantic import BaseModel
from enum import Enum
from app.schemas.waypoint import WaypointCreate
from typing import List
from typing import Optional
from app.schemas.user import UserOut
from datetime import datetime


class ExcursionCreateFull(BaseModel):
    title: str
    description: str | None = None
    points: List[WaypointCreate]

class ExcursionStatus(str, Enum):
    draft = "draft"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class ExcursionCreate(BaseModel):
    title: str
    description: str | None = None

class ExcursionOut(BaseModel):
    id: int
    title: str
    description: str | None = None
    image_url: str | None = None
    status: ExcursionStatus
    average_rating: float | None = None
    author_id: int
    author: Optional[UserOut] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ExcursionCreateFullData(BaseModel):
    title: str
    description: str | None = None
    points: List[WaypointCreate]
