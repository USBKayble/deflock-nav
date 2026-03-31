# Routing Engine Design

## Overview

The routing engine is the core of DeFlock Nav. It needs to:
1. Calculate optimal routes between two points
2. Penalize road segments near surveillance cameras
3. Balance travel time vs camera exposure
4. Return multiple route options with exposure scores

---

## Engine Choice: Valhalla

### Why Valhalla Over OSRM?

| Feature | Valhalla | OSRM |
|---------|----------|------|
| Custom costing models | ✅ Native support | ❌ Not supported |
| Self-hosted | ✅ | ✅ |
| Performance | Good | Better |
| Dynamic edge weights | ✅ | ❌ (pre-computed) |
| Multi-modal routing | ✅ | Limited |

**Decision:** Valhalla's custom costing is the key differentiator. OSRM pre-computes edge weights, making runtime penalty adjustments impossible without rebuilding tiles.

---

## Custom Costing Model

### Concept

Valhalla uses "costing models" to determine the cost of traversing each edge (road segment) in the graph. We extend this with a `camera_penalty` costing that adds costs based on ALPR proximity.

### Implementation Approaches

#### Approach A: Lua Scripting (Recommended for MVP)

Valhalla supports Lua scripts for custom edge costing. This is the fastest path.

```lua
-- camera_penalty.lua
-- Attached to Valhalla's dynamic costing

local camera_penalty = {}

function camera_penalty.setup(config)
    -- Load camera data into memory
    -- Could read from PostGIS dump or GeoJSON
    cameras = load_camera_data("cameras.geojson")
    
    -- Config
    base_penalty = 1000       -- Cost added per camera within 100m
    fov_penalty = 5000        -- Extra cost if in field of view
    fov_angle = 180           -- Conservative FOV assumption (degrees)
    max_distance = 200        -- Max distance to apply penalty (meters)
end

function camera_penalty.cost(edge, previous_edge)
    local base_cost = edge.length / edge.speed
    
    local penalty = 0
    local edge_lat = edge.lat
    local edge_lon = edge.lon
    local edge_heading = edge.heading
    
    -- Check each camera
    for _, cam in ipairs(cameras) do
        local dist = haversine(edge_lat, edge_lon, cam.lat, cam.lon)
        
        if dist <= max_distance then
            -- Base proximity penalty
            penalty = penalty + base_penalty * (1 - dist / max_distance)
            
            -- FOV penalty (if camera direction is known)
            if cam.direction ~= nil then
                if in_fov(edge_heading, cam.direction, fov_angle) then
                    penalty = penalty + fov_penalty
                end
            end
        end
    end
    
    return base_cost + penalty
end

function camera_penalty.transition(edge1, edge2)
    -- No special transition cost
    return 0
end

function in_fov(heading, cam_direction, fov_angle)
    local diff = math.abs(heading - cam_direction) % 360
    if diff > 180 then
        diff = 360 - diff
    end
    return diff <= fov_angle / 2
end

function haversine(lat1, lon1, lat2, lon2)
    -- Standard haversine distance in meters
    local R = 6371000
    local phi1 = math.rad(lat1)
    local phi2 = math.rad(lat2)
    local dphi = math.rad(lat2 - lat1)
    local dlambda = math.rad(lon2 - lon1)
    
    local a = math.sin(dphi/2)^2 + 
              math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)^2
    local c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c
end

return camera_penalty
```

**Pros:** Fast to implement, no C++ knowledge needed, hot-reloadable  
**Cons:** Performance overhead from Lua interpretation, limited data passing

---

#### Approach B: Native C++ Costing (Production)

For production performance, implement costing directly in Valhalla.

```cpp
// valhalla/sif/camerapenaltycosting.h

#include <valhalla/sif/dynamiccost.h>
#include <valhalla/baldr/graphconstants.h>
#include <spatialite.h>  // For PostGIS queries

namespace valhalla {
namespace sif {

class CameraPenaltyCosting : public DynamicCost {
public:
    CameraPenaltyCosting(const CostingOptions& options);
    
    // Main costing function
    Cost EdgeCost(const baldr::DirectedEdge* edge,
                  const baldr::GraphTile* tile,
                  const baldr::TimeInfo& time_info) const override;
    
private:
    // Camera data (loaded at startup, periodically refreshed)
    struct Camera {
        double lat;
        double lon;
        int direction;  // -1 if unknown
    };
    std::vector<Camera> cameras_;
    std::unique_ptr<SpatialIndex> spatial_index_;  // R-tree for fast lookup
    
    // Penalties
    double base_penalty_;
    double fov_penalty_;
    double max_distance_;
    
    bool InFieldOfView(double heading, int cam_direction) const;
};

}  // namespace sif
}  // namespace valhalla
```

