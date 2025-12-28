'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useInstruments, useDebounce } from '@/hooks'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { MARKETS } from '@/lib/constants'
import { InstrumentFilters } from '@/types'
import { Search } from 'lucide-react'

const INSTRUMENT_TYPES = [
  { value: 'stock', label: '股票' },
  { value: 'etf', label: 'ETF' },
  { value: 'qdii', label: 'QDII' },
  { value: 'lof', label: 'LOF' },
]

export default function InstrumentsPage() {
  const [filters, setFilters] = useState<InstrumentFilters>({})
  const [searchQuery, setSearchQuery] = useState('')
  const debouncedQuery = useDebounce(searchQuery, 300)

  const { data, isLoading } = useInstruments({
    ...filters,
    q: debouncedQuery || undefined,
  })

  return (
    <div className="container py-6">
      <h1 className="text-2xl font-bold mb-6">标的</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜索标的..."
            className="pl-9"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <Select
          value={filters.market || 'all'}
          onValueChange={(value) =>
            setFilters({
              ...filters,
              market: value === 'all' ? undefined : (value as InstrumentFilters['market']),
            })
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
              type: value === 'all' ? undefined : (value as InstrumentFilters['type']),
            })
          }
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="类型" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部类型</SelectItem>
            {INSTRUMENT_TYPES.map((t) => (
              <SelectItem key={t.value} value={t.value}>
                {t.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Instruments List */}
      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 10 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : data?.items.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          暂无标的
        </div>
      ) : (
        <div className="space-y-2">
          {data?.items.map((instrument) => (
            <Link key={instrument.id} href={`/instruments/${instrument.symbol}`}>
              <Card className="hover:bg-accent transition-colors cursor-pointer">
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div>
                      <p className="font-semibold">{instrument.symbol}</p>
                      <p className="text-sm text-muted-foreground">{instrument.name}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">{instrument.market}</Badge>
                    <Badge variant="outline">{instrument.type}</Badge>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
