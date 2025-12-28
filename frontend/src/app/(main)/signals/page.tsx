'use client'

import { useState, useCallback } from 'react'
import { useSignals, useSignalWebSocket } from '@/hooks'
import { SignalCard } from '@/components/business'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { SignalFilters, Signal } from '@/types'
import { useNotificationStore } from '@/stores'
import { Badge } from '@/components/ui/badge'

export default function SignalsPage() {
  const [filters] = useState<SignalFilters>({})
  const realtimeSignals = useNotificationStore((s) => s.realtimeSignals)
  const isConnected = useNotificationStore((s) => s.isConnected)

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = useSignals(filters)

  const handleNewSignal = useCallback((_signal: Signal) => {
    // Signal is already added to store by the hook
  }, [])

  // Setup WebSocket
  useSignalWebSocket({ onNewSignal: handleNewSignal })

  const historicalSignals = data?.pages.flatMap((page) => page.items) ?? []

  // Merge realtime and historical, dedupe by id
  const seenIds = new Set<string>()
  const allSignals = [...realtimeSignals, ...historicalSignals].filter((s) => {
    if (seenIds.has(s.id)) return false
    seenIds.add(s.id)
    return true
  })

  return (
    <div className="container py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">信号流</h1>
        <div className="flex items-center gap-2">
          <Badge variant={isConnected ? 'default' : 'secondary'}>
            {isConnected ? '实时更新中' : '未连接'}
          </Badge>
        </div>
      </div>

      {/* Signal List */}
      <div className="space-y-4">
        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-40 w-full" />
          ))
        ) : allSignals.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            暂无信号
          </div>
        ) : (
          <>
            {allSignals.map((signal) => (
              <SignalCard key={signal.id} signal={signal} />
            ))}

            {hasNextPage && (
              <div className="flex justify-center pt-4">
                <Button
                  variant="outline"
                  onClick={() => fetchNextPage()}
                  disabled={isFetchingNextPage}
                >
                  {isFetchingNextPage ? '加载中...' : '加载更多'}
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
