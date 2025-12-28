import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { User } from '@/types'

// Cookie utilities for syncing with middleware
const setCookie = (name: string, value: string, days = 7) => {
  if (typeof document === 'undefined') return
  const expires = new Date(Date.now() + days * 864e5).toUTCString()
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`
}

const deleteCookie = (name: string) => {
  if (typeof document === 'undefined') return
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`
}

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean

  setUser: (user: User | null) => void
  setTokens: (accessToken: string | null, refreshToken?: string | null) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,

      setUser: (user) =>
        set({
          user,
          isAuthenticated: !!user,
        }),

      setTokens: (accessToken, refreshToken) => {
        // Sync token to cookie for middleware access
        if (accessToken) {
          setCookie('access_token', accessToken)
        } else {
          deleteCookie('access_token')
        }

        set((state) => ({
          token: accessToken,
          refreshToken: refreshToken ?? state.refreshToken,
          // Derive isAuthenticated from token presence
          isAuthenticated: !!accessToken,
        }))
      },

      logout: () => {
        // Clear cookies
        deleteCookie('access_token')
        deleteCookie('refresh_token')

        set({
          user: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false,
        })
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => sessionStorage), // Use sessionStorage for better security
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
      }),
      onRehydrateStorage: () => (state) => {
        // Sync token to cookie on rehydration
        if (state?.token) {
          setCookie('access_token', state.token)
        }
      },
    }
  )
)
