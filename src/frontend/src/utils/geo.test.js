import { describe, it, expect } from 'vitest'
import { pointToSegmentDistance, haversine } from './geo'

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
