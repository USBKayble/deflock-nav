import { decodePolyline } from './geo.js'

const OSRM_URL = 'https://router.project-osrm.org'

export async function getRoutes(start, end, count = 3) {
  const coords = `${start.lon},${start.lat};${end.lon},${end.lat}`
  const url = `${OSRM_URL}/route/v1/driving/${coords}?overview=full&alternatives=${count - 1}&geometries=polyline`
  const res = await fetch(url)
  if (!res.ok) throw new Error(`OSRM error: ${res.status}`)
  const data = await res.json()
  if (data.code !== 'Ok') throw new Error(`OSRM: ${data.code}`)
  return data.routes.map((r, i) => ({
    id: `route-${i}`,
    geometry: decodePolyline(r.geometry),
    distanceMeters: r.distance,
    durationSeconds: r.duration,
  }))
}
