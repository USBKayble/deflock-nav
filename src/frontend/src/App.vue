<template>
  <div class="app">
    <div class="sidebar">
      <h1>DeFlock Nav</h1>
      <p class="subtitle">Routes that avoid surveillance</p>

      <div class="form">
        <label>Start</label>
        <input
          v-model="startQuery"
          type="text"
          placeholder="Location (e.g. My Location, Times Square)"
        />

        <label>End</label>
        <input
          v-model="endQuery"
          type="text"
          placeholder="Location (e.g. Central Park)"
        />

        <button @click="findRoute" :disabled="loading">
          {{ loading ? 'Finding...' : 'Find Route' }}
        </button>
      </div>

      <div v-if="error" class="error">{{ error }}</div>

      <div v-if="routes.length" class="routes">
        <div
          v-for="route in routes"
          :key="route.id"
          class="route-card"
          :class="{
            selected: selectedRoute?.id === route.id,
            recommended: route.isRecommended,
          }"
          @click="selectRoute(route)"
        >
          <div class="route-header">
            <span v-if="route.isRecommended" class="badge">Recommended</span>
            <span class="time">{{ formatTime(route.durationSeconds) }}</span>
          </div>
          <div class="route-stats">
            <span>{{ (route.distanceMeters / 1000).toFixed(1) }} km</span>
            <span
              :class="{
                warn: route.cameraExposure.totalCameras > 0,
                safe: route.cameraExposure.totalCameras === 0,
              }"
            >
              {{ route.cameraExposure.totalCameras }} cameras
            </span>
          </div>
        </div>
      </div>

      <div v-if="selectedRoute" class="camera-list">
        <h3>Cameras on route</h3>
        <div
          v-for="cam in selectedRoute.cameraExposure.cameras"
          :key="cam.osmId"
          class="camera-item"
        >
          <span class="dist">{{ cam.distanceMeters }}m</span>
          <span class="op">{{ cam.operator }}</span>
          <span v-if="cam.inFov" class="fov">In FOV</span>
        </div>
        <p v-if="selectedRoute.cameraExposure.totalCameras === 0" class="safe-msg">
          No cameras detected on this route
        </p>
      </div>
    </div>

    <div id="map" ref="mapEl"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { fetchCameras, getRouteBbox } from './utils/overpass.js'
import { getRoutes } from './utils/routing.js'
import { geocode } from './utils/geocoding.js'

const mapEl = ref(null)
const startQuery = ref('')
const endQuery = ref('')
const startCoords = ref(null)

const loading = ref(false)
const error = ref(null)
const routes = ref([])
const selectedRoute = ref(null)

let map,
  routeLayers = [],
  cameraLayer = null

const ROUTE_COLORS = ['#3b82f6', '#8b5cf6', '#f59e0b']

onMounted(() => {
  map = L.map(mapEl.value).setView([40.73, -73.99], 13)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap',
  }).addTo(map)
  cameraLayer = L.layerGroup().addTo(map)

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        startCoords.value = {
          lat: position.coords.latitude,
          lon: position.coords.longitude
        }
        startQuery.value = 'My Location'
        map.setView([position.coords.latitude, position.coords.longitude], 13)
      },
      (err) => {
        console.warn('Geolocation error:', err)
      }
    )
  }
})

function clearRoutes() {
  routeLayers.forEach((l) => map.removeLayer(l))
  routeLayers = []
  cameraLayer.clearLayers()
}

function selectRoute(route) {
  selectedRoute.value = route
  routeLayers.forEach((l, i) => {
    l.setStyle({ weight: routes.value[i].id === route.id ? 6 : 3, opacity: routes.value[i].id === route.id ? 1 : 0.4 })
  })
}

function drawCameras(cameras) {
  const camIcon = L.divIcon({
    className: 'cam-marker',
    html: '<div style="background:#ef4444;width:10px;height:10px;border-radius:50%;border:2px solid white;"></div>',
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  })
  cameras.forEach((cam) => {
    const container = document.createElement('div')
    const b = document.createElement('b')
    b.textContent = cam.operator
    container.appendChild(b)
    container.appendChild(document.createElement('br'))
    container.appendChild(document.createTextNode(cam.type))

    L.marker([cam.lat, cam.lon], { icon: camIcon })
      .bindPopup(container)
      .addTo(cameraLayer)
  })
}

