import { describe, it, expect } from 'vitest'
import { decodePolyline } from '../geo.js'

describe('decodePolyline', () => {
  it('should return an empty array for an empty string', () => {
    expect(decodePolyline('')).toEqual([])
  })

  it('should correctly decode a known polyline string', () => {
    // Example from Google Encoded Polyline Algorithm Format documentation
    // Points: (38.5, -120.2), (40.7, -120.95), (43.252, -126.453)
    const encoded = '_p~iF~ps|U_ulLnnqC_mqNvxq`@'
    const expected = [
      [38.5, -120.2],
      [40.7, -120.95],
      [43.252, -126.453]
    ]
    expect(decodePolyline(encoded)).toEqual(expected)
  })

  it('should decode a single coordinate correctly', () => {
    // Point: (38.5, -120.2)
    const encoded = '_p~iF~ps|U'
    const expected = [[38.5, -120.2]]
    expect(decodePolyline(encoded)).toEqual(expected)
  })
})
