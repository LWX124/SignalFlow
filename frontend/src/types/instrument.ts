export type InstrumentType = 'stock' | 'etf' | 'qdii' | 'lof' | 'index'

export type Market = 'SH' | 'SZ' | 'HK' | 'US'

export interface Instrument {
  id: string
  symbol: string
  name: string
  market: Market
  type: InstrumentType
  exchange?: string
  currency: string
  isActive: boolean
}

export interface InstrumentSnapshot {
  symbol: string
  price: number
  change: number
  changePercent: number
  volume: number
  amount: number
  high: number
  low: number
  open: number
  prevClose: number
  timestamp: string
}

export interface InstrumentBar {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume?: number
}

export interface InstrumentFilters {
  market?: Market
  type?: InstrumentType
  q?: string
  skip?: number
  limit?: number
}

export interface InstrumentsResponse {
  items: Instrument[]
  total: number
}
