export type SubscriptionStatus = 'active' | 'paused' | 'expired' | 'cancelled'

export type NotificationChannel = 'site' | 'email' | 'wechat' | 'app'

export interface Subscription {
  id: string
  userId: string
  strategyId: string
  strategyName: string
  status: SubscriptionStatus
  params: Record<string, unknown>
  channels: NotificationChannel[]
  cooldownSeconds: number
  signalCount7d?: number
  createdAt: string
  updatedAt: string
}

export interface CreateSubscriptionRequest {
  strategyId: string
  params: Record<string, unknown>
  channels: NotificationChannel[]
  cooldownSeconds: number
}

export interface UpdateSubscriptionRequest {
  params?: Record<string, unknown>
  channels?: NotificationChannel[]
  cooldownSeconds?: number
}

export interface SubscriptionsResponse {
  items: Subscription[]
  total: number
}
