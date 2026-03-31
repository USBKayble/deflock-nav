import { decodePolyline } from './geo.js'

// Assuming we are served from the same host, use relative path
const API_URL = '/api/v1'

export async function getRoutes(start, end, count = 3) {
  const res = await fetch(`${API_URL}/route`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      start: { lat: start.lat, lon: start.lon },
      end: { lat: end.lat, lon: end.lon },
      alternatives: count,
      avoidance_level: 'balanced',
      mode: 'auto'
    })
  })

  if (!res.ok) throw new Error(`API error: ${res.status}`)
  const data = await res.json()

  // The backend now returns the full route object including camera exposure and scores
  return data.map(r => ({
    ...r,
    geometry: decodePolyline(r.geometry), // Decode for Leaflet
  }))
}
