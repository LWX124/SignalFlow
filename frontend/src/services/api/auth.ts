import { apiClient } from './client'
import { User, LoginRequest, RegisterRequest, TokenResponse, AuthResponse } from '@/types'

export const authApi = {
  register: async (request: RegisterRequest): Promise<AuthResponse> => {
    const { data } = await apiClient.post<AuthResponse>('/auth/register', request)
    return data
  },

  login: async (request: LoginRequest): Promise<AuthResponse> => {
    const { data } = await apiClient.post<AuthResponse>('/auth/login', request)
    return data
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout')
  },

  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    const { data } = await apiClient.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    })
    return data
  },

  me: async (): Promise<User> => {
    const { data } = await apiClient.get<User>('/auth/me')
    return data
  },

  updateProfile: async (request: { nickname?: string; email?: string; avatar?: string }): Promise<User> => {
    const { data } = await apiClient.put<User>('/auth/profile', request)
    return data
  },

  changePassword: async (request: { currentPassword: string; newPassword: string }): Promise<void> => {
    await apiClient.put('/auth/password', {
      current_password: request.currentPassword,
      new_password: request.newPassword,
    })
  },
}
