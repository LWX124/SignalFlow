import { useAuthStore } from '@/stores/auth-store'

// WebSocket message types for type safety
export interface WebSocketMessage<T = unknown> {
  type: string
  data: T
}

export interface SignalMessage {
  id: string
  strategyId: string
  symbol: string
  direction: 'long' | 'short'
  action: 'open' | 'close'
  price: number
  timestamp: string
}

export interface NotificationMessage {
  id: string
  type: 'signal' | 'system' | 'promotion'
  title: string
  content: string
  createdAt: string
}

type MessageHandler<T = unknown> = (data: T) => void

class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private handlers: Map<string, Set<MessageHandler>> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private pingInterval: NodeJS.Timeout | null = null
  private isAuthenticated = false

  constructor(url: string) {
    this.url = url
  }

  connect() {
    if (typeof window === 'undefined') return

    const token = useAuthStore.getState().token
    if (!token) return

    try {
      // Connect without token in URL for security
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        console.log('WebSocket connected, authenticating...')
        // Send token as first message after connection (more secure than URL param)
        this.sendAuth(token)
      }

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage

          // Handle authentication response
          if (message.type === 'auth_success') {
            console.log('WebSocket authenticated')
            this.isAuthenticated = true
            this.reconnectAttempts = 0
            this.startPing()
            return
          }

          if (message.type === 'auth_error') {
            console.error('WebSocket authentication failed')
            this.disconnect()
            return
          }

          this.handleMessage(message)
        } catch (e) {
          console.error('Failed to parse WebSocket message', e)
        }
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.stopPing()
        this.attemptReconnect()
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error', error)
      }
    } catch (e) {
      console.error('Failed to create WebSocket', e)
    }
  }

  disconnect() {
    this.stopPing()
    this.isAuthenticated = false
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  private sendAuth(token: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'auth', token }))
    }
  }

  subscribe(type: string, handler: MessageHandler) {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set())
    }
    this.handlers.get(type)!.add(handler)

    return () => {
      this.handlers.get(type)?.delete(handler)
    }
  }

  send(message: unknown) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN && this.isAuthenticated
  }

  private handleMessage(message: WebSocketMessage) {
    const handlers = this.handlers.get(message.type)
    if (handlers) {
      handlers.forEach((handler) => handler(message.data))
    }
  }

  private startPing() {
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send('ping')
      }
    }, 30000)
  }

  private stopPing() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnect attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)

    setTimeout(() => {
      console.log(`Reconnecting... attempt ${this.reconnectAttempts}`)
      this.connect()
    }, delay)
  }
}

export const wsClient = new WebSocketClient(
  process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1/ws/signals'
)
