# Quick Start: Weekend MVP

## The 80/20 Approach

This gets you a working prototype in a weekend without modifying Valhalla.

### Strategy

Instead of custom routing, use standard Valhalla to generate multiple route options, then score and rank them by camera exposure.

```
Standard routes → Score by camera proximity → Rank → Display best options
```

---

## Day 1: Get Camera Data + Display

### Step 1: Install Docker

```bash
# Verify Docker is installed
docker --version
docker compose version
```

### Step 2: Start PostGIS

```bash
cd deflock-nav
docker compose up -d postgis
```

### Step 3: Load Camera Data

```bash
# Download cameras for your area via Overpass
python scripts/download_cameras.py --bbox "-74.1,40.7,-73.9,40.8"

# Or for entire US (slow, ~50K cameras)
python scripts/download_cameras.py --country US
```

### Step 4: View on Map

```bash
cd src/frontend
npm install
npm run dev
```

You should see cameras on a Leaflet map.

---

## Day 2: Add Routing

### Step 1: Start Valhalla

```bash
# Download OSM extract for your area
wget https://download.geofabrik.de/north-america/us/new-york-latest.osm.pbf

# Build Valhalla tiles
docker compose run valhalla valhalla_build_tiles -c /valhalla.json new-york-latest.osm.pbf

# Start Valhalla
docker compose up -d valhalla
```

### Step 2: Test Basic Routing

```bash
curl -X POST http://localhost:8002/route \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {"lat": 40.7128, "lon": -74.0060},
      {"lat": 40.7484, "lon": -73.9857}
    ],
    "costing": "auto"
  }'
```

### Step 3: Build Scoring Logic

```python
# src/routing/scorer.py
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points

def score_route(route_geometry: list, cameras: list) -> dict:
    """
    Score a route by camera exposure.
    
    Args:
        route_geometry: List of [lon, lat] coordinates
        cameras: List of camera dicts with lat/lon
    
    Returns:
        {
            "total_cameras": int,
            "cameras_in_fov": int,
            "exposure_score": float,
            "cameras": list
        }
    """
    line = LineString(route_geometry)
    exposure = []
    
    for cam in cameras:
        cam_point = Point(cam["lon"], cam["lat"])
        dist = line.distance(cam_point) * 111000  # Rough meters
        
        if dist < 200:  # Within 200m
            weight = 1 - (dist / 200)
            
            # Check FOV if direction known
            in_fov = False
            if cam.get("camera_direction"):
                # Simplified: check if route passes "in front of" camera
                in_fov = check_fov(line, cam_point, cam["camera_direction"])
                if in_fov:
                    weight *= 3
            
            exposure.append({
                "osm_id": cam["osm_id"],
                "lat": cam["lat"],
                "lon": cam["lon"],
                "operator": cam.get("operator"),
                "distance_meters": dist,
                "in_fov": in_fov,
                "weight": weight
            })
    
    return {
        "total_cameras": len(exposure),
        "cameras_in_fov": sum(1 for e in exposure if e["in_fov"]),
        "exposure_score": sum(e["weight"] for e in exposure),
        "cameras": exposure
    }

def check_fov(route_line, cam_point, direction, fov_angle=180):
    """Check if route passes through camera's field of view."""
    # Find closest point on route to camera
    _, nearest = nearest_points(route_line, cam_point)
    
    # Get route heading at that point
    coords = list(route_line.coords)
    for i in range(len(coords) - 1):
        if Point(coords[i]).distance(nearest) < 0.001:
            heading = get_heading(coords[i], coords[i+1])
            diff = abs(heading - direction) % 360
            if diff > 180:
                diff = 360 - diff
            return diff <= fov_angle / 2
    
    return False
```

### Step 4: Wire It Up

