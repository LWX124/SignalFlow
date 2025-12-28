'use client'

import { useSignalExplain } from '@/hooks'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

interface AIExplainCardProps {
  signalId: string
}

export function AIExplainCard({ signalId }: AIExplainCardProps) {
  const { data, isLoading, error } = useSignalExplain(signalId)

  if (isLoading) {
    return (
      <Card className="bg-muted/50">
        <CardContent className="p-4">
          <Skeleton className="h-4 w-3/4 mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-5/6" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="bg-muted/50">
        <CardContent className="p-4 text-sm text-muted-foreground">
          AI解读加载失败
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="bg-muted/50">
      <CardContent className="p-4">
        <p className="text-sm whitespace-pre-wrap">{data?.content}</p>
      </CardContent>
    </Card>
  )
}
