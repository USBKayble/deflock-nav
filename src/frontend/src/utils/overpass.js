// Assuming we are served from the same host, use relative path
const API_URL = '/api/v1'

export async function fetchCameras(bbox) {
  const [minLon, minLat, maxLon, maxLat] = bbox
  const bboxStr = `${minLon},${minLat},${maxLon},${maxLat}`

  const res = await fetch(`${API_URL}/cameras?bbox=${bboxStr}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)

  const data = await res.json()
  // The backend already returns the normalized format
  return data
}

export function getRouteBbox(start, end, padding = 0.02) {
  return [
    Math.min(start.lon, end.lon) - padding,
    Math.min(start.lat, end.lat) - padding,
    Math.max(start.lon, end.lon) + padding,
    Math.max(start.lat, end.lat) + padding,
  ]
}
