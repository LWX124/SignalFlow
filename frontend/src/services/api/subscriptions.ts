import { apiClient } from './client'
import {
  Subscription,
  CreateSubscriptionRequest,
  UpdateSubscriptionRequest,
  SubscriptionsResponse,
} from '@/types'

export const subscriptionsApi = {
  list: async (): Promise<SubscriptionsResponse> => {
    const { data } = await apiClient.get<SubscriptionsResponse>('/subscriptions')
    return data
  },

  getById: async (id: string): Promise<Subscription> => {
    const { data } = await apiClient.get<Subscription>(`/subscriptions/${id}`)
    return data
  },

  create: async (request: CreateSubscriptionRequest): Promise<Subscription> => {
    const { data } = await apiClient.post<Subscription>('/subscriptions', {
      strategy_id: request.strategyId,
      params: request.params,
      channels: request.channels,
      cooldown_seconds: request.cooldownSeconds,
    })
    return data
  },

  update: async (id: string, request: UpdateSubscriptionRequest): Promise<Subscription> => {
    const { data } = await apiClient.patch<Subscription>(`/subscriptions/${id}`, {
      params: request.params,
      channels: request.channels,
      cooldown_seconds: request.cooldownSeconds,
    })
    return data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/subscriptions/${id}`)
  },

  enable: async (id: string): Promise<Subscription> => {
    const { data } = await apiClient.post<Subscription>(`/subscriptions/${id}:enable`)
    return data
  },

  disable: async (id: string): Promise<Subscription> => {
    const { data } = await apiClient.post<Subscription>(`/subscriptions/${id}:disable`)
    return data
  },
}
