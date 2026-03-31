# API Design

## Base URL

```
Development: http://localhost:8000/api/v1
Production:  https://api.deflock-nav.example.com/v1
```

---

## Endpoints

### POST /route

Calculate a route with camera avoidance.

**Request:**
```json
{
  "start": {
    "lat": 40.7128,
    "lon": -74.0060
  },
  "end": {
    "lat": 40.7484,
    "lon": -73.9857
  },
  "avoidance_level": "balanced",
  "alternatives": 3,
  "mode": "auto"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `start` | `{lat, lon}` | Yes | Origin coordinates |
| `end` | `{lat, lon}` | Yes | Destination coordinates |
| `avoidance_level` | string | No | `relaxed`, `balanced`, `strict`, `paranoid` (default: `balanced`) |
| `alternatives` | int | No | Number of alternative routes to return (default: 3) |
| `mode` | string | No | `auto`, `bicycle`, `pedestrian` (default: `auto`) |

**Response:**
```json
{
  "routes": [
    {
      "id": "route-0",
      "geometry": "u{~vFvy|i@...",  // encoded polyline
      "distance_meters": 5420,
      "duration_seconds": 480,
      "camera_exposure": {
        "total_cameras": 3,
        "cameras_in_fov": 1,
        "exposure_score": 4.2,
        "cameras": [
          {
            "osm_id": 123456,
            "lat": 40.7200,
            "lon": -74.0050,
            "operator": "Flock Safety",
            "distance_meters": 45,
            "in_fov": true,
            "direction": 90
          }
        ]
      },
      "is_recommended": false
    },
    {
      "id": "route-1",
      "geometry": "u{~vFvy|i@...",
      "distance_meters": 7100,
      "duration_seconds": 720,
      "camera_exposure": {
        "total_cameras": 0,
        "cameras_in_fov": 0,
        "exposure_score": 0,
        "cameras": []
      },
      "is_recommended": true
    }
  ],
  "selected_route_id": "route-1",
  "avoidance_level": "balanced",
  "metadata": {
    "cameras_in_area": 47,
    "computation_time_ms": 234
  }
}
```

**Errors:**
```json
// 400 - Invalid coordinates
{
  "error": "invalid_coordinates",
  "message": "Start coordinates out of range"
}

// 404 - No route found
{
  "error": "no_route",
  "message": "No route found between points (water body?)"
}

// 503 - Valhalla unavailable
{
  "error": "routing_unavailable",
  "message": "Routing engine temporarily unavailable"
}
```

---

### GET /cameras

Get cameras in a bounding box.

**Request:**
```
GET /cameras?bbox=-74.1,40.7,-73.9,40.8&type=ALPR&limit=1000
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bbox` | string | Yes | `min_lon,min_lat,max_lon,max_lat` |
| `type` | string | No | Filter: `ALPR`, `camera`, `gunshot_detector` |
| `operator` | string | No | Filter by operator (partial match) |
| `limit` | int | No | Max results (default: 500, max: 5000) |
| `updated_since` | string | No | ISO 8601 timestamp filter |

**Response:**
```json
{
  "cameras": [
    {
      "osm_id": 123456,
      "lat": 40.7128,
      "lon": -74.0060,
      "surveillance_type": "ALPR",
      "camera_direction": 90,
      "camera_type": "fixed",
      "operator": "Flock Safety",
      "last_updated": "2026-03-15T10:30:00Z"
    }
  ],
  "total": 47,
  "bbox": [-74.1, 40.7, -73.9, 40.8]
}
```

---

### GET /cameras/{osm_id}

Get details for a specific camera.

**Response:**
```json
{
  "osm_id": 123456,
  "lat": 40.7128,
  "lon": -74.0060,
  "surveillance_type": "ALPR",
  "camera_direction": 90,
  "camera_type": "fixed",
  "operator": "Flock Safety",
  "last_updated": "2026-03-15T10:30:00Z",
  "osm_url": "https://www.openstreetmap.org/node/123456",
  "deflock_url": "https://deflock.me/node/123456"
}
```

---

### GET /stats

Get camera statistics for an area.

**Request:**
```
GET /stats?bbox=-74.1,40.7,-73.9,40.8
```

**Response:**
```json
{
  "bbox": [-74.1, 40.7, -73.9, 40.8],
  "total_cameras": 47,
  "by_type": {
    "ALPR": 38,
    "camera": 7,
    "gunshot_detector": 2
  },
  "by_operator": {
    "Flock Safety": 32,
    "City of New York": 8,
    "Unknown": 7
  },
  "coverage_area_sq_km": 12.5,
  "density_per_sq_km": 3.76,
  "last_sync": "2026-03-31T00:00:00Z"
}
```

---

### POST /admin/sync

Trigger camera data sync (admin only).

**Request:**
```json
{
  "region": "us-northeast",
  "force": false
}
```

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "status": "started",
  "sync_id": "sync-abc123",
  "estimated_completion": "2026-03-31T12:05:00Z"
}
```

---

## Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST /route | 30 | 1 minute |
| GET /cameras | 60 | 1 minute |
| GET /stats | 60 | 1 minute |
| POST /admin/sync | 1 | 1 hour |

**Headers:**
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 28
X-RateLimit-Reset: 1711887600
```

---

## Authentication

Most endpoints are **public** (no auth required). This is a privacy tool — requiring accounts would be hypocritical.

**Admin endpoints** require a bearer token:
```
Authorization: Bearer <token>
```

Token configured via environment variable `ADMIN_TOKEN`.

---

## WebSocket (Future)

For real-time route updates during navigation:

```
ws://localhost:8000/api/v1/route/live

# Client sends:
{"type": "position", "lat": 40.7128, "lon": -74.0060}

# Server sends:
{"type": "camera_alert", "camera": {...}, "distance_meters": 200, "in_fov": true}
{"type": "reroute_suggested", "reason": "camera_ahead", "alternative": {...}}
```

---

## Implementation Notes

### FastAPI Structure

```python
# src/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="DeFlock Nav API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vue dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

# src/api/routes/routing.py
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1")

@router.post("/route")
async def calculate_route(request: RouteRequest):
    # 1. Validate coordinates
    # 2. Query cameras in bounding box (PostGIS + Redis cache)
    # 3. Call Valhalla with custom costing
    # 4. Score routes by camera exposure
    # 5. Return ranked routes
    pass

@router.get("/cameras")
async def get_cameras(bbox: str, type: str = None, limit: int = 500):
    pass

@router.get("/stats")
async def get_stats(bbox: str):
    pass
```

### Pydantic Models

```python
# src/api/models.py
from pydantic import BaseModel
from typing import Optional

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
    cameras: list[Camera]

class Route(BaseModel):
    id: str
    geometry: str
    distance_meters: float
    duration_seconds: float
    camera_exposure: CameraExposure
    is_recommended: bool
```
