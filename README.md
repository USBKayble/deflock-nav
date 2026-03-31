# DeFlock Nav

Privacy-first navigation that routes around surveillance cameras.

## What Is This?

A navigation app that uses [DeFlock](https://deflock.me)/OpenStreetMap data on ALPR (Automatic License Plate Reader) locations to calculate routes that minimize exposure to mass surveillance infrastructure.

**Status:** Working MVP. Deployed on Vercel.

## How It Works

1. **You enter start/end coordinates**
2. App fetches 3 route options from OSRM (public routing API)
3. App fetches camera locations from OpenStreetMap Overpass API
4. Each route is scored by camera exposure (proximity + field-of-view)
5. Routes are ranked — lowest camera exposure is recommended
6. Map shows cameras, route lines, and exposure stats

Everything runs client-side. No backend. No accounts. No tracking.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Vue 3 + Leaflet |
| Camera data | OpenStreetMap Overpass API |
| Routing | OSRM public API |
| Deployment | Vercel (static) |

## Local Development

```bash
cd src/frontend
npm install
npm run dev
```

## Deploy to Vercel

```bash
vercel
```

Or connect the GitHub repo to Vercel — it will auto-detect the config.

## Project Structure

```
deflock-nav/
├── src/frontend/           # Vue 3 SPA (this is the app)
│   ├── src/
│   │   ├── App.vue         # Main UI with map + route planning
│   │   ├── main.js         # Entry point
│   │   └── utils/
│   │       ├── overpass.js # Fetch cameras from OSM
│   │       ├── routing.js  # Get routes from OSRM
│   │       ├── scorer.js   # Score routes by camera exposure
│   │       └── geo.js      # Haversine, FOV, polyline decode
│   └── package.json
├── docs/                   # Architecture docs (for future expansion)
├── .github/workflows/      # CI + Jules automation
├── vercel.json             # Vercel deployment config
└── README.md
```

## Limitations (MVP)

- Requires lat/lon input (no geocoding yet)
- Camera data coverage depends on OpenStreetMap contributors
- OSRM public API has rate limits
- Only supports driving routes
- No mobile app (responsive web only)

## Future

- Add geocoding (Nominatim or Mapbox)
- Add avoidance levels (strict/relaxed)
- Cache camera data in localStorage
- PWA for offline use
- Custom Valhalla routing engine (see `docs/ROUTING_ENGINE.md`)

## Related Projects

- [DeFlock](https://github.com/FoggedLens/deflock) — The camera mapping project this builds on
- [OSRM](https://project-osrm.org/) — Open-source routing engine
- [OpenStreetMap](https://www.openstreetmap.org/) — The map data source

## License

TBD
