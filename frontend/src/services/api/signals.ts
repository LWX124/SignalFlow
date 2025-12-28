import { apiClient } from './client'
import { Signal, SignalFilters, SignalsResponse, SignalExplain } from '@/types'

export const signalsApi = {
  list: async (filters?: SignalFilters, cursor?: string): Promise<SignalsResponse> => {
    const { data } = await apiClient.get<SignalsResponse>('/signals', {
      params: { ...filters, cursor },
    })
    return data
  },

  getById: async (id: string): Promise<Signal> => {
    const { data } = await apiClient.get<Signal>(`/signals/${id}`)
    return data
  },

  getExplain: async (id: string): Promise<SignalExplain> => {
    const { data } = await apiClient.get<SignalExplain>(`/signals/${id}/explain`)
    return data
  },
}
