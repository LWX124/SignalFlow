'use client'

import { useEffect, useCallback } from 'react'
import { wsClient } from '@/services/websocket'
import { useNotificationStore } from '@/stores/notification-store'
import { useAuthStore } from '@/stores/auth-store'
import { Signal } from '@/types'

interface UseSignalWebSocketOptions {
  onNewSignal?: (signal: Signal) => void
}

export function useSignalWebSocket(options: UseSignalWebSocketOptions = {}) {
  const { onNewSignal } = options
  const addSignal = useNotificationStore((s) => s.addSignal)
  const setConnected = useNotificationStore((s) => s.setConnected)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  const handleNewSignal = useCallback(
    (data: unknown) => {
      const signal = data as Signal
      addSignal(signal)
      onNewSignal?.(signal)
    },
    [addSignal, onNewSignal]
  )

  useEffect(() => {
    if (!isAuthenticated) return

    wsClient.connect()
    setConnected(true)

    const unsubscribe = wsClient.subscribe('new_signal', handleNewSignal)

    return () => {
      unsubscribe()
      wsClient.disconnect()
      setConnected(false)
    }
  }, [isAuthenticated, handleNewSignal, setConnected])
}

export function useNotificationWebSocket() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const setConnected = useNotificationStore((s) => s.setConnected)

  useEffect(() => {
    if (!isAuthenticated) return

    wsClient.connect()
    setConnected(true)

    const unsubscribeSignal = wsClient.subscribe('new_signal', (data) => {
      const signal = data as Signal
      // Show browser notification
      if (typeof window !== 'undefined' && 'Notification' in window && Notification.permission === 'granted') {
        new Notification('新信号', {
          body: `${signal.symbol} - ${signal.side}`,
          icon: '/favicon.ico',
        })
      }
    })

    const unsubscribeNotification = wsClient.subscribe('notification', (_data) => {
      // Handle other notification types
    })

    return () => {
      unsubscribeSignal()
      unsubscribeNotification()
      wsClient.disconnect()
      setConnected(false)
    }
  }, [isAuthenticated, setConnected])
}
