export type NotificationType = 'signal' | 'system' | 'promotion'

export interface Notification {
  id: string
  userId: string
  type: NotificationType
  title: string
  content: string
  data?: Record<string, unknown>
  isRead: boolean
  createdAt: string
}

export interface NotificationsResponse {
  items: Notification[]
  total: number
  unreadCount: number
}
