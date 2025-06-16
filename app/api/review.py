# app/api/review.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.dependencies import get_current_user
from app.models import Review, Excursion, User
from app.schemas.review import ReviewCreate, ReviewOut
from typing import List

router = APIRouter()

@router.post("/excursions/{excursion_id}/review", response_model=ReviewOut)
def create_review(excursion_id: int, review: ReviewCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    excursion = db.query(Excursion).filter(Excursion.id == excursion_id).first()
    if not excursion:
        raise HTTPException(status_code=404, detail="Экскурсия не найдена")

    db_review = Review(
        user_id=current_user.id,
        excursion_id=excursion_id,
        rating=review.rating,
        comment=review.comment
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


@router.get("/excursions/{excursion_id}/reviews", response_model=List[ReviewOut])
def get_reviews(excursion_id: int, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(Review.excursion_id == excursion_id).all()
    result = []
    for r in reviews:
        result.append(ReviewOut(
            id=r.id,
            user_id=r.user_id,
            excursion_id=r.excursion_id,
            rating=r.rating,
            comment=r.comment,
            user_full_name=r.user.full_name if r.user else None
        ))
    return result

