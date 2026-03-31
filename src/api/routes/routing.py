import httpx
import math
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.api.config import settings

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

def decode_polyline(polyline_str: str) -> list[list[float]]:
    # Implementation of Google's polyline algorithm
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {'latitude': 0, 'longitude': 0}

    while index < len(polyline_str):
        for unit in ['latitude', 'longitude']:
            shift, result = 0, 0
            while True:
                byte = ord(polyline_str[index]) - 63
                index += 1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20:
                    break

            if (result & 1):
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = (result >> 1)

        lat += changes['latitude']
        lng += changes['longitude']

        coordinates.append([lat / 100000.0, lng / 100000.0])

    return coordinates

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371e3 # metres
    phi1 = lat1 * math.pi/180
    phi2 = lat2 * math.pi/180
    delta_phi = (lat2-lat1) * math.pi/180
    delta_lambda = (lon2-lon1) * math.pi/180

    a = math.sin(delta_phi/2) * math.sin(delta_phi/2) + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda/2) * math.sin(delta_lambda/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

def point_to_segment_distance(point, line_start, line_end) -> float:
    lat, lon = point
    lat1, lon1 = line_start
    lat2, lon2 = line_end

    # Distance between points
    dist12 = haversine(lat1, lon1, lat2, lon2)
    dist13 = haversine(lat1, lon1, lat, lon)
    dist23 = haversine(lat2, lon2, lat, lon)

    # Check if the angle is obtuse
    if (dist12 == 0): return dist13
    if (dist13**2 > dist12**2 + dist23**2): return dist23
    if (dist23**2 > dist12**2 + dist13**2): return dist13

    # Area of triangle
    s = (dist12 + dist13 + dist23) / 2
    # Ensure s - side > 0 to avoid domain error in sqrt
    area = math.sqrt(max(0, s * (s - dist12) * (s - dist13) * (s - dist23)))

    return 2 * area / dist12

def get_heading(start, end) -> float:
    lat1, lon1 = start[0] * math.pi/180, start[1] * math.pi/180
    lat2, lon2 = end[0] * math.pi/180, end[1] * math.pi/180

    y = math.sin(lon2 - lon1) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)

    brng = math.atan2(y, x) * 180 / math.pi
    return (brng + 360) % 360

def in_field_of_view(heading: float, camera_direction: float, fov_angle: float = 120) -> bool:
    diff = abs(heading - camera_direction) % 360
    if diff > 180:
        diff = 360 - diff
    return diff <= fov_angle / 2

def score_route(route: dict, cameras: list[dict]) -> dict:
    exposed = []
    coords = route["geometry_decoded"]

    for cam in cameras:
        min_dist = float('inf')
        is_in_fov = False

        for i in range(len(coords) - 1):
            # point_to_segment_distance expects (lat, lon) for all points
            dist = point_to_segment_distance((cam["lat"], cam["lon"]), coords[i], coords[i+1])
            if dist < min_dist:
                min_dist = dist
                if dist < 200 and cam.get("direction") is not None:
                    heading = get_heading(coords[i], coords[i+1])
                    is_in_fov = in_field_of_view(heading, cam["direction"])

        if min_dist < 200:
            weight = (1 - min_dist / 200) * (3 if is_in_fov else 1)
            exposed.append({
                "osmId": cam["osmId"],
                "lat": cam["lat"],
                "lon": cam["lon"],
                "operator": cam.get("operator", "Unknown"),
                "distanceMeters": round(min_dist),
                "inFov": is_in_fov,
                "weight": weight
            })

    total_cameras = len(exposed)
    cameras_in_fov = len([c for c in exposed if c["inFov"]])
    exposure_score = sum(c["weight"] for c in exposed)
    sorted_cameras = sorted(exposed, key=lambda c: c["distanceMeters"])

    return {
        "total_cameras": total_cameras,
        "cameras_in_fov": cameras_in_fov,
        "exposure_score": exposure_score,
        "cameras": sorted_cameras
    }

@router.post("/route", response_model=list[Route])
async def calculate_route(request: RouteRequest):
    # Get OSRM Routes
    coords_str = f"{request.start.lon},{request.start.lat};{request.end.lon},{request.end.lat}"
    url = f"{settings.OSRM_URL}/route/v1/driving/{coords_str}?overview=full&alternatives={request.alternatives - 1}&geometries=polyline"

    async with httpx.AsyncClient() as client:
        res = await client.get(url)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail="OSRM Error")
        data = res.json()
        if data.get("code") != "Ok":
            raise HTTPException(status_code=400, detail=f"OSRM Error: {data.get('code')}")

    routes = []
    for i, r in enumerate(data.get("routes", [])):
        routes.append({
            "id": f"route-{i}",
            "geometry": r["geometry"],
            "geometry_decoded": decode_polyline(r["geometry"]),
            "distance_meters": r["distance"],
            "duration_seconds": r["duration"]
        })

    # Determine BBox and Fetch Cameras
    padding = 0.02
    min_lon = min(request.start.lon, request.end.lon) - padding
    min_lat = min(request.start.lat, request.end.lat) - padding
    max_lon = max(request.start.lon, request.end.lon) + padding
    max_lat = max(request.start.lat, request.end.lat) + padding
    bbox = f"{min_lon},{min_lat},{max_lon},{max_lat}"

    try:
        from src.api.database import AsyncSessionLocal
        from src.api.routes.cameras import get_cameras
        async with AsyncSessionLocal() as db:
            cameras = await get_cameras(bbox=bbox, type=None, operator=None, limit=500, db=db)
    except Exception as e:
        print(f"Failed to fetch cameras: {e}")
        cameras = []

    # Score Routes
    scored_routes = []
    for r in routes:
        exposure = score_route(r, cameras)
        scored_routes.append({
            "id": r["id"],
            "geometry": r["geometry"],
            "distance_meters": r["distance_meters"],
            "duration_seconds": r["duration_seconds"],
            "camera_exposure": exposure,
            "is_recommended": False
        })

    # Rank Routes
    scored_routes.sort(key=lambda r: r["camera_exposure"]["exposure_score"])
    if scored_routes:
        scored_routes[0]["is_recommended"] = True

    return scored_routes
