import { describe, it, expect } from 'vitest'
import { pointToSegmentDistance, haversine } from './geo'

describe('haversine', () => {
  it('should return 0 for identical points', () => {
    expect(haversine(0, 0, 0, 0)).toBe(0)
    expect(haversine(40.7128, -74.006, 40.7128, -74.006)).toBe(0)
  })

  it('should calculate distance correctly between two points (New York and London)', () => {
    // New York: 40.7128° N, 74.0060° W
    // London: 51.5074° N, 0.1278° W
    const dist = haversine(40.7128, -74.006, 51.5074, -0.1278)
    // The great-circle distance is roughly 5570 km.
    expect(dist).toBeGreaterThan(5500000)
    expect(dist).toBeLessThan(5600000)
  })

  it('should calculate distance correctly across the equator', () => {
    // 0,0 to 0,90 should be exactly a quarter of the Earth's circumference at the equator.
    // circumference = 2 * pi * R ~= 40030 km. Quarter = 10007 km.
    const dist = haversine(0, 0, 0, 90)
    expect(dist).toBeCloseTo((Math.PI * 6371000) / 2, -3) // Match to within a km
  })

  it('should be symmetric', () => {
    const p1 = [40.7128, -74.006]
    const p2 = [51.5074, -0.1278]
    expect(haversine(p1[0], p1[1], p2[0], p2[1])).toBe(haversine(p2[0], p2[1], p1[0], p1[1]))
  })

  it('should handle negative coordinates', () => {
    // Sydney: 33.8688° S, 151.2093° E
    // Buenos Aires: 34.6037° S, 58.3816° W
    const dist = haversine(-33.8688, 151.2093, -34.6037, -58.3816)
    // Distance should be roughly 11800 km
    expect(dist).toBeGreaterThan(11700000)
    expect(dist).toBeLessThan(11900000)
  })
})

describe('pointToSegmentDistance', () => {
  it('should return 0 when point is exactly on the start of the segment', () => {
    const point = [0, 0]
    const segStart = [0, 0]
    const segEnd = [1, 1]
    const dist = pointToSegmentDistance(point, segStart, segEnd)
    expect(dist).toBe(0)
  })

  it('should return 0 when point is exactly on the end of the segment', () => {
    const point = [1, 1]
    const segStart = [0, 0]
    const segEnd = [1, 1]
    const dist = pointToSegmentDistance(point, segStart, segEnd)
    expect(dist).toBe(0)
  })

  it('should return 0 when point is on the segment between start and end', () => {
    const point = [0.5, 0.5]
    const segStart = [0, 0]
    const segEnd = [1, 1]
    const dist = pointToSegmentDistance(point, segStart, segEnd)
    // The point is exactly halfway, projected t=0.5, distance to (0.5, 0.5) is 0
    expect(dist).toBe(0)
  })

  it('should return distance to start when point is beyond the start of the segment', () => {
    const point = [-1, -1]
    const segStart = [0, 0]
    const segEnd = [1, 1]
    const dist = pointToSegmentDistance(point, segStart, segEnd)
    const expectedDist = haversine(-1, -1, 0, 0)
    expect(dist).toBeCloseTo(expectedDist)
  })

  it('should return distance to end when point is beyond the end of the segment', () => {
    const point = [2, 2]
    const segStart = [0, 0]
    const segEnd = [1, 1]
    const dist = pointToSegmentDistance(point, segStart, segEnd)
    const expectedDist = haversine(2, 2, 1, 1)
    expect(dist).toBeCloseTo(expectedDist)
  })

  it('should return distance to closest point on segment when orthogonal', () => {
    // Segment from (0,0) to (0,2) along the Y axis
    const segStart = [0, 0]
    const segEnd = [0, 2]
    // Point at (1, 1). Closest projected point on the line in cartesian is (0, 1).
    const point = [1, 1]
    const dist = pointToSegmentDistance(point, segStart, segEnd)
    const expectedDist = haversine(1, 1, 0, 1)
    expect(dist).toBeCloseTo(expectedDist)
  })

  it('should handle zero-length segments (start equals end)', () => {
    const point = [1, 1]
    const segStart = [0, 0]
    const segEnd = [0, 0]
    const dist = pointToSegmentDistance(point, segStart, segEnd)
    const expectedDist = haversine(1, 1, 0, 0)
    expect(dist).toBeCloseTo(expectedDist)
  })
})
