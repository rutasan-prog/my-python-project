from fastapi import FastAPI
from app.db.session import SessionLocal
from app.api import auth
from sqlalchemy import text
from fastapi.staticfiles import StaticFiles
from app.api import excursion
from app.api import waypoint
from fastapi.middleware.cors import CORSMiddleware
from app.api import review
# Запуск ниже
"""uvicorn app.main:app --reload"""
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем маршруты из auth.py
app.include_router(auth.router)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(excursion.router)
app.include_router(waypoint.router)
app.include_router(review.router)

# Тест подключения к БД
@app.get("/")
def read_root():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        return {"message": "✅ Подключение к базе успешно!"}
    except Exception as e:
        return {"error": str(e)}



