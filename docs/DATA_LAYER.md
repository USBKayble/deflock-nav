# Data Layer

## Data Sources

### 1. OpenStreetMap — Camera Data

DeFlock stores ALPR locations in OpenStreetMap using the `man_made=surveillance` tag schema.

**Overpass API query:**
```overpass
[out:json][timeout:60];
(
  node["man_made"="surveillance"]["surveillance:type"="ALPR"]({{bbox}});
  node["man_made"="surveillance"]["surveillance:type"="camera"]["operator"~"Flock",i]({{bbox}});
);
out body;
>;
out skel qt;
```

**Response format:**
```json
{
  "elements": [
    {
      "type": "node",
      "id": 123456789,
      "lat": 40.7128,
      "lon": -74.0060,
      "tags": {
        "man_made": "surveillance",
        "surveillance:type": "ALPR",
        "camera:direction": "90",
        "camera:type": "fixed",
        "operator": "Flock Safety"
      }
    }
  ]
}
```

### 2. OpenStreetMap — Road Network

Download OSM extracts for road graph:
- Source: [Geofabrik](https://download.geofabrik.de/) or [BBBike](https://extract.bbbike.org/)
- Format: `.osm.pbf`
- Used by Valhalla to build routing tiles

---

## Data Pipeline

```
┌─────────────────┐
│  Overpass API    │ ──┐
│  (camera data)   │   │
└─────────────────┘   │
                      ▼
┌─────────────────────────────────┐
│  Sync Script (Python)           │
│  ├─ Query Overpass by region    │
│  ├─ Parse response              │
│  ├─ Validate tags               │
│  └─ Upsert to PostGIS           │
└─────────────────┬───────────────┘
                  │
                  ▼
┌─────────────────────────────────┐
│  PostGIS Database               │
│  ├─ cameras table (spatial)     │
│  ├─ regions table               │
│  └─ sync_log table              │
└─────────────────┬───────────────┘
                  │
                  ▼
┌─────────────────────────────────┐
│  Redis Cache                    │
│  ├─ Camera clusters by region   │
│  └─ TTL: 24 hours               │
└─────────────────────────────────┘
```

---

## Database Schema

### PostGIS

```sql
-- Main camera table
CREATE TABLE cameras (
    osm_id BIGINT PRIMARY KEY,
    location GEOMETRY(Point, 4326) NOT NULL,
    surveillance_type VARCHAR(50),      -- ALPR, camera, gunshot_detector
    camera_direction INTEGER,           -- 0-360 degrees, NULL if unknown
    camera_type VARCHAR(50),            -- fixed, dome, panning
    operator VARCHAR(255),              -- Flock Safety, City of X, etc.
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    
    -- Spatial index for fast proximity queries
    CONSTRAINT cameras_location_idx USING GIST (location)
);

-- Index for filtering by type
CREATE INDEX cameras_type_idx ON cameras (surveillance_type);

-- Sync log
CREATE TABLE sync_log (
    id SERIAL PRIMARY KEY,
    region VARCHAR(100),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    cameras_found INTEGER,
    cameras_updated INTEGER,
    status VARCHAR(20)  -- success, failed, partial
);
```

### Spatial Queries

```sql
-- Find cameras within 200m of a point
SELECT osm_id, surveillance_type, camera_direction, operator,
       ST_Distance(location::geography, ST_Point(-74.006, 40.7128)::geography) as distance_m
FROM cameras
WHERE ST_DWithin(location::geography, ST_Point(-74.006, 40.7128)::geography, 200)
ORDER BY distance_m;

-- Find cameras along a route (line)
SELECT c.osm_id, c.surveillance_type, c.camera_direction
FROM cameras c
WHERE ST_DWithin(c.location::geography, 
    ST_GeomFromText('LINESTRING(-74.006 40.7128, -73.985 40.748)', 4326)::geography, 
    50);
```

---

## Sync Strategy

### Frequency
- **Full sync:** Weekly (re-query entire region)
- **Incremental:** Daily (only new/updated nodes)
- **On-demand:** Via `/api/v1/sync` endpoint

### Implementation

```python
# scripts/sync_cameras.py
import httpx
from datetime import datetime

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Query for US bounding box (or per-state)
QUERY = """
[out:json][timeout:120];
area["ISO3166-1"="US"]->.usa;
(
  node["man_made"="surveillance"]["surveillance:type"="ALPR"](area.usa);
  node["man_made"="surveillance"]["surveillance:type"="camera"]["operator"~"Flock",i](area.usa);
);
out body;
>;
out skel qt;
"""

async def sync_cameras():
    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(OVERPASS_URL, data={"data": QUERY})
        data = response.json()
        
        cameras = []
        for element in data["elements"]:
            if element["type"] == "node" and "tags" in element:
                cameras.append({
                    "osm_id": element["id"],
                    "lat": element["lat"],
                    "lon": element["lon"],
                    "surveillance_type": element["tags"].get("surveillance:type"),
                    "camera_direction": element["tags"].get("camera:direction"),
                    "operator": element["tags"].get("operator"),
                })
        
        # Upsert to PostGIS
        await upsert_cameras(cameras)
        print(f"Synced {len(cameras)} cameras")
```

---

## Caching

### Redis Cache Layer

```python
import redis
import json

r = redis.Redis()

def get_cameras_in_bbox(bbox: tuple, refresh=False):
    """
    Get cameras in bounding box with caching.
    
    bbox: (min_lon, min_lat, max_lon, max_lat)
    """
    cache_key = f"cameras:{bbox}"
    
    if not refresh:
        cached = r.get(cache_key)
        if cached:
            return json.loads(cached)
    
    # Query PostGIS
    cameras = query_postgis_for_bbox(bbox)
    
    # Cache for 24 hours
    r.setex(cache_key, 86400, json.dumps(cameras))
    
    return cameras
```

---

## Data Quality Considerations

### Known Issues

1. **Incomplete coverage** — OSM data is crowdsourced; some areas have zero cameras mapped
2. **Stale data** — Cameras get moved/removed; no automated detection of changes
3. **Missing tags** — Many cameras lack `camera:direction`; can't compute FOV without it
4. **Duplicates** — Same camera might be mapped twice by different contributors

### Mitigations

| Issue | Mitigation |
|-------|------------|
| Incomplete | Show "data confidence" indicators in UI; don't promise zero cameras |
| Stale data | Regular syncs; flag cameras not updated in 6+ months |
| Missing direction | Assume 360° FOV (conservative) when direction unknown |
| Deduplication | Merge nodes within 10m of each other with same operator |

---

## Alternative Data Sources

If OSM coverage is too sparse in your area:

1. **Flock's own map** — Some communities publish their camera locations
2. **FOIA requests** — Law enforcement must disclose ALPR deployments
3. **Community reporting** — DeFlock app already handles this
4. **Computer vision** — Dashcam footage analysis (experimental, privacy concerns)
