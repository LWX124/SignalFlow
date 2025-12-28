'use client'

import { useSignal, useSignalExplain } from '@/hooks'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { SIGNAL_SIDES } from '@/lib/constants'
import { formatDistanceToNow, format } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'

interface PageProps {
  params: { signalId: string }
}

export default function SignalDetailPage({ params }: PageProps) {
  const { data: signal, isLoading } = useSignal(params.signalId)
  const { data: explain, isLoading: isLoadingExplain } = useSignalExplain(params.signalId)

  const sideConfig = SIGNAL_SIDES.find((s) => s.value === signal?.side) || SIGNAL_SIDES[3]

  if (isLoading) {
    return (
      <div className="container py-6">
        <Skeleton className="h-8 w-48 mb-6" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!signal) {
    return (
      <div className="container py-6">
        <p className="text-muted-foreground">信号不存在</p>
      </div>
    )
  }

  return (
    <div className="container py-6 max-w-4xl">
      {/* Back link */}
      <Link
        href="/signals"
        className="inline-flex items-center text-muted-foreground hover:text-foreground mb-6"
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        返回信号流
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Link
              href={`/instruments/${signal.symbol}`}
              className="text-2xl font-bold hover:underline"
            >
              {signal.symbol}
            </Link>
            <span className="text-muted-foreground">{signal.instrumentName}</span>
            <Badge className={sideConfig.color}>{sideConfig.label}</Badge>
          </div>
          <p className="text-muted-foreground">
            {format(new Date(signal.createdAt), 'yyyy-MM-dd HH:mm:ss')} (
            {formatDistanceToNow(new Date(signal.createdAt), {
              addSuffix: true,
              locale: zhCN,
            })}
            )
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-muted-foreground">置信度</p>
          <p className="text-2xl font-bold">{Math.round(signal.confidence * 100)}%</p>
        </div>
      </div>

      {/* Signal Summary */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>信号摘要</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-sm text-muted-foreground">策略</p>
              <p className="font-medium">{signal.strategyName || signal.strategyId}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">市场</p>
              <p className="font-medium">{signal.market}</p>
            </div>
          </div>

          <div>
            <p className="text-sm text-muted-foreground mb-2">触发原因</p>
            <ul className="space-y-1">
              {signal.reasonPoints.map((reason, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-muted-foreground">•</span>
                  {reason}
                </li>
              ))}
            </ul>
          </div>

          {signal.riskTags.length > 0 && (
            <div className="mt-4">
              <p className="text-sm text-muted-foreground mb-2">风险提示</p>
              <div className="flex gap-2">
                {signal.riskTags.map((tag) => (
                  <Badge key={tag} variant="outline">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* AI Explain */}
      <Card>
        <CardHeader>
          <CardTitle>AI 解读</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoadingExplain ? (
            <div className="space-y-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
            </div>
          ) : explain?.content ? (
            <p className="whitespace-pre-wrap">{explain.content}</p>
          ) : (
            <p className="text-muted-foreground">暂无 AI 解读</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
