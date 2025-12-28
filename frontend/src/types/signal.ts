export type SignalSide = 'buy' | 'sell' | 'opportunity' | 'observe' | 'warning'

export interface Signal {
  id: string
  strategyId: string
  strategyName?: string
  symbol: string
  instrumentName?: string
  market: string
  side: SignalSide
  confidence: number
  reasonPoints: string[]
  riskTags: string[]
  evidence?: Record<string, unknown>
  aiExplain?: string
  timestamp: string
  createdAt: string
}

export interface SignalFilters {
  strategyId?: string
  symbol?: string
  market?: string
  side?: SignalSide
  startDate?: string
  endDate?: string
}

export interface SignalsResponse {
  items: Signal[]
  nextCursor?: string
  hasMore: boolean
}

export interface SignalExplain {
  content: string
}
