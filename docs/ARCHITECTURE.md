# Architecture Deep Dive

## System Design

### Core Principles

1. **Privacy-first** — No user tracking, no analytics, no accounts required
2. **Offline-capable** — Camera data cached locally, routes computed client-side if possible
3. **Data-driven** — Everything hinges on OSM data quality; design for incompleteness
4. **Modular** — Routing engine is swappable (Valhalla, OSRM, GraphHopper)

---

## Component Details

### 1. Data Layer

**Source:** OpenStreetMap via Overpass API

**Camera data schema (from OSM):**
```
node["man_made"="surveillance"]["surveillance:type"="ALPR"]
```

**Relevant OSM tags:**
| Tag | Meaning | Example |
|-----|---------|---------|
| `surveillance:type` | What's watching | `ALPR`, `camera`, `gunshot_detector` |
| `camera:direction` | Facing direction (degrees) | `45` (NE), `270` (W) |
| `camera:type` | Camera form factor | `fixed`, `dome`, `panning` |
| `operator` | Who runs it | `Flock Safety`, `City of X` |

**Data flow:**
```
Overpass API → Parse → PostGIS (cached) → Spatial queries
     ↓
  Periodic sync (daily)
     ↓
  Local cache (Redis, 24h TTL)
```

---

### 2. Routing Engine

**Engine:** Valhalla (self-hosted)

**Why Valhalla?**
- Supports custom costing models (the key feature)
- Can run locally (no API keys, no rate limits)
- Good performance for interactive use
- Written in C++, handles large graphs well

**Custom costing model: `camera_penalty`**

The costing model modifies edge weights in the road graph based on proximity to cameras.

```cpp
// Pseudocode for Valhalla custom costing
float CameraPenaltyCosting::EdgeCost(const DirectedEdge* edge, 
                                      const CameraData& cameras) {
    float base_cost = edge->length() / edge->speed();
    
    // Find cameras near this edge
    auto nearby = cameras.FindNear(edge->centroid(), 200_meters);
    
    float penalty = 0;
    for (auto& cam : nearby) {
        float distance = DistanceToCamera(edge, cam);
        
        if (InFieldOfView(edge->heading(), cam)) {
            // Directly in camera's field of view
            if (distance < 50_meters) {
                penalty += 5000;  // Heavy: avoid this edge
            } else if (distance < 150_meters) {
                penalty += 1000;  // Moderate penalty
            }
        }
        
        // General proximity penalty (even if not in FOV)
        if (distance < 200_meters) {
            penalty += 100;
        }
    }
    
    return base_cost + penalty;
}
```

**Field-of-view calculation:**
```python
def in_field_of_view(edge_heading: float, camera: Camera) -> bool:
    """
    Check if a road segment is within a camera's field of view.
    
    Args:
        edge_heading: Direction of travel on the road segment (degrees)
        camera: Camera with direction and FOV angle
    
    Returns:
        True if the road segment is visible to the camera
    """
    # ALPR cameras typically have ~40-60° FOV for plate reading
    # We use 180° as conservative estimate (camera sees both directions)
    fov_degrees = camera.get('fov', 180)
    cam_direction = camera['direction']
    
    angle_diff = abs(edge_heading - cam_direction) % 360
    if angle_diff > 180:
        angle_diff = 360 - angle_diff
    
    return angle_diff <= fov_degrees / 2
```

---

### 3. API Layer

**Framework:** FastAPI (Python)

**Why FastAPI?**
- Async support (Overpass API calls are I/O bound)
- Auto-generated OpenAPI docs
- Pydantic validation
- Easy Valhalla integration via HTTP client

**Key endpoints:**

```
POST /api/v1/route
  Calculate route with camera avoidance

GET  /api/v1/cameras
  Get cameras in bounding box

GET  /api/v1/stats
  Camera density statistics for an area

POST /api/v1/sync
  Trigger camera data refresh (admin)
```

See `docs/API_DESIGN.md` for full specification.

---

### 4. Frontend

**Stack:** Vue 3 + Vite + Leaflet

**Why Vue + Leaflet?**
- DeFlock already uses this stack (code reuse possible)
- Leaflet is lightweight and free (no Mapbox API key needed)
- Vue 3 Composition API for clean state management

**Key features:**
- Interactive map with camera markers
- Route input (start/end)
- "Avoid cameras" toggle
- Route comparison panel (time vs exposure)
- Camera density heatmap (optional)

**UI mockup flow:**
```
┌─────────────────────────────────────────┐
│  [Start] → [End]  │  ☑ Avoid cameras   │
│                   │  [Calculate Route]  │
├─────────────────────────────────────────┤
│                                         │
│           ┌───┐                         │
│          / 📷  \    ← Route A           │
│    Start ●─────●───● End                │
│          \  📷 /                        │
│           └───┘    ← Route B            │
│                                         │
│  Route A: 12 min, 3 cameras             │
│  Route B: 18 min, 0 cameras  ← Selected│
│                                         │
└─────────────────────────────────────────┘
```

---

## Data Flow

```
User requests route
        │
        ▼
┌───────────────┐     ┌──────────────┐
│  FastAPI       │────▶│  PostGIS     │
│  /api/v1/route │     │  Get cameras │
└───────┬───────┘     │  in route    │
        │              │  bounding box│
        │              └──────────────┘
        ▼
┌───────────────┐
│  Valhalla      │
│  Custom route  │
│  with camera   │
│  penalties     │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│  Response      │
│  ├─ Route geo  │
│  ├─ Camera     │
│  │  exposure   │
│  └─ Time       │
└───────────────┘
```

---

## Deployment

**Development:** Docker Compose
```yaml
services:
  valhalla:    # Routing engine
  postgis:     # Camera data + spatial queries
  redis:       # Cache
  api:         # FastAPI backend
  frontend:    # Vue dev server
```

**Production options:**
- Self-hosted (VPS with 8GB+ RAM for Valhalla)
- Fly.io / Railway (containerized)
- AWS (ECS + RDS PostGIS)

---

## Performance Considerations

| Operation | Target | Strategy |
|-----------|--------|----------|
| Camera query | <50ms | PostGIS spatial index, Redis cache |
| Route calculation | <2s | Valhalla local instance, pre-built tiles |
| Map render | <500ms | Vector tiles, lazy loading |

**Scaling:**
- Camera data: ~500KB per US state (tiny)
- Valhalla tiles: ~2GB per US state
- Route caching: Redis with 1h TTL for popular routes

---

## Open Questions

1. **Penalty tuning** — How aggressive should avoidance be? Configurable levels?
2. **Fallback behavior** — What if all routes pass cameras? Show anyway with warning?
3. **Real-time data** — How fresh does camera data need to be? Daily sync OK?
4. **Mobile app** — Native (Flutter) or PWA? PWA is faster to ship.
5. **Multi-modal** — Walking/cycling routes too? Different camera exposure profiles.
