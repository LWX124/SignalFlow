'use client'

import { useState } from 'react'
import { useStrategies } from '@/hooks'
import { StrategyCard } from '@/components/business'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { STRATEGY_TYPES, RISK_LEVELS, MARKETS } from '@/lib/constants'
import { StrategyFilters } from '@/types'
import { useDebounce } from '@/hooks'
import { Search } from 'lucide-react'

export default function MarketplacePage() {
  const [filters, setFilters] = useState<StrategyFilters>({})
  const [searchQuery, setSearchQuery] = useState('')
  const debouncedQuery = useDebounce(searchQuery, 300)

  const { data, isLoading } = useStrategies({
    ...filters,
    q: debouncedQuery || undefined,
  })

  return (
    <div className="container py-6">
      <h1 className="text-2xl font-bold mb-6">策略广场</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜索策略..."
            className="pl-9"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <Select
          value={filters.market || 'all'}
          onValueChange={(value) =>
            setFilters({ ...filters, market: value === 'all' ? undefined : value })
          }
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="市场" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部市场</SelectItem>
            {MARKETS.map((m) => (
              <SelectItem key={m.value} value={m.value}>
                {m.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filters.type || 'all'}
          onValueChange={(value) =>
            setFilters({
              ...filters,
              type: value === 'all' ? undefined : (value as StrategyFilters['type']),
            })
          }
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="类型" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部类型</SelectItem>
            {STRATEGY_TYPES.map((t) => (
              <SelectItem key={t.value} value={t.value}>
                {t.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filters.riskLevel || 'all'}
          onValueChange={(value) =>
            setFilters({
              ...filters,
              riskLevel: value === 'all' ? undefined : (value as StrategyFilters['riskLevel']),
            })
          }
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="风险" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部风险</SelectItem>
            {RISK_LEVELS.map((r) => (
              <SelectItem key={r.value} value={r.value}>
                {r.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Strategy Grid */}
      {isLoading ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="space-y-4">
              <Skeleton className="h-48 w-full" />
            </div>
          ))}
        </div>
      ) : data?.items.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          暂无策略
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {data?.items.map((strategy) => (
            <StrategyCard key={strategy.id} strategy={strategy} />
          ))}
        </div>
      )}
    </div>
  )
}
