from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1")


class Coordinate(BaseModel):
    lat: float
    lon: float


class RouteRequest(BaseModel):
    start: Coordinate
    end: Coordinate
    avoidance_level: str = "balanced"
    alternatives: int = 3
    mode: str = "auto"


class CameraExposure(BaseModel):
    total_cameras: int
    cameras_in_fov: int
    exposure_score: float
    cameras: list


class Route(BaseModel):
    id: str
    geometry: str
    distance_meters: float
    duration_seconds: float
    camera_exposure: CameraExposure
    is_recommended: bool


@router.post("/route")
async def calculate_route(request: RouteRequest):
    pass
