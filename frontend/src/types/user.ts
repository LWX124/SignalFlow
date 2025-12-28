export type UserRole = 'user' | 'admin'

export type UserTier = 'free' | 'pro' | 'enterprise'

export interface User {
  id: string
  email: string
  nickname: string
  role: UserRole
  tier: UserTier
  avatarUrl?: string
  createdAt: string
  updatedAt: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  nickname: string
}

export interface TokenResponse {
  accessToken: string
  refreshToken: string
}

export interface AuthResponse {
  user: User
  tokens: TokenResponse
}
