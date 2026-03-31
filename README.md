# DeFlock Nav

Privacy-first navigation that routes around surveillance cameras.

## What Is This?

A navigation app that uses [DeFlock](https://deflock.me)/OpenStreetMap data on ALPR (Automatic License Plate Reader) locations to calculate routes that minimize exposure to mass surveillance infrastructure.

**Status:** Architecture phase. Nothing built yet.

## Problem

Flock Safety and similar companies have deployed thousands of ALPRs across the US. These cameras:
- Log every license plate that passes
- Build searchable databases of vehicle movements
- Share data across jurisdictions with minimal oversight
- Are expanding rapidly through HOAs, businesses, and law enforcement

There's no tool today that helps you navigate while minimizing surveillance exposure.

## Solution

A routing engine that:
1. Queries ALPR locations from OpenStreetMap (via DeFlock's crowdsourced data)
2. Applies penalty weights to road segments near cameras
3. Calculates routes that balance travel time vs camera exposure
4. Shows you exactly how many cameras you'll pass on each route option

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend                              │
│  Vue 3 + Leaflet / Mapbox GL                           │
│  ├─ Interactive route planning                          │
│  ├─ Camera visualization (ALPRs, direction, FOV)       │
│  ├─ Route comparison (time vs exposure)                │
│  └─ "Avoid cameras" toggle                             │
├─────────────────────────────────────────────────────────┤
│                    API Layer                             │
│  FastAPI (Python)                                       │
│  ├─ /route - Calculate route with camera avoidance     │
│  ├─ /cameras - Get cameras in bounding box             │
│  └─ /stats - Camera density statistics                 │
├─────────────────────────────────────────────────────────┤
│                  Routing Engine                          │
│  Valhalla (self-hosted)                                │
│  ├─ Custom "camera_penalty" costing model              │
│  ├─ Edge weight modification based on ALPR proximity   │
│  └─ Field-of-view awareness                            │
├─────────────────────────────────────────────────────────┤
│                   Data Layer                             │
│  ├─ OpenStreetMap Overpass API (camera data)           │
│  ├─ Local OSM PBF extract (road network)               │
│  └─ Periodic sync + caching                            │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology | Why |
|-----------|------------|-----|
| Routing engine | Valhalla | Supports custom costing models |
| Map data | OpenStreetMap | DeFlock data lives here |
| Camera data | Overpass API | Query OSM surveillance tags |
| Backend API | FastAPI | Fast, async, Python ecosystem |
| Frontend | Vue 3 + Leaflet | DeFlock uses this; lightweight |
| Database | PostgreSQL + PostGIS | Spatial queries for camera proximity |
| Cache | Redis | Route caching, camera data TTL |
| Deployment | Docker Compose | Local dev + production parity |

## Project Structure

```
deflock-nav/
├── docs/                    # Architecture documentation
│   ├── ARCHITECTURE.md      # System design deep-dive
│   ├── DATA_LAYER.md        # OSM/Overpass integration
│   ├── ROUTING_ENGINE.md    # Penalty algorithm design
│   ├── API_DESIGN.md        # Endpoint specifications
│   └── QUICK_START.md       # Weekend MVP approach
├── src/
│   ├── api/                 # FastAPI backend
│   ├── routing/             # Valhalla config + custom costing
│   ├── frontend/            # Vue 3 web app
│   └── data/                # OSM sync, caching, PostGIS
├── scripts/                 # Data sync, setup utilities
├── docker/                  # Dockerfiles, compose configs
└── docker-compose.yml       # Local development stack
```

## Getting Started

See [`docs/QUICK_START.md`](docs/QUICK_START.md) for the fastest path to a working prototype.

## Related Projects

- [DeFlock](https://github.com/FoggedLens/deflock) — The camera mapping project this builds on
- [Valhalla](https://github.com/valhalla/valhalla) — Open-source routing engine
- [OpenStreetMap](https://www.openstreetmap.org/) — The map data source

## License

TBD (probably MIT or Apache 2.0 to match DeFlock)
