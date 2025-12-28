'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { SubscribeDialog } from './subscribe-dialog'
import { Strategy } from '@/types'
import { cn } from '@/lib/utils'
import { RISK_LEVELS } from '@/lib/constants'

interface StrategyCardProps {
  strategy: Strategy
  className?: string
}

export function StrategyCard({ strategy, className }: StrategyCardProps) {
  const router = useRouter()
  const [showSubscribe, setShowSubscribe] = useState(false)

  const riskConfig = RISK_LEVELS.find((r) => r.value === strategy.riskLevel) || RISK_LEVELS[1]

  return (
    <>
      <Card
        className={cn(
          'hover:shadow-lg transition-shadow cursor-pointer',
          className
        )}
        onClick={() => router.push(`/marketplace/${strategy.id}`)}
      >
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-semibold text-lg">{strategy.name}</h3>
              <p className="text-sm text-muted-foreground">{strategy.type}</p>
            </div>
            <Badge className={riskConfig.color}>
              {riskConfig.label}
            </Badge>
          </div>
        </CardHeader>

        <CardContent>
          <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
            {strategy.description}
          </p>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">近30天信号</span>
              <p className="font-medium">{strategy.metricsSummary?.signalCount ?? 0} 次</p>
            </div>
            <div>
              <span className="text-muted-foreground">历史命中率</span>
              <p className="font-medium">
                {((strategy.metricsSummary?.hitRate ?? 0) * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        </CardContent>

        <CardFooter className="pt-2 gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={(e) => {
              e.stopPropagation()
              router.push(`/marketplace/${strategy.id}`)
            }}
          >
            查看详情
          </Button>
          <Button
            size="sm"
            onClick={(e) => {
              e.stopPropagation()
              setShowSubscribe(true)
            }}
          >
            订阅
          </Button>
        </CardFooter>
      </Card>

      <SubscribeDialog
        strategy={strategy}
        open={showSubscribe}
        onOpenChange={setShowSubscribe}
      />
    </>
  )
}
