# DeFlock Nav

Privacy-first navigation that routes around surveillance cameras.

## What Is This?

A navigation app that uses [DeFlock](https://deflock.me)/OpenStreetMap data on ALPR (Automatic License Plate Reader) locations to calculate routes that minimize exposure to mass surveillance infrastructure.

**Status:** Working Beta. Deployed as a self-hosted 'all-in-one' Docker Compose setup on TrueNAS Scale.

## How It Works

1. **You enter start/end coordinates**
2. App fetches 3 route options via the FastAPI backend (which may use Valhalla or proxy OSRM)
3. App fetches camera locations (proxied through backend from Overpass API or local PostGIS)
4. Each route is scored by camera exposure (proximity + field-of-view)
5. Routes are ranked — lowest camera exposure is recommended
6. Map shows cameras, route lines, and exposure stats

External API integrations (such as Overpass and OSRM) are proxied through the FastAPI backend to avoid frontend rate limits and allow persistent storage of data directly into the local PostGIS database.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Vue 3 + Leaflet (built with Vite) |
| Backend | FastAPI + Pydantic |
| Database | PostGIS (SQLAlchemy, GeoAlchemy2) |
| Caching | Redis |
| Routing | Valhalla / OSRM |
| Deployment | Docker Compose (Self-hosted on TrueNAS Scale) |

## Local Development

The project uses Docker Compose for orchestration, managing services for PostGIS, Redis, Valhalla, and the FastAPI backend.
The backend serves the built Vue frontend on port 8000.

```bash
# Setup environment variables
cp .env.example .env

# Run all services
docker compose up -d
```

A root `package.json` proxies scripts (`install`, `build`, `lint`, `test`) to the `src/frontend` directory. Node.js 20 is enforced.
To develop the frontend directly:
```bash
nvm use
npm install
npm run dev
```

## Project Structure

```
deflock-nav/
├── src/
│   ├── api/                # FastAPI backend
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── database.py
│   │   ├── config.py
│   │   └── routes/
│   └── frontend/           # Vue 3 SPA
│       ├── src/
│       │   ├── App.vue     # Main UI with map + route planning
│       │   ├── main.js     # Entry point
│       │   └── utils/
│       └── package.json
├── docker/                 # Dockerfiles
├── docs/                   # Architecture docs
├── .github/workflows/      # CI + Jules automation
├── docker-compose.yml      # Orchestration
├── package.json            # Root proxy scripts
└── README.md
```

## Limitations (Beta)

- Requires lat/lon input (no geocoding yet)
- Camera data coverage depends on OpenStreetMap contributors
- Only supports driving routes
- No mobile app (responsive web only)

## TODO List

- [ ] Write automated tests (none currently exist)
- [ ] Add geocoding (Nominatim or Mapbox)
- [ ] Add avoidance levels (strict/relaxed)
- [ ] Implement caching of camera data in localStorage / Redis
- [ ] PWA for offline use
- [ ] Fully integrate custom Valhalla routing engine (see `docs/ROUTING_ENGINE.md`)

## Related Projects

- [DeFlock](https://github.com/FoggedLens/deflock) — The camera mapping project this builds on
- [OSRM](https://project-osrm.org/) — Open-source routing engine
- [Valhalla](https://github.com/valhalla/valhalla) — Open-source routing engine
- [OpenStreetMap](https://www.openstreetmap.org/) — The map data source

## License

TBD
