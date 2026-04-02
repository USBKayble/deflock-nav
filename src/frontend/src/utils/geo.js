export function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371000
  const phi1 = (lat1 * Math.PI) / 180
  const phi2 = (lat2 * Math.PI) / 180
  const dphi = ((lat2 - lat1) * Math.PI) / 180
  const dlambda = ((lon2 - lon1) * Math.PI) / 180

  const a =
    Math.sin(dphi / 2) * Math.sin(dphi / 2) +
    Math.cos(phi1) * Math.cos(phi2) * Math.sin(dlambda / 2) * Math.sin(dlambda / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))

  return R * c
}

export function pointToSegmentDistance(p, p1, p2) {
  let x = p1[0],
    y = p1[1],
    dx = p2[0] - x,
    dy = p2[1] - y,
    dot = dx * dx + dy * dy,
    t

  if (dot > 0) {
    t = ((p[0] - x) * dx + (p[1] - y) * dy) / dot

    if (t > 1) {
      x = p2[0]
      y = p2[1]
    } else if (t > 0) {
      x += dx * t
      y += dy * t
    }
  }

  return haversine(p[0], p[1], x, y)
}

export function inFieldOfView(heading, camDirection, fov = 180) {
  let diff = Math.abs(heading - camDirection) % 360
  if (diff > 180) {
    diff = 360 - diff
  }
  return diff <= fov / 2
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
