'use client'

import { useNotifications, useMarkAsRead, useMarkAllAsRead } from '@/hooks'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { Check, CheckCheck, Bell, Info, Megaphone } from 'lucide-react'

const notificationIcons = {
  signal: Bell,
  system: Info,
  promotion: Megaphone,
}

export default function NotificationsPage() {
  const { data, isLoading } = useNotifications()
  const { mutate: markAsRead } = useMarkAsRead()
  const { mutate: markAllAsRead, isPending: isMarkingAll } = useMarkAllAsRead()

  const unreadCount = data?.unreadCount ?? 0

  return (
    <div className="container py-6 max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">通知中心</h1>
          {unreadCount > 0 && (
            <p className="text-muted-foreground">{unreadCount} 条未读</p>
          )}
        </div>
        {unreadCount > 0 && (
          <Button
            variant="outline"
            onClick={() => markAllAsRead()}
            disabled={isMarkingAll}
          >
            <CheckCheck className="h-4 w-4 mr-2" />
            全部已读
          </Button>
        )}
      </div>

      {/* Notifications List */}
      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      ) : data?.items?.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          暂无通知
        </div>
      ) : (
        <div className="space-y-2">
          {data?.items?.map((notification) => {
            const Icon = notificationIcons[notification.type] || Bell
            return (
              <Card
                key={notification.id}
                className={notification.isRead ? 'opacity-60' : ''}
              >
                <CardContent className="p-4 flex items-start gap-4">
                  <div className="p-2 bg-muted rounded-full">
                    <Icon className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <p className="font-medium">{notification.title}</p>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">
                          {formatDistanceToNow(new Date(notification.createdAt), {
                            addSuffix: true,
                            locale: zhCN,
                          })}
                        </span>
                        {!notification.isRead && (
                          <Badge variant="default" className="h-5 px-1.5">
                            新
                          </Badge>
                        )}
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {notification.content}
                    </p>
                    {!notification.isRead && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="mt-2 h-7 px-2"
                        onClick={() => markAsRead(notification.id)}
                      >
                        <Check className="h-3 w-3 mr-1" />
                        标为已读
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
