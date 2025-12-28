import { create } from 'zustand'
import { Signal } from '@/types'

interface NotificationState {
  realtimeSignals: Signal[]
  unreadCount: number
  isConnected: boolean

  addSignal: (signal: Signal) => void
  clearSignals: () => void
  decrementUnread: () => void
  resetUnread: () => void
  setConnected: (connected: boolean) => void
}

export const useNotificationStore = create<NotificationState>((set) => ({
  realtimeSignals: [],
  unreadCount: 0,
  isConnected: false,

  addSignal: (signal) =>
    set((state) => ({
      realtimeSignals: [signal, ...state.realtimeSignals].slice(0, 50),
      unreadCount: state.unreadCount + 1,
    })),

  clearSignals: () => set({ realtimeSignals: [] }),

  decrementUnread: () =>
    set((state) => ({ unreadCount: Math.max(0, state.unreadCount - 1) })),

  resetUnread: () => set({ unreadCount: 0 }),

  setConnected: (connected) => set({ isConnected: connected }),
}))