```python
# src/api/main.py (simplified)
import httpx
from fastapi import FastAPI

app = FastAPI()
VALHALLA_URL = "http://localhost:8002"

@app.post("/api/v1/route")
async def calculate_route(start: dict, end: dict):
    # Get 3 routes from Valhalla
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{VALHALLA_URL}/route", json={
            "locations": [
                {"lat": start["lat"], "lon": start["lon"]},
                {"lat": end["lat"], "lon": end["lon"]}
            ],
            "costing": "auto",
            "alternates": 3
        })
    
    valhalla_routes = response.json()["alternates"]
    
    # Get cameras in bounding box
    bbox = get_bbox(start, end)
    cameras = await get_cameras_in_bbox(bbox)
    
    # Score each route
    scored_routes = []
    for route in valhalla_routes:
        geometry = decode_polyline(route["shape"])
        score = score_route(geometry, cameras)
        scored_routes.append({
            "geometry": route["shape"],
            "distance_meters": route["trip"]["legs"][0]["length"] * 1000,
            "duration_seconds": route["trip"]["legs"][0]["time"],
            "camera_exposure": score
        })
    
    # Sort by exposure (lowest first)
    scored_routes.sort(key=lambda r: r["camera_exposure"]["exposure_score"])
    
    # Mark best as recommended
    scored_routes[0]["is_recommended"] = True
    
    return {"routes": scored_routes}
```

---

## Day 2 (continued): Frontend

```vue
<!-- src/frontend/src/App.vue -->
<template>
  <div id="app">
    <div class="controls">
      <input v-model="startLat" placeholder="Start lat" />
      <input v-model="startLon" placeholder="Start lon" />
      <input v-model="endLat" placeholder="End lat" />
      <input v-model="endLon" placeholder="End lon" />
      <button @click="calculateRoute">Find Route</button>
      
      <div v-if="routes.length" class="route-list">
        <div 
          v-for="route in routes" 
          :key="route.id"
          :class="{ recommended: route.is_recommended }"
          @click="selectRoute(route)"
        >
          <strong>{{ route.is_recommended ? '⭐ ' : '' }}</strong>
          {{ formatTime(route.duration_seconds) }} |
          {{ route.camera_exposure.total_cameras }} cameras |
          Score: {{ route.camera_exposure.exposure_score.toFixed(1) }}
        </div>
      </div>
    </div>
    
    <l-map :zoom="13" :center="[40.7128, -74.006]">
      <l-tile-layer :url="tileUrl" />
      
      <!-- Camera markers -->
      <l-circle-marker
        v-for="cam in cameras"
        :key="cam.osm_id"
        :lat-lng="[cam.lat, cam.lon]"
        :radius="5"
        color="red"
      />
      
      <!-- Route lines -->
      <l-polyline
        v-for="route in routes"
        :key="route.id"
        :lat-lngs="decodeRoute(route.geometry)"
        :color="route.is_recommended ? 'green' : 'gray'"
        :weight="route.is_recommended ? 5 : 3"
      />
    </l-map>
  </div>
</template>
```

---

## What You Get (MVP)

```
Working features:
✅ Camera data from OSM (via Overpass)
✅ Multiple route options from Valhalla
✅ Camera exposure scoring per route
✅ Route comparison UI
✅ Recommended route highlighting
✅ Camera markers on map

Not yet (full app):
❌ Custom routing engine penalties
❌ Real-time rerouting
❌ Field-of-view calculations
❌ Camera density heatmap
❌ Mobile app
❌ Offline support
```

---

## From MVP to Full App

Once the MVP works, migrate to the full architecture:

```
Phase 1 (Weekend MVP):
  Standard Valhalla + scoring layer

Phase 2 (Week 1-2):
  Add Valhalla Lua costing script
  
Phase 3 (Week 3-4):
  Frontend polish, camera filtering, stats
  
Phase 4 (Week 5-6):
  Caching, performance optimization, deployment
```

---

## Troubleshooting

### Valhalla won't start
- Check available RAM (needs ~2GB for small extract, ~8GB for US)
- Verify OSM extract downloaded correctly
- Check logs: `docker compose logs valhalla`

### No cameras showing
- Verify Overpass query: test at [overpass-turbo.eu](https://overpass-turbo.eu/)
- Check PostGIS: `psql -c "SELECT count(*) FROM cameras;"`
- Some areas have genuinely zero mapped cameras

### Routes not calculating
- Test Valhalla directly: `curl http://localhost:8002/status`
- Check coordinates are in the downloaded region
- Verify API response format matches expected schema
