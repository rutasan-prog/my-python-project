# app/schemas/review.py
from pydantic import BaseModel, Field
from typing import Optional

class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class ReviewOut(BaseModel):
    id: int
    user_id: int
    excursion_id: int
    rating: int
    comment: Optional[str] = None
    user_full_name: Optional[str] = None

    class Config:
        from_attributes = True