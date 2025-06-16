from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
import os

from app.db.session import SessionLocal
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.waypoint import Waypoint
from app.models.excursion import Excursion
from app.schemas.waypoint import WaypointOut
from app.schemas.waypoint import WaypointOut
from typing import List

router = APIRouter()

UPLOAD_FOLDER = "static/images"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/waypoints/create", response_model=WaypointOut)
async def create_waypoint(
    excursion_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    latitude: float = Form(...),
    longitude: float = Form(...),
    order_index: int = Form(0),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Проверяем, что экскурсия существует и принадлежит пользователю
    excursion = db.query(Excursion).filter_by(id=excursion_id).first()
    if not excursion:
        raise HTTPException(status_code=404, detail="Экскурсия не найдена")
    if excursion.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы не владелец экскурсии")

    # Обрабатываем изображение
    image_url = None
    if image:
        ext = image.filename.split(".")[-1]
        filename = f"{uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        with open(filepath, "wb") as f:
            content = await image.read()
            f.write(content)
        image_url = f"/static/images/{filename}"

    waypoint = Waypoint(
        excursion_id=excursion_id,
        name=name,
        description=description,
        latitude=latitude,
        longitude=longitude,
        order_index=order_index,
        image_url=image_url
    )

    db.add(waypoint)
    db.commit()
    db.refresh(waypoint)
    return waypoint

@router.get("/excursions/{excursion_id}/waypoints", response_model=List[WaypointOut])
def get_waypoints_for_excursion(excursion_id: int, db: Session = Depends(get_db)):
    waypoints = db.query(Waypoint).filter(Waypoint.excursion_id == excursion_id).order_by(Waypoint.order_index).all()
    return waypoints