**Pros:** Maximum performance, full control  
**Cons:** Requires C++ expertise, longer implementation, need to rebuild Valhalla

---

#### Approach C: Post-Processing (MVP Hack)

Simplest approach — no Valhalla modifications needed.

```python
# Get multiple routes from standard Valhalla
# Score each by camera exposure
# Return best option

async def get_camera_aware_route(start, end, preference="balanced"):
    # Get 3 route options from Valhalla (standard costing)
    routes = await valhalla.route(
        start, end,
        alternatives=3,
        costing="auto"
    )
    
    # Score each route by camera exposure
    scored_routes = []
    for route in routes:
        cameras = await get_cameras_along_route(route["geometry"])
        score = score_route(route, cameras)
        scored_routes.append({
            "route": route,
            "cameras": cameras,
            "exposure_score": score
        })
    
    # Return based on preference
    if preference == "avoid_cameras":
        return min(scored_routes, key=lambda r: r["exposure_score"])
    elif preference == "fastest":
        return min(scored_routes, key=lambda r: r["route"]["time"])
    else:  # balanced
        # Normalize and weight both factors
        return min(scored_routes, key=lambda r: 
            r["route"]["time"] / max_time + 
            r["exposure_score"] / max_exposure
        )

def score_route(route, cameras):
    """Score = sum of camera exposure along route."""
    total_exposure = 0
    for segment in route["legs"]:
        for cam in cameras:
            dist = distance_to_segment(cam, segment)
            if dist < 200:  # meters
                # Closer = higher exposure
                weight = 1 - (dist / 200)
                # Extra weight if in FOV
                if in_fov(segment["heading"], cam["direction"]):
                    weight *= 3
                total_exposure += weight
    return total_exposure
```

**Pros:** Zero engine modifications, works with existing Valhalla  
**Cons:** Limited — can only choose from generated alternatives, not truly optimize

---

## Penalty Tuning

### The Core Question

> "How many extra minutes is avoiding 1 camera worth?"

This is a UX/product decision. Suggest making it configurable:

```python
# User preference levels
AVOIDANCE_LEVELS = {
    "relaxed": {
        "base_penalty": 100,    # Mild preference to avoid
        "fov_penalty": 500,
        "max_detour_minutes": 5
    },
    "balanced": {
        "base_penalty": 1000,   # Moderate avoidance
        "fov_penalty": 5000,
        "max_detour_minutes": 10
    },
    "strict": {
        "base_penalty": 10000,  # Strong avoidance
        "fov_penalty": 50000,
        "max_detour_minutes": 20
    },
    "paranoid": {
        "base_penalty": 100000, # Avoid at almost any cost
        "fov_penalty": 500000,
        "max_detour_minutes": None  # No limit
    }
}
```

### How to Tune

1. Start with "balanced" defaults
2. Generate routes for real trips with different penalty values
3. Plot "detour time vs cameras avoided" curve
4. Find the knee of the curve — that's your sweet spot

---

## Route Response Format

```json
{
  "routes": [
    {
      "id": "route-a",
      "geometry": "encoded_polyline...",
      "distance_meters": 5420,
      "duration_seconds": 480,
      "camera_exposure": {
        "total_cameras": 3,
        "cameras_in_fov": 1,
        "exposure_score": 4.2,
        "cameras": [
          {
            "osm_id": 123456,
            "lat": 40.7128,
            "lon": -74.0060,
            "operator": "Flock Safety",
            "distance_meters": 45,
            "in_fov": true
          }
        ]
      }
    },
    {
      "id": "route-b",
      "geometry": "encoded_polyline...",
      "distance_meters": 7100,
      "duration_seconds": 720,
      "camera_exposure": {
        "total_cameras": 0,
        "cameras_in_fov": 0,
        "exposure_score": 0,
        "cameras": []
      }
    }
  ],
  "selected_route": "route-b",
  "avoidance_level": "balanced"
}
```

---

## Performance Optimization

### Pre-computation

```python
# Build spatial index at startup
def build_spatial_index(cameras):
    """R-tree index for fast spatial queries."""
    index = rtree.index.Index()
    for i, cam in enumerate(cameras):
        index.insert(i, (cam.lon, cam.lat, cam.lon, cam.lat))
    return index
```

### Caching

```
Route cache key: hash(start_lat, start_lon, end_lat, end_lon, avoidance_level)
Cache TTL: 1 hour
Cache backend: Redis
```

### Parallel Processing

```python
# Query cameras for route bounding box in parallel with Valhalla routing
async def get_route(start, end, avoidance):
    route_task = asyncio.create_task(valhalla.route(start, end))
    cameras_task = asyncio.create_task(get_cameras_bbox(start, end))
    
    route, cameras = await asyncio.gather(route_task, cameras_task)
    return apply_penalties(route, cameras, avoidance)
```
