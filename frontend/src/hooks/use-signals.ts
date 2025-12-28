'use client'

import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { signalsApi } from '@/services/api'
import { queryKeys } from '@/lib/query-client'
import { SignalFilters } from '@/types'

export function useSignals(filters?: SignalFilters) {
  return useInfiniteQuery({
    queryKey: queryKeys.signals.list(filters),
    queryFn: ({ pageParam }) => signalsApi.list(filters, pageParam as string | undefined),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) =>
      lastPage.hasMore ? lastPage.nextCursor : undefined,
    staleTime: 30 * 1000, // 30 seconds
  })
}

export function useSignal(id: string) {
  return useQuery({
    queryKey: queryKeys.signals.detail(id),
    queryFn: () => signalsApi.getById(id),
    enabled: !!id,
  })
}

export function useSignalExplain(id: string) {
  return useQuery({
    queryKey: queryKeys.signals.explain(id),
    queryFn: () => signalsApi.getExplain(id),
    enabled: !!id,
    staleTime: Infinity, // AI explanation won't change
  })
}
