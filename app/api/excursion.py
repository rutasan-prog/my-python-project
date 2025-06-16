from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
import os
import shutil
from app.db.session import SessionLocal
from app.schemas.excursion import ExcursionCreate, ExcursionOut
from app.models.excursion import Excursion
from app.auth.dependencies import get_current_user
from app.models.user import User
from typing import List
from app.schemas.excursion import ExcursionOut
from app.models.excursion import ExcursionStatus
from fastapi import status as http_status
from app.schemas.excursion import ExcursionCreateFull
from app.models.waypoint import Waypoint
from sqlalchemy import func
from app.models.review import Review
from sqlalchemy.orm import joinedload
from app.schemas.user import UserOut
from sqlalchemy import or_
import json

router = APIRouter()

UPLOAD_FOLDER = "static/images"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/excursions/create-full")
async def create_excursion_full(
    title: str = Form(...),
    description: str = Form(""),
    image: UploadFile = File(None),
    points: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    files: list[UploadFile] = File([])  # все изображения точек под ключами типа point_images_0, point_images_1 и т.п.
):
    # Сохраняем картинку экскурсии
    image_url = None
    if image:
        ext = image.filename.split(".")[-1]
        filename = f"{uuid4().hex}.{ext}"
        path = f"static/images/{filename}"
        with open(path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_url = f"/static/images/{filename}"

    # Создание экскурсии
    excursion = Excursion(
        title=title,
        description=description,
        image_url=image_url,
        author_id=current_user.id,
        status=ExcursionStatus.draft
    )
    db.add(excursion)
    db.commit()
    db.refresh(excursion)

    # Парсинг точек
    point_list = json.loads(points)
    for i, point in enumerate(point_list):
        point_image_url = None
        if i < len(files):
            image_file = files[i]
            if image_file and image_file.filename:
                ext = image_file.filename.split(".")[-1]
                filename = f"{uuid4().hex}.{ext}"
                path = f"static/images/{filename}"
                with open(path, "wb") as buffer:
                    shutil.copyfileobj(image_file.file, buffer)
                point_image_url = f"/static/images/{filename}"

        wp = Waypoint(
            excursion_id=excursion.id,
            name=point["name"],
            description=point.get("description"),
            latitude=point["latitude"],
            longitude=point["longitude"],
            order_index=point.get("order_index", i),
            image_url=point_image_url
        )
        db.add(wp)

    db.commit()
    return {"message": "Экскурсия создана", "excursion_id": excursion.id}

@router.post("/excursions/create")
def create_excursion(data: ExcursionCreateFull, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    excursion = Excursion(
        title=data.title,
        description=data.description,
        author_id=current_user.id,
        status=ExcursionStatus.draft
    )
    db.add(excursion)
    db.commit()
    db.refresh(excursion)

    for index, point in enumerate(data.points):
        waypoint = Waypoint(
            excursion_id=excursion.id,
            name=point.name,
            description=point.description,
            latitude=point.latitude,
            longitude=point.longitude,
            order_index=index
        )
        db.add(waypoint)

    db.commit()
    return {"message": "Экскурсия и точки успешно созданы", "id": excursion.id}

@router.post("/excursions/create-with-image", response_model=ExcursionOut)
async def create_excursion_with_image(
    title: str = Form(...),
    description: str = Form(""),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Сохраняем картинку
    ext = image.filename.split(".")[-1]
    filename = f"{uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    with open(filepath, "wb") as f:
        content = await image.read()
        f.write(content)

    # Создаем экскурсию
    excursion = Excursion(
        title=title,
        description=description,
        image_url=f"/static/images/{filename}",
        author_id=current_user.id
    )
    db.add(excursion)
    db.commit()
    db.refresh(excursion)
    return excursion

@router.get("/excursions/all", response_model=List[ExcursionOut])
def get_all_excursions(db: Session = Depends(get_db)):
    excursions = db.query(Excursion).filter(Excursion.status == ExcursionStatus.approved).all()
    result = []

    for ex in excursions:
        avg = db.query(func.avg(Review.rating)).filter(Review.excursion_id == ex.id).scalar()
        result.append(ExcursionOut(
            id=ex.id,
            title=ex.title,
            description=ex.description,
            author_id=ex.author_id,
            status=ex.status,
            image_url=ex.image_url,
            average_rating=round(avg, 2) if avg else None,
            created_at=ex.created_at
        ))

    return result


@router.get("/admin/excursions", response_model=List[ExcursionOut])
def get_all_excursions_admin(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Только для админа")

    excursions = db.query(Excursion) \
        .filter(or_(
            Excursion.status == ExcursionStatus.pending,
            Excursion.status == ExcursionStatus.approved
        )) \
        .options(joinedload(Excursion.author)) \
        .order_by(Excursion.status, Excursion.created_at.desc()) \
        .all()

    result = []
    for ex in excursions:
        result.append(ExcursionOut(
            id=ex.id,
            title=ex.title,
            description=ex.description,
            image_url=ex.image_url,
            status=ex.status,
            average_rating=None,
            author_id=ex.author_id,
            author=UserOut.model_validate(ex.author, from_attributes=True) if ex.author else None,
            created_at = ex.created_at
        ))
    return result



@router.post("/admin/excursions/{id}/approve")
def approve_excursion(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Только для админа")

    excursion = db.query(Excursion).filter(Excursion.id == id).first()
    if not excursion:
        raise HTTPException(status_code=404, detail="Экскурсия не найдена")

    excursion.status = ExcursionStatus.approved
    db.commit()
    return {"message": "Экскурсия одобрена"}


@router.post("/admin/excursions/{id}/reject")
def reject_excursion(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Только для админа")

    excursion = db.query(Excursion).filter(Excursion.id == id).first()
    if not excursion:
        raise HTTPException(status_code=404, detail="Экскурсия не найдена")

    excursion.status = ExcursionStatus.draft
    db.commit()
    return {"message": "Экскурсия возвращена в черновики"}

@router.post("/excursions/{id}/submit")
def submit_excursion(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    excursion = db.query(Excursion).filter(Excursion.id == id).first()
    if not excursion or excursion.author_id != current_user.id:
        raise HTTPException(status_code=404, detail="Экскурсия не найдена или не ваша")

    if excursion.status != ExcursionStatus.draft:
        raise HTTPException(status_code=400, detail="Уже отправлена или одобрена")

    excursion.status = ExcursionStatus.pending
    db.commit()
    return {"message": "Экскурсия отправлена на модерацию"}

@router.get("/my/excursions", response_model=List[ExcursionOut])
def get_my_excursions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Excursion)\
             .filter(Excursion.author_id == current_user.id)\
             .order_by(Excursion.created_at.desc())\
             .all()

@router.post("/excursions/{id}/edit-full")
async def edit_excursion_full(
    id: int,
    title: str = Form(...),
    description: str = Form(""),
    image: UploadFile = File(None),
    points: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    files: list[UploadFile] = File([])
):
    excursion = db.query(Excursion).filter_by(id=id, author_id=current_user.id).first()
    if not excursion:
        raise HTTPException(status_code=404, detail="Экскурсия не найдена или не ваша")

    if excursion.status == ExcursionStatus.approved:
        excursion.status = ExcursionStatus.draft

    if image:
        ext = image.filename.split(".")[-1]
        filename = f"{uuid4().hex}.{ext}"
        path = f"static/images/{filename}"
        with open(path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        excursion.image_url = f"/static/images/{filename}"

    excursion.title = title
    excursion.description = description

    db.query(Waypoint).filter(Waypoint.excursion_id == excursion.id).delete()

    point_list = json.loads(points)
    for i, point in enumerate(point_list):
        point_image_url = None
        if i < len(files):
            image_file = files[i]
            if image_file and image_file.filename:
                ext = image_file.filename.split(".")[-1]
                filename = f"{uuid4().hex}.{ext}"
                path = f"static/images/{filename}"
                with open(path, "wb") as buffer:
                    shutil.copyfileobj(image_file.file, buffer)
                point_image_url = f"/static/images/{filename}"

        wp = Waypoint(
            excursion_id=excursion.id,
            name=point["name"],
            description=point.get("description"),
            latitude=point["latitude"],
            longitude=point["longitude"],
            order_index=point.get("order_index", i),
            image_url=point_image_url
        )
        db.add(wp)

    db.commit()
    return {"message": "Экскурсия обновлена", "excursion_id": excursion.id}