export function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371000
  const phi1 = (lat1 * Math.PI) / 180
  const phi2 = (lat2 * Math.PI) / 180
  const dphi = ((lat2 - lat1) * Math.PI) / 180
  const dlambda = ((lon2 - lon1) * Math.PI) / 180
  const a =
    Math.sin(dphi / 2) ** 2 +
    Math.cos(phi1) * Math.cos(phi2) * Math.sin(dlambda / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

export function inFieldOfView(heading, camDirection, fovAngle = 180) {
  let diff = Math.abs(heading - camDirection) % 360
  if (diff > 180) diff = 360 - diff
  return diff <= fovAngle / 2
}

export function decodePolyline(encoded) {
  const coords = []
  let lat = 0,
    lon = 0,
    index = 0
  while (index < encoded.length) {
    let b,
      shift = 0,
      result = 0
    do {
      b = encoded.charCodeAt(index++) - 63
      result |= (b & 0x1f) << shift
      shift += 5
    } while (b >= 0x20)
    const dlat = result & 1 ? ~(result >> 1) : result >> 1
    lat += dlat
    shift = 0
    result = 0
    do {
      b = encoded.charCodeAt(index++) - 63
      result |= (b & 0x1f) << shift
      shift += 5
    } while (b >= 0x20)
    const dlon = result & 1 ? ~(result >> 1) : result >> 1
    lon += dlon
    coords.push([lat / 1e5, lon / 1e5])
  }
  return coords
}

export function getHeading(p1, p2) {
  const dlon = ((p2[1] - p1[1]) * Math.PI) / 180
  const lat1 = (p1[0] * Math.PI) / 180
  const lat2 = (p2[0] * Math.PI) / 180
  const y = Math.sin(dlon) * Math.cos(lat2)
  const x =
    Math.cos(lat1) * Math.sin(lat2) -
    Math.sin(lat1) * Math.cos(lat2) * Math.cos(dlon)
  return ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360
}

export function pointToSegmentDistance(point, segStart, segEnd) {
  const [px, py] = point
  const [ax, ay] = segStart
  const [bx, by] = segEnd
  const dx = bx - ax,
    dy = by - ay
  const len2 = dx * dx + dy * dy
  if (len2 === 0) return haversine(px, py, ax, ay)
  let t = ((px - ax) * dx + (py - ay) * dy) / len2
  t = Math.max(0, Math.min(1, t))
  return haversine(px, py, ax + t * dx, ay + t * dy)
}
