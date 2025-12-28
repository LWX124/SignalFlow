import axios, { AxiosError, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth-store'

// API error response type
export interface ApiErrorResponse {
  message?: string
  detail?: string
  code?: string
}

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Add request ID
    config.headers['X-Request-ID'] = crypto.randomUUID()

    return config
  },
  (error: AxiosError) => Promise.reject(error)
)

// Token refresh response type
interface TokenRefreshResponse {
  access_token: string
  refresh_token: string
}

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorResponse>) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

    // Token expired, try to refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = useAuthStore.getState().refreshToken
        if (!refreshToken) {
          throw new Error('No refresh token')
        }

        const { data } = await axios.post<TokenRefreshResponse>(
          `${process.env.NEXT_PUBLIC_API_URL || '/api/v1'}/auth/refresh`,
          { refresh_token: refreshToken }
        )

        useAuthStore.getState().setTokens(data.access_token, data.refresh_token)

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`
        }

        return apiClient(originalRequest)
      } catch (refreshError) {
        console.warn('Token refresh failed:', refreshError)
        useAuthStore.getState().logout()
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

// Helper to extract error message from API response
export function getApiErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const data = error.response?.data as ApiErrorResponse | undefined
    return data?.message || data?.detail || error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unexpected error occurred'
}
