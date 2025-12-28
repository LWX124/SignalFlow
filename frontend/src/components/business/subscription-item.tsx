'use client'

import { useState } from 'react'
import { Settings, Pause, Play, Trash2 } from 'lucide-react'

import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useToggleSubscription, useDeleteSubscription } from '@/hooks'
import { Subscription } from '@/types'
import { toast } from '@/components/ui/use-toast'
import { SUBSCRIPTION_STATUS, NOTIFICATION_CHANNELS } from '@/lib/constants'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'

interface SubscriptionItemProps {
  subscription: Subscription
}

export function SubscriptionItem({ subscription }: SubscriptionItemProps) {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  const { mutate: toggleSubscription, isPending: isToggling } = useToggleSubscription()
  const { mutate: deleteSubscription, isPending: isDeleting } = useDeleteSubscription()

  const statusConfig = SUBSCRIPTION_STATUS.find(
    (s) => s.value === subscription.status
  ) || SUBSCRIPTION_STATUS[0]

  const isActive = subscription.status === 'active'

  const handleToggle = () => {
    toggleSubscription(
      { id: subscription.id, enable: !isActive },
      {
        onSuccess: () => {
          toast({
            title: isActive ? '已暂停订阅' : '已启用订阅',
          })
        },
        onError: (error) => {
          toast({
            title: '操作失败',
            description: error.message,
            variant: 'destructive',
          })
        },
      }
    )
  }

  const handleDelete = () => {
    deleteSubscription(subscription.id, {
      onSuccess: () => {
        toast({ title: '订阅已删除' })
        setShowDeleteDialog(false)
      },
      onError: (error) => {
        toast({
          title: '删除失败',
          description: error.message,
          variant: 'destructive',
        })
      },
    })
  }

  const channelLabels = subscription.channels
    .map((ch) => NOTIFICATION_CHANNELS.find((c) => c.id === ch)?.label || ch)
    .join('、')

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-semibold">{subscription.strategyName}</h3>
              <Badge className={statusConfig.color}>{statusConfig.label}</Badge>
            </div>

            <div className="text-sm text-muted-foreground space-y-1">
              <p>推送渠道: {channelLabels}</p>
              <p>冷却时间: {subscription.cooldownSeconds / 60} 分钟</p>
              {subscription.signalCount7d !== undefined && (
                <p>近7天: {subscription.signalCount7d} 条信号</p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" disabled>
              <Settings className="h-4 w-4" />
            </Button>

            <Button
              variant="ghost"
              size="icon"
              onClick={handleToggle}
              disabled={isToggling}
            >
              {isActive ? (
                <Pause className="h-4 w-4" />
              ) : (
                <Play className="h-4 w-4" />
              )}
            </Button>

            <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
              <AlertDialogTrigger asChild>
                <Button variant="ghost" size="icon">
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>确认删除订阅？</AlertDialogTitle>
                  <AlertDialogDescription>
                    删除后将不再接收该策略的信号推送，此操作无法撤销。
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>取消</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={handleDelete}
                    disabled={isDeleting}
                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  >
                    {isDeleting ? '删除中...' : '确认删除'}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
