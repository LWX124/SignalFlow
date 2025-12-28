'use client'

import { useQuery } from '@tanstack/react-query'
import { instrumentsApi } from '@/services/api'
import { queryKeys } from '@/lib/query-client'
import { InstrumentFilters } from '@/types'

export function useInstruments(filters?: InstrumentFilters) {
  return useQuery({
    queryKey: queryKeys.instruments.list(filters),
    queryFn: () => instrumentsApi.list(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useInstrument(symbol: string, market?: string) {
  return useQuery({
    queryKey: queryKeys.instruments.detail(symbol),
    queryFn: () => instrumentsApi.getBySymbol(symbol, market),
    enabled: !!symbol,
  })
}

export function useInstrumentSnapshot(symbol: string) {
  return useQuery({
    queryKey: queryKeys.instruments.snapshot(symbol),
    queryFn: () => instrumentsApi.getSnapshot(symbol),
    enabled: !!symbol,
    refetchInterval: 10000, // Refresh every 10 seconds
  })
}

export function useInstrumentBars(symbol: string, timeframe = '1d', limit = 100) {
  return useQuery({
    queryKey: queryKeys.instruments.bars(symbol, timeframe),
    queryFn: () => instrumentsApi.getBars(symbol, timeframe, limit),
    enabled: !!symbol,
    staleTime: 60 * 1000, // 1 minute
  })
}

export function useInstrumentSignals(symbol: string, skip?: number, limit?: number) {
  return useQuery({
    queryKey: queryKeys.instruments.signals(symbol),
    queryFn: () => instrumentsApi.getSignals(symbol, skip, limit),
    enabled: !!symbol,
  })
}
