import httpx
import json
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from src.api.database import get_db
from src.api.models import Camera
from src.api.config import settings

router = APIRouter(prefix="/api/v1")

async def fetch_cameras_from_overpass(bbox: str) -> list[dict]:
    min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
    query = f"""
    [out:json][timeout:30];
    (
      node["man_made"="surveillance"]["surveillance:type"="ALPR"]({min_lat},{min_lon},{max_lat},{max_lon});
      node["man_made"="surveillance"]["surveillance:type"="camera"]["operator"~"Flock",i]({min_lat},{min_lon},{max_lat},{max_lon});
    );
    out body;
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                settings.OVERPASS_URL,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data={'data': query}
            )
            if res.status_code != 200:
                return []
            data = res.json()
    except httpx.RequestError:
        return []

    cameras = []
    for el in data.get('elements', []):
        if el.get('type') == 'node' and el.get('tags'):
            tags = el['tags']
            direction = None
            if 'camera:direction' in tags:
                try:
                    direction = int(tags['camera:direction'])
                except ValueError:
                    pass

            cameras.append({
                "osm_id": el['id'],
                "lat": el['lat'],
                "lon": el['lon'],
                "type": tags.get('surveillance:type', 'camera'),
                "direction": direction,
                "operator": tags.get('operator', 'Unknown')
            })
    return cameras

async def sync_cameras_to_db(db: AsyncSession, bbox: str):
    cameras = await fetch_cameras_from_overpass(bbox)
    if not cameras:
        return

    for cam in cameras:
        point = f"SRID=4326;POINT({cam['lon']} {cam['lat']})"
        stmt = text("""
            INSERT INTO cameras (osm_id, location, surveillance_type, camera_direction, camera_type, operator, last_updated)
            VALUES (:osm_id, ST_GeomFromEWKT(:location), :surveillance_type, :camera_direction, :camera_type, :operator, NOW())
            ON CONFLICT (osm_id) DO UPDATE SET
                location = EXCLUDED.location,
                surveillance_type = EXCLUDED.surveillance_type,
                camera_direction = EXCLUDED.camera_direction,
                camera_type = EXCLUDED.camera_type,
                operator = EXCLUDED.operator,
                last_updated = NOW()
        """)
        await db.execute(stmt, {
            "osm_id": cam["osm_id"],
            "location": point,
            "surveillance_type": "ALPR" if cam["type"] == "ALPR" else "camera",
            "camera_direction": cam["direction"],
            "camera_type": cam["type"],
            "operator": cam["operator"]
        })
    await db.commit()

@router.get("/cameras")
async def get_cameras(
    bbox: str = Query(..., description="min_lon,min_lat,max_lon,max_lat"),
    type: str | None = Query(None),
    operator: str | None = Query(None),
    limit: int = Query(500, le=5000),
    db: AsyncSession = Depends(get_db)
):
    try:
        min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid bbox format")

    # First, always try to sync with Overpass to ensure we have the latest data
    # (In a true production app, we would cache this sync or run it asynchronously)
    try:
        await sync_cameras_to_db(db, bbox)
    except Exception as e:
        print(f"Failed to sync with Overpass: {e}")
        # Proceed with what we have in DB

    # Query PostGIS for cameras in bbox
    bbox_poly = f"SRID=4326;POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"

    query = select(
        Camera.osm_id,
        func.ST_Y(Camera.location).label('lat'),
        func.ST_X(Camera.location).label('lon'),
        Camera.camera_type.label('type'),
        Camera.camera_direction.label('direction'),
        Camera.operator
    ).where(
        func.ST_Intersects(Camera.location, func.ST_GeomFromEWKT(bbox_poly))
    ).limit(limit)

    result = await db.execute(query)
    cameras = []
    for row in result:
        cameras.append({
            "osmId": row.osm_id,
            "lat": row.lat,
            "lon": row.lon,
            "type": row.type,
            "direction": row.direction,
            "operator": row.operator
        })

    return cameras

@router.get("/cameras/{osm_id}")
async def get_camera(osm_id: int, db: AsyncSession = Depends(get_db)):
    query = select(
        Camera.osm_id,
        func.ST_Y(Camera.location).label('lat'),
        func.ST_X(Camera.location).label('lon'),
        Camera.camera_type.label('type'),
        Camera.camera_direction.label('direction'),
        Camera.operator
    ).where(Camera.osm_id == osm_id)

    result = await db.execute(query)
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Camera not found")

    return {
        "osmId": row.osm_id,
        "lat": row.lat,
        "lon": row.lon,
        "type": row.type,
        "direction": row.direction,
        "operator": row.operator
    }

@router.get("/stats")
async def get_stats(bbox: str = Query(...)):
    # Stubbed
    return {"status": "ok"}
