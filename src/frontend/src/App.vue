<template>
  <div class="app">
    <div class="controls">
      <input v-model="start.lat" placeholder="Start lat" />
      <input v-model="start.lon" placeholder="Start lon" />
      <input v-model="end.lat" placeholder="End lat" />
      <input v-model="end.lon" placeholder="End lon" />
      <select v-model="avoidanceLevel">
        <option value="relaxed">Relaxed</option>
        <option value="balanced">Balanced</option>
        <option value="strict">Strict</option>
        <option value="paranoid">Paranoid</option>
      </select>
      <button @click="calculateRoute" :disabled="loading">
        {{ loading ? 'Calculating...' : 'Find Route' }}
      </button>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="routes.length" class="route-list">
      <div
        v-for="route in routes"
        :key="route.id"
        :class="{ recommended: route.is_recommended }"
        @click="selectedRoute = route"
      >
        <span v-if="route.is_recommended">⭐ </span>
        {{ formatTime(route.duration_seconds) }}
        | {{ route.camera_exposure.total_cameras }} cameras
        | Score: {{ route.camera_exposure.exposure_score.toFixed(1) }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const start = ref({ lat: 40.7128, lon: -74.006 })
const end = ref({ lat: 40.7484, lon: -73.9857 })
const avoidanceLevel = ref('balanced')
const routes = ref([])
const selectedRoute = ref(null)
const loading = ref(false)
const error = ref(null)

function formatTime(seconds) {
  const mins = Math.round(seconds / 60)
  return mins < 60 ? `${mins} min` : `${Math.floor(mins / 60)}h ${mins % 60}m`
}

async function calculateRoute() {
  loading.value = true
  error.value = null
  try {
    const res = await fetch('http://localhost:8000/api/v1/route', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        start: start.value,
        end: end.value,
        avoidance_level: avoidanceLevel.value,
      }),
    })
    if (!res.ok) throw new Error(`API error: ${res.status}`)
    const data = await res.json()
    routes.value = data.routes
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>
