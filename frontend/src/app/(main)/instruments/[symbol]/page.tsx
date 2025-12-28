'use client'

import dynamic from 'next/dynamic'
import { useInstrument, useInstrumentBars, useInstrumentSignals } from '@/hooks'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import { SignalCard } from '@/components/business'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'

// Dynamic import for chart (no SSR)
const KLineChart = dynamic(
  () => import('@/components/charts/kline-chart').then((mod) => mod.KLineChart),
  {
    loading: () => <Skeleton className="h-[400px] w-full" />,
    ssr: false,
  }
)

interface PageProps {
  params: { symbol: string }
}

export default function InstrumentDetailPage({ params }: PageProps) {
  const { data: instrument, isLoading } = useInstrument(params.symbol)
  const { data: bars } = useInstrumentBars(params.symbol, '1d', 60)
  const { data: signals } = useInstrumentSignals(params.symbol, 0, 10)

  if (isLoading) {
    return (
      <div className="container py-6">
        <Skeleton className="h-8 w-48 mb-6" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!instrument) {
    return (
      <div className="container py-6">
        <p className="text-muted-foreground">标的不存在</p>
      </div>
    )
  }

  return (
    <div className="container py-6">
      {/* Back link */}
      <Link
        href="/instruments"
        className="inline-flex items-center text-muted-foreground hover:text-foreground mb-6"
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        返回标的列表
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold">{instrument.symbol}</h1>
            <span className="text-muted-foreground">{instrument.name}</span>
          </div>
          <div className="flex gap-2">
            <Badge variant="secondary">{instrument.market}</Badge>
            <Badge variant="outline">{instrument.type}</Badge>
            {instrument.exchange && (
              <Badge variant="outline">{instrument.exchange}</Badge>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="chart">
        <TabsList>
          <TabsTrigger value="chart">K线图</TabsTrigger>
          <TabsTrigger value="signals">相关信号</TabsTrigger>
        </TabsList>

        <TabsContent value="chart" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>日K线</CardTitle>
            </CardHeader>
            <CardContent>
              {bars && bars.length > 0 ? (
                <KLineChart data={bars} height={400} />
              ) : (
                <div className="h-[400px] flex items-center justify-center text-muted-foreground">
                  暂无数据
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="signals" className="mt-6">
          <div className="space-y-4">
            {signals?.items && signals.items.length > 0 ? (
              signals.items.map((signal) => (
                <SignalCard key={signal.id} signal={signal} />
              ))
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                暂无相关信号
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
