'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { subscriptionsApi } from '@/services/api'
import { queryKeys } from '@/lib/query-client'
import { CreateSubscriptionRequest, UpdateSubscriptionRequest } from '@/types'

export function useSubscriptions() {
  return useQuery({
    queryKey: queryKeys.subscriptions.list(),
    queryFn: () => subscriptionsApi.list(),
  })
}

export function useSubscription(id: string) {
  return useQuery({
    queryKey: queryKeys.subscriptions.detail(id),
    queryFn: () => subscriptionsApi.getById(id),
    enabled: !!id,
  })
}

export function useCreateSubscription() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: CreateSubscriptionRequest) =>
      subscriptionsApi.create(request),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.subscriptions.all,
      })
    },
  })
}

export function useUpdateSubscription() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: UpdateSubscriptionRequest }) =>
      subscriptionsApi.update(id, request),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.subscriptions.all,
      })
    },
  })
}

export function useDeleteSubscription() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => subscriptionsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.subscriptions.all,
      })
    },
  })
}

export function useToggleSubscription() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, enable }: { id: string; enable: boolean }) =>
      enable ? subscriptionsApi.enable(id) : subscriptionsApi.disable(id),
    onMutate: async ({ id, enable }) => {
      // Optimistic update
      await queryClient.cancelQueries({
        queryKey: queryKeys.subscriptions.list(),
      })

      const previous = queryClient.getQueryData(queryKeys.subscriptions.list())

      queryClient.setQueryData(queryKeys.subscriptions.list(), (old: { items: Array<{ id: string; status: string }> } | undefined) => ({
        ...old,
        items: old?.items?.map((sub) =>
          sub.id === id
            ? { ...sub, status: enable ? 'active' : 'paused' }
            : sub
        ),
      }))

      return { previous }
    },
    onError: (_err, _variables, context) => {
      queryClient.setQueryData(
        queryKeys.subscriptions.list(),
        context?.previous
      )
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.subscriptions.all,
      })
    },
  })
}
