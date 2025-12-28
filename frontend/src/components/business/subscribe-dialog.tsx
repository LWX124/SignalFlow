'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { useCreateSubscription } from '@/hooks'
import { Strategy, NotificationChannel } from '@/types'
import { toast } from '@/components/ui/use-toast'
import { NOTIFICATION_CHANNELS } from '@/lib/constants'

interface SubscribeDialogProps {
  strategy: Strategy
  open: boolean
  onOpenChange: (open: boolean) => void
}

const formSchema = z.object({
  channels: z.array(z.string()).min(1, '至少选择一个推送渠道'),
  cooldownMinutes: z.number().min(1).max(1440),
})

export function SubscribeDialog({
  strategy,
  open,
  onOpenChange,
}: SubscribeDialogProps) {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      channels: ['site'],
      cooldownMinutes: strategy.defaultCooldown / 60,
    },
  })

  const { mutate: createSubscription, isPending } = useCreateSubscription()

  const onSubmit = (values: z.infer<typeof formSchema>) => {
    createSubscription(
      {
        strategyId: strategy.id,
        params: strategy.defaultParams,
        channels: values.channels as NotificationChannel[],
        cooldownSeconds: values.cooldownMinutes * 60,
      },
      {
        onSuccess: () => {
          toast({ title: '订阅成功' })
          onOpenChange(false)
          form.reset()
        },
        onError: (error) => {
          toast({
            title: '订阅失败',
            description: error.message,
            variant: 'destructive',
          })
        },
      }
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>订阅 {strategy.name}</DialogTitle>
          <DialogDescription>
            设置推送渠道和冷却时间
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* Push channels */}
            <FormField
              control={form.control}
              name="channels"
              render={() => (
                <FormItem>
                  <FormLabel>推送渠道</FormLabel>
                  <div className="flex flex-wrap gap-4">
                    {NOTIFICATION_CHANNELS.map((option) => (
                      <FormField
                        key={option.id}
                        control={form.control}
                        name="channels"
                        render={({ field }) => (
                          <FormItem className="flex items-center space-x-2 space-y-0">
                            <FormControl>
                              <Checkbox
                                checked={field.value?.includes(option.id)}
                                onCheckedChange={(checked) => {
                                  const current = field.value || []
                                  if (checked) {
                                    field.onChange([...current, option.id])
                                  } else {
                                    field.onChange(
                                      current.filter((v) => v !== option.id)
                                    )
                                  }
                                }}
                              />
                            </FormControl>
                            <FormLabel className="font-normal cursor-pointer">
                              {option.label}
                            </FormLabel>
                          </FormItem>
                        )}
                      />
                    ))}
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Cooldown time */}
            <FormField
              control={form.control}
              name="cooldownMinutes"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>冷却时间（分钟）</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      min={1}
                      max={1440}
                      {...field}
                      onChange={(e) => field.onChange(parseInt(e.target.value) || 60)}
                    />
                  </FormControl>
                  <FormDescription>
                    同一标的在冷却期内不会重复推送
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                取消
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? '订阅中...' : '确认订阅'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
