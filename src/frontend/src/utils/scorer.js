import { pointToSegmentDistance, inFieldOfView, getHeading } from './geo.js'

export function scoreRoute(route, cameras) {
  const exposed = []
  const coords = route.geometry

  for (const cam of cameras) {
    let minDist = Infinity
    let isInFov = false

    for (let i = 0; i < coords.length - 1; i++) {
      const dist = pointToSegmentDistance(
        [cam.lat, cam.lon],
        coords[i],
        coords[i + 1]
      )
      if (dist < minDist) {
        minDist = dist
        if (dist < 200 && cam.direction !== null) {
          const heading = getHeading(coords[i], coords[i + 1])
          isInFov = inFieldOfView(heading, cam.direction)
        }
      }
    }

    if (minDist < 200) {
      const weight = (1 - minDist / 200) * (isInFov ? 3 : 1)
      exposed.push({
        osmId: cam.osmId,
        lat: cam.lat,
        lon: cam.lon,
        operator: cam.operator,
        distanceMeters: Math.round(minDist),
        inFov: isInFov,
        weight,
      })
    }
  }

  return {
    totalCameras: exposed.length,
    camerasInFov: exposed.filter((c) => c.inFov).length,
    exposureScore: exposed.reduce((sum, c) => sum + c.weight, 0),
    cameras: exposed.sort((a, b) => a.distanceMeters - b.distanceMeters),
  }
}

export function rankRoutes(routes, cameras) {
  return routes
    .map((r) => ({ ...r, cameraExposure: scoreRoute(r, cameras) }))
    .sort((a, b) => a.cameraExposure.exposureScore - b.cameraExposure.exposureScore)
    .map((r, i) => ({ ...r, isRecommended: i === 0 }))
}
