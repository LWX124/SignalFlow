'use client'

import { useState } from 'react'
import { useStrategy, useStrategyPerformance } from '@/hooks'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import { SubscribeDialog } from '@/components/business'
import { RISK_LEVELS } from '@/lib/constants'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'

interface PageProps {
  params: { strategyId: string }
}

export default function StrategyDetailPage({ params }: PageProps) {
  const [showSubscribe, setShowSubscribe] = useState(false)
  const { data: strategy, isLoading } = useStrategy(params.strategyId)
  const { data: performance } = useStrategyPerformance(params.strategyId)

  const riskConfig = RISK_LEVELS.find((r) => r.value === strategy?.riskLevel) || RISK_LEVELS[1]

  if (isLoading) {
    return (
      <div className="container py-6">
        <Skeleton className="h-8 w-48 mb-6" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!strategy) {
    return (
      <div className="container py-6">
        <p className="text-muted-foreground">策略不存在</p>
      </div>
    )
  }

  return (
    <div className="container py-6">
      {/* Back link */}
      <Link
        href="/marketplace"
        className="inline-flex items-center text-muted-foreground hover:text-foreground mb-6"
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        返回策略广场
      </Link>

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold">{strategy.name}</h1>
            <Badge className={riskConfig.color}>{riskConfig.label}</Badge>
          </div>
          <p className="text-muted-foreground">{strategy.description}</p>
        </div>
        <Button size="lg" onClick={() => setShowSubscribe(true)}>
          订阅策略
        </Button>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">概览</TabsTrigger>
          <TabsTrigger value="performance">历史表现</TabsTrigger>
          <TabsTrigger value="params">参数说明</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  策略类型
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{strategy.type}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  适用市场
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{strategy.markets.join(', ')}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  信号频率
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{strategy.frequencyHint || '日内'}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  所需等级
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold capitalize">{strategy.tierRequired}</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="performance" className="mt-6">
          <div className="grid md:grid-cols-3 gap-6">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  近30天信号数
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {performance?.signalCount ?? strategy.metricsSummary?.signalCount ?? 0}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  历史命中率
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {((strategy.metricsSummary?.hitRate ?? 0) * 100).toFixed(1)}%
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  平均收益
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {((strategy.metricsSummary?.avgReturn ?? 0) * 100).toFixed(2)}%
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="params" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>策略参数</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(strategy.paramsSchema?.properties || {}).map(
                  ([key, prop]: [string, Record<string, unknown>]) => (
                    <div key={key} className="flex justify-between border-b pb-2">
                      <div>
                        <p className="font-medium">{(prop.description as string) || key}</p>
                        <p className="text-sm text-muted-foreground">
                          默认值: {String(strategy.defaultParams?.[key] ?? '-')}
                        </p>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        类型: {String(prop.type)}
                      </p>
                    </div>
                  )
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <SubscribeDialog
        strategy={strategy}
        open={showSubscribe}
        onOpenChange={setShowSubscribe}
      />
    </div>
  )
}