function drawRoutes() {
  clearRoutes()
  routes.value.forEach((route, i) => {
    const polyline = L.polyline(route.geometry, {
      color: ROUTE_COLORS[i] || '#666',
      weight: route.isRecommended ? 6 : 3,
      opacity: route.isRecommended ? 1 : 0.6,
    })
      .on('click', () => selectRoute(route))
      .addTo(map)
    routeLayers.push(polyline)
  })
  if (routes.value.length) {
    map.fitBounds(L.polyline(routes.value[0].geometry).getBounds(), { padding: [40, 40] })
  }
}

async function findRoute() {
  loading.value = true
  error.value = null
  routes.value = []
  selectedRoute.value = null
  clearRoutes()

  try {
    let start = null
    let end = null

    if (startQuery.value.trim().toLowerCase() === 'my location' && startCoords.value) {
      start = startCoords.value
    } else {
      start = await geocode(startQuery.value)
      if (!start) throw new Error(`Could not find location: ${startQuery.value}`)
    }

    end = await geocode(endQuery.value)
    if (!end) throw new Error(`Could not find location: ${endQuery.value}`)

    if (isNaN(start.lat) || isNaN(start.lon) || isNaN(end.lat) || isNaN(end.lon)) {
      throw new Error('Invalid coordinates')
    }

    const [scoredRoutes, cameras] = await Promise.all([
      getRoutes(start, end, 3),
      fetchCameras(getRouteBbox(start, end)),
    ])

    drawCameras(cameras)

    // The backend now performs the routing and scoring logic
    // We just map it to the frontend's expected properties
    routes.value = scoredRoutes.map(r => ({
      ...r,
      cameraExposure: {
        totalCameras: r.camera_exposure.total_cameras,
        camerasInFov: r.camera_exposure.cameras_in_fov,
        exposureScore: r.camera_exposure.exposure_score,
        cameras: r.camera_exposure.cameras.map(c => ({
          osmId: c.osmId,
          distanceMeters: c.distanceMeters,
          operator: c.operator,
          inFov: c.inFov,
        }))
      },
      isRecommended: r.is_recommended,
      distanceMeters: r.distance_meters,
      durationSeconds: r.duration_seconds
    }))

    selectedRoute.value = routes.value.find((r) => r.isRecommended) || routes.value[0]
    drawRoutes()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function formatTime(seconds) {
  const mins = Math.round(seconds / 60)
  return mins < 60 ? `${mins} min` : `${Math.floor(mins / 60)}h ${mins % 60}m`
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.app {
  display: flex;
  height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.sidebar {
  width: 340px;
  background: #0f172a;
  color: #e2e8f0;
  padding: 20px;
  overflow-y: auto;
}

h1 {
  font-size: 1.5rem;
  color: #f8fafc;
}

.subtitle {
  color: #94a3b8;
  font-size: 0.85rem;
  margin-bottom: 20px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}

.form label {
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
  margin-top: 8px;
}

.form input {
  padding: 8px;
  border: 1px solid #334155;
  border-radius: 6px;
  background: #1e293b;
  color: #f1f5f9;
  font-size: 0.9rem;
}

.form button {
  margin-top: 12px;
  padding: 10px;
  border: none;
  border-radius: 6px;
  background: #3b82f6;
  color: white;
  font-weight: 600;
  cursor: pointer;
}

.form button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  background: #7f1d1d;
  color: #fca5a5;
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 0.85rem;
}

.routes {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.route-card {
  background: #1e293b;
  border: 2px solid #334155;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
}

.route-card.selected {
  border-color: #3b82f6;
}

.route-card.recommended {
  border-color: #22c55e;
}

.route-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.badge {
  background: #22c55e;
  color: #052e16;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
}

.time {
  font-weight: 600;
  color: #f1f5f9;
}

.route-stats {
  display: flex;
  gap: 16px;
  margin-top: 6px;
  font-size: 0.85rem;
  color: #94a3b8;
}

.route-stats .warn {
  color: #f59e0b;
}

.route-stats .safe {
  color: #22c55e;
}

.camera-list h3 {
  font-size: 0.9rem;
  margin-bottom: 8px;
  color: #cbd5e1;
}

.camera-item {
  display: flex;
  gap: 10px;
  padding: 6px 0;
  border-bottom: 1px solid #1e293b;
  font-size: 0.8rem;
}

.camera-item .dist {
  color: #f59e0b;
  min-width: 45px;
}

.camera-item .op {
  color: #94a3b8;
  flex: 1;
}

.camera-item .fov {
  color: #ef4444;
  font-weight: 600;
}

.safe-msg {
  color: #22c55e;
  font-size: 0.85rem;
}

#map {
  flex: 1;
}

.cam-marker {
  background: none !important;
  border: none !important;
}
</style>
