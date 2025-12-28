'use client'

import { useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { authApi } from '@/services/api'
import { useAuthStore } from '@/stores/auth-store'
import { queryKeys } from '@/lib/query-client'
import { LoginRequest, RegisterRequest, User } from '@/types'

export function useAuth() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const { user, isAuthenticated, setUser, setTokens, logout: clearAuth } = useAuthStore()

  // Fetch current user
  const { isLoading: isLoadingUser } = useQuery({
    queryKey: queryKeys.auth.user(),
    queryFn: async () => {
      const user = await authApi.me()
      setUser(user)
      return user
    },
    enabled: isAuthenticated && !user,
    retry: false,
  })

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: (request: LoginRequest) => authApi.login(request),
    onSuccess: (data) => {
      setUser(data.user)
      setTokens(data.tokens.accessToken, data.tokens.refreshToken)
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.user() })
    },
  })

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: (request: RegisterRequest) => authApi.register(request),
    onSuccess: (data) => {
      setUser(data.user)
      setTokens(data.tokens.accessToken, data.tokens.refreshToken)
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.user() })
    },
  })

  // Logout
  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } catch {
      // Ignore errors
    } finally {
      clearAuth()
      queryClient.clear()
      router.push('/login')
    }
  }, [clearAuth, queryClient, router])

  return {
    user,
    isAuthenticated,
    isLoading: isLoadingUser,
    isLoadingUser,
    login: loginMutation.mutateAsync,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error,
    register: registerMutation.mutateAsync,
    isRegistering: registerMutation.isPending,
    registerError: registerMutation.error,
    logout,
  }
}

// Hook for updating user profile
export function useUpdateProfile() {
  const queryClient = useQueryClient()
  const { setUser } = useAuthStore()

  return useMutation({
    mutationFn: async (data: { nickname?: string; email?: string; avatar?: string }) => {
      const response = await authApi.updateProfile(data)
      return response
    },
    onSuccess: (data) => {
      setUser(data)
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.user() })
    },
  })
}

// Hook for changing password
export function useChangePassword() {
  return useMutation({
    mutationFn: async (data: { currentPassword: string; newPassword: string }) => {
      return authApi.changePassword(data)
    },
  })
}
