'use client'

import { useQuery } from '@tanstack/react-query'
import { strategiesApi } from '@/services/api'
import { queryKeys } from '@/lib/query-client'
import { StrategyFilters } from '@/types'

export function useStrategies(filters?: StrategyFilters) {
  return useQuery({
    queryKey: queryKeys.strategies.list(filters),
    queryFn: () => strategiesApi.list(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useStrategy(id: string) {
  return useQuery({
    queryKey: queryKeys.strategies.detail(id),
    queryFn: () => strategiesApi.getById(id),
    enabled: !!id,
  })
}

export function useStrategySignals(id: string, skip?: number, limit?: number) {
  return useQuery({
    queryKey: queryKeys.strategies.signals(id),
    queryFn: () => strategiesApi.getSignals(id, skip, limit),
    enabled: !!id,
  })
}

export function useStrategyPerformance(id: string, days = 30) {
  return useQuery({
    queryKey: queryKeys.strategies.performance(id, days),
    queryFn: () => strategiesApi.getPerformance(id, days),
    enabled: !!id,
  })
}
