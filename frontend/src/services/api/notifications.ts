import { apiClient } from './client'
import { Notification, NotificationsResponse } from '@/types'

export const notificationsApi = {
  list: async (skip?: number, limit?: number): Promise<NotificationsResponse> => {
    const { data } = await apiClient.get<NotificationsResponse>('/notifications', {
      params: { skip, limit },
    })
    return data
  },

  markAsRead: async (id: string): Promise<Notification> => {
    const { data } = await apiClient.patch<Notification>(`/notifications/${id}/read`)
    return data
  },

  markAllAsRead: async (): Promise<void> => {
    await apiClient.post('/notifications/read-all')
  },

  getUnreadCount: async (): Promise<number> => {
    const { data } = await apiClient.get<{ count: number }>('/notifications/unread-count')
    return data.count
  },
}
