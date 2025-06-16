from pydantic import BaseModel

class WaypointCreate(BaseModel):
    name: str
    description: str | None = None
    latitude: float
    longitude: float
    order_index: int = 0

class WaypointOut(WaypointCreate):
    id: int
    image_url: str | None = None

    class Config:
        from_attributes = True
