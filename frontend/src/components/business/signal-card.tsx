'use client'

import { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'
import Link from 'next/link'

import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { AIExplainCard } from './ai-explain-card'
import { Signal } from '@/types'
import { cn } from '@/lib/utils'
import { SIGNAL_SIDES } from '@/lib/constants'

interface SignalCardProps {
  signal: Signal
  className?: string
}

export function SignalCard({ signal, className }: SignalCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const sideConfig = SIGNAL_SIDES.find((s) => s.value === signal.side) || SIGNAL_SIDES[3]

  return (
    <Card className={cn('', className)}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Link
              href={`/instruments/${signal.symbol}`}
              className="font-semibold hover:underline"
            >
              {signal.symbol}
            </Link>
            <span className="text-sm text-muted-foreground">
              {signal.instrumentName}
            </span>
            <Badge className={sideConfig.color}>{sideConfig.label}</Badge>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              置信度 {Math.round(signal.confidence * 100)}%
            </span>
            <span className="text-xs text-muted-foreground">
              {formatDistanceToNow(new Date(signal.createdAt), {
                addSuffix: true,
                locale: zhCN,
              })}
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Reason points */}
        <ul className="text-sm space-y-1 mb-3">
          {signal.reasonPoints.map((reason, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-muted-foreground">•</span>
              {reason}
            </li>
          ))}
        </ul>

        {/* Risk tags */}
        {signal.riskTags.length > 0 && (
          <div className="flex items-center gap-2 mb-3">
            <span className="text-sm text-muted-foreground">风险:</span>
            {signal.riskTags.map((tag) => (
              <Badge key={tag} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        )}

        {/* AI explain collapsible */}
        <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
          <div className="flex items-center gap-2">
            <Link href={`/signals/${signal.id}`}>
              <Button variant="ghost" size="sm">
                查看详情
                <ExternalLink className="ml-1 h-3 w-3" />
              </Button>
            </Link>

            <CollapsibleTrigger asChild>
              <Button variant="ghost" size="sm">
                AI解读
                {isExpanded ? (
                  <ChevronUp className="ml-1 h-4 w-4" />
                ) : (
                  <ChevronDown className="ml-1 h-4 w-4" />
                )}
              </Button>
            </CollapsibleTrigger>
          </div>

          <CollapsibleContent className="mt-3">
            <AIExplainCard signalId={signal.id} />
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  )
}
