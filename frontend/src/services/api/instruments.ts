import { apiClient } from './client'
import {
  Instrument,
  InstrumentFilters,
  InstrumentsResponse,
  InstrumentSnapshot,
  InstrumentBar,
  SignalsResponse,
} from '@/types'

export const instrumentsApi = {
  list: async (filters?: InstrumentFilters): Promise<InstrumentsResponse> => {
    const { data } = await apiClient.get<InstrumentsResponse>('/instruments', {
      params: filters,
    })
    return data
  },

  getBySymbol: async (symbol: string, market?: string): Promise<Instrument> => {
    const { data } = await apiClient.get<Instrument>(`/instruments/${symbol}`, {
      params: { market },
    })
    return data
  },

  getSignals: async (
    symbol: string,
    skip?: number,
    limit?: number
  ): Promise<SignalsResponse> => {
    const { data } = await apiClient.get<SignalsResponse>(`/instruments/${symbol}/signals`, {
      params: { skip, limit },
    })
    return data
  },

  getSnapshot: async (symbol: string): Promise<InstrumentSnapshot> => {
    const { data } = await apiClient.get<InstrumentSnapshot>(`/instruments/${symbol}/snapshot`)
    return data
  },

  getBars: async (
    symbol: string,
    timeframe: string,
    limit?: number
  ): Promise<InstrumentBar[]> => {
    const { data } = await apiClient.get<InstrumentBar[]>(`/instruments/${symbol}/bars`, {
      params: { timeframe, limit },
    })
    return data
  },
}
