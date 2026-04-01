import { describe, it, expect } from 'vitest'
import { inFieldOfView } from '../geo.js'

describe('inFieldOfView', () => {
  it('should be true when heading is exactly the camera direction', () => {
    expect(inFieldOfView(0, 0)).toBe(true)
    expect(inFieldOfView(90, 90)).toBe(true)
    expect(inFieldOfView(180, 180)).toBe(true)
    expect(inFieldOfView(270, 270)).toBe(true)
  })

  it('should be true when heading is within the default FOV (180 deg)', () => {
    // camDirection = 90. FOV = 180. Allowed difference <= 90. Valid [0, 180].
    expect(inFieldOfView(80, 90)).toBe(true)
    expect(inFieldOfView(100, 90)).toBe(true)
    expect(inFieldOfView(45, 90)).toBe(true)
    expect(inFieldOfView(135, 90)).toBe(true)
  })

  it('should be false when heading is outside the default FOV (180 deg)', () => {
    // camDirection = 90. Allowed [0, 180]. Outside: 181 to 359
    expect(inFieldOfView(181, 90)).toBe(false)
    expect(inFieldOfView(270, 90)).toBe(false)
    expect(inFieldOfView(350, 90)).toBe(false)
  })

  it('should test boundary cases exactly on the edge of the FOV', () => {
    // camDirection = 90. Edge = 0, 180
    expect(inFieldOfView(0, 90)).toBe(true)
    expect(inFieldOfView(180, 90)).toBe(true)

    // Custom FOV = 90. camDirection = 90. Edge = 45, 135
    expect(inFieldOfView(45, 90, 90)).toBe(true)
    expect(inFieldOfView(135, 90, 90)).toBe(true)
  })

  it('should handle wrap-around cases correctly (crossing 0/360 boundary)', () => {
    // camDirection = 10. FOV = 180. Allowed diff <= 90.
    // 10 - 90 = -80 (or 280), 10 + 90 = 100. Valid [280, 360] and [0, 100]
    expect(inFieldOfView(350, 10)).toBe(true)
    expect(inFieldOfView(330, 10)).toBe(true)
    expect(inFieldOfView(280, 10)).toBe(true) // exactly 90 deg difference
    expect(inFieldOfView(279, 10)).toBe(false)

    // camDirection = 350. FOV = 90. Allowed diff <= 45.
    // 350 - 45 = 305, 350 + 45 = 395 (or 35). Valid [305, 360] and [0, 35]
    expect(inFieldOfView(10, 350, 90)).toBe(true) // diff 20
    expect(inFieldOfView(35, 350, 90)).toBe(true) // diff 45
    expect(inFieldOfView(36, 350, 90)).toBe(false) // diff 46
    expect(inFieldOfView(340, 350, 90)).toBe(true)
  })

  it('should handle custom FOV angles', () => {
    // FOV = 60. Allowed diff <= 30.
    // camDirection = 180. Valid [150, 210]
    expect(inFieldOfView(160, 180, 60)).toBe(true)
    expect(inFieldOfView(200, 180, 60)).toBe(true)
    expect(inFieldOfView(149, 180, 60)).toBe(false)
    expect(inFieldOfView(211, 180, 60)).toBe(false)
  })

  it('should handle large angles over 360 or negative correctly', () => {
    // Math.abs(-10 - 10) % 360 = 20 % 360 = 20
    expect(inFieldOfView(-10, 10)).toBe(true) // diff 20
    expect(inFieldOfView(370, 10)).toBe(true) // 370 - 10 = 360 => 0
    expect(inFieldOfView(730, 10)).toBe(true) // 720 diff -> 0
  })
})
