export interface PaginatedResponse<T> {
  items: T[]
  total: number
  hasMore?: boolean
  nextCursor?: string
}

export interface ApiError {
  message: string
  code?: string
  details?: Record<string, unknown>
}

export interface ApiResponse<T> {
  data?: T
  error?: ApiError
}
