export type StrategyType = 'arbitrage' | 'technical' | 'fundamental' | 'event' | 'composite'

export type RiskLevel = 'low' | 'medium' | 'high'

export interface StrategyMetrics {
  signalCount?: number
  hitRate?: number
  avgReturn?: number
  maxDrawdown?: number
}

export interface Strategy {
  id: string
  version: string
  name: string
  description?: string
  type: StrategyType
  markets: string[]
  riskLevel?: RiskLevel
  frequencyHint?: string
  paramsSchema: Record<string, unknown>
  defaultParams: Record<string, unknown>
  defaultCooldown: number
  metricsSummary: StrategyMetrics
  tierRequired: string
}

export interface StrategyFilters {
  type?: StrategyType
  market?: string
  riskLevel?: RiskLevel
  q?: string
  skip?: number
  limit?: number
}

export interface StrategiesResponse {
  items: Strategy[]
  total: number
}
