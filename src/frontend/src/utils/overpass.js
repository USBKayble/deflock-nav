const OVERPASS_URL = 'https://overpass-api.de/api/interpreter'

export async function fetchCameras(bbox) {
  const [minLon, minLat, maxLon, maxLat] = bbox
  const query = `
    [out:json][timeout:30];
    (
      node["man_made"="surveillance"]["surveillance:type"="ALPR"](${minLat},${minLon},${maxLat},${maxLon});
      node["man_made"="surveillance"]["surveillance:type"="camera"]["operator"~"Flock",i](${minLat},${minLon},${maxLat},${maxLon});
    );
    out body;
  `
  const res = await fetch(OVERPASS_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `data=${encodeURIComponent(query)}`,
  })
  if (!res.ok) throw new Error(`Overpass API error: ${res.status}`)
  const data = await res.json()
  return data.elements
    .filter((el) => el.type === 'node' && el.tags)
    .map((el) => ({
      osmId: el.id,
      lat: el.lat,
      lon: el.lon,
      type: el.tags['surveillance:type'] || 'camera',
      direction: el.tags['camera:direction']
        ? parseInt(el.tags['camera:direction'], 10)
        : null,
      operator: el.tags.operator || 'Unknown',
    }))
}

export function getRouteBbox(start, end, padding = 0.02) {
  return [
    Math.min(start.lon, end.lon) - padding,
    Math.min(start.lat, end.lat) - padding,
    Math.max(start.lon, end.lon) + padding,
    Math.max(start.lat, end.lat) + padding,
  ]
}
