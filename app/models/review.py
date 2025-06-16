# app/models/review.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    excursion_id = Column(Integer, ForeignKey("excursions.id"))
    rating = Column(Integer)  # от 1 до 5
    comment = Column(String)

    user = relationship("User")
    excursion = relationship("Excursion")