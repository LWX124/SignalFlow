import { apiClient } from './client'
import { Strategy, StrategyFilters, StrategiesResponse, SignalsResponse } from '@/types'

export const strategiesApi = {
  list: async (filters?: StrategyFilters): Promise<StrategiesResponse> => {
    const { data } = await apiClient.get<StrategiesResponse>('/strategies', {
      params: filters,
    })
    return data
  },

  getById: async (id: string): Promise<Strategy> => {
    const { data } = await apiClient.get<Strategy>(`/strategies/${id}`)
    return data
  },

  getSignals: async (
    id: string,
    skip?: number,
    limit?: number
  ): Promise<SignalsResponse> => {
    const { data } = await apiClient.get<SignalsResponse>(`/strategies/${id}/signals`, {
      params: { skip, limit },
    })
    return data
  },

  getPerformance: async (
    id: string,
    days?: number
  ): Promise<{
    strategyId: string
    periodDays: number
    signalCount: number
    metricsSummary: Record<string, unknown>
  }> => {
    const { data } = await apiClient.get(`/strategies/${id}/performance`, {
      params: { days },
    })
    return data
  },
}
