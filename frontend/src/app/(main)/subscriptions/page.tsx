'use client'

import Link from 'next/link'
import { useSubscriptions } from '@/hooks'
import { SubscriptionItem } from '@/components/business'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Plus } from 'lucide-react'

export default function SubscriptionsPage() {
  const { data, isLoading } = useSubscriptions()

  const activeCount = data?.items?.filter((s) => s.status === 'active').length ?? 0

  return (
    <div className="container py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">我的订阅</h1>
          <p className="text-muted-foreground">
            {activeCount} 个活跃订阅
          </p>
        </div>
        <Link href="/marketplace">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            添加订阅
          </Button>
        </Link>
      </div>

      {/* Subscriptions List */}
      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      ) : data?.items?.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground mb-4">暂无订阅</p>
          <Link href="/marketplace">
            <Button>去策略广场看看</Button>
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {data?.items?.map((subscription) => (
            <SubscriptionItem key={subscription.id} subscription={subscription} />
          ))}
        </div>
      )}
    </div>
  )
}
