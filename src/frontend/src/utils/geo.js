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
