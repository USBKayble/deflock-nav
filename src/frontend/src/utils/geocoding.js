export async function geocode(query) {
  if (!query) return null

  const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1`

  try {
    const res = await fetch(url, {
      headers: {
        'Accept-Language': 'en',
        'User-Agent': 'DeFlockNav/1.0'
      }
    })

    if (!res.ok) throw new Error(`Geocoding error: ${res.status}`)

    const data = await res.json()
    if (data && data.length > 0) {
      return {
        lat: parseFloat(data[0].lat),
        lon: parseFloat(data[0].lon),
        displayName: data[0].display_name
      }
    }
    return null
  } catch (error) {
    console.error('Geocoding failed:', error)
    throw error
  }
}
