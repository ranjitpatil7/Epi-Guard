import { describe, it, expect } from 'vitest'
import { getRiskColor } from '../pages/map/MapView'

describe('MapView Business Logic', () => {
  it('correctly maps risk scores to colors', () => {
    const riskData = [
      { region_id: 1, estimated_risk_score: 39.6 },
      { region_id: 2, estimated_risk_score: 53.5 },
      { region_id: 3, estimated_risk_score: 63.4 },
      { region_id: 4, estimated_risk_score: 80.0 },
      { region_id: 5, estimated_risk_score: 95.0 },
    ]

    expect(getRiskColor(riskData, 1)).toBe('#10b981') // green
    expect(getRiskColor(riskData, 2)).toBe('#eab308') // yellow
    expect(getRiskColor(riskData, 3)).toBe('#f97316') // orange
    expect(getRiskColor(riskData, 4)).toBe('#ef4444') // red
    expect(getRiskColor(riskData, 5)).toBe('#ef4444') // red
  })

  it('prevents regression to riskData.data.find(...) by accepting arrays directly', () => {
    // If someone changes getCurrentRisk to return { data: [...] } without fixing this,
    // this test acts as a regression boundary.
    const invalidData = { data: [{ region_id: 1, estimated_risk_score: 50 }] } as any
    expect(getRiskColor(invalidData, 1)).toBe('#3b82f6') // fallback blue when array check fails
  })
})
