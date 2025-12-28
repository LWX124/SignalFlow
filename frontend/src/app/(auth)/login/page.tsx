'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { AxiosError } from 'axios'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { useAuth } from '@/hooks'
import { toast } from '@/components/ui/use-toast'

const formSchema = z.object({
  email: z.string().email('请输入有效的邮箱地址'),
  password: z.string().min(6, '密码至少6个字符'),
})

// Validate redirect URL to prevent open redirect attacks
function getSafeRedirect(redirect: string | null): string {
  const defaultPath = '/marketplace'
  if (!redirect) return defaultPath

  // Only allow internal paths (starting with / but not //)
  if (redirect.startsWith('/') && !redirect.startsWith('//')) {
    // Additional check: ensure no protocol in the path
    try {
      const url = new URL(redirect, 'http://localhost')
      if (url.origin === 'http://localhost') {
        return redirect
      }
    } catch {
      // Invalid URL, use default
    }
  }
  return defaultPath
}

export default function LoginPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const redirect = getSafeRedirect(searchParams.get('redirect'))
  const { login, isLoggingIn } = useAuth()

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  })

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    try {
      await login(values)
      toast({ title: '登录成功' })
      router.push(redirect)
    } catch (error) {
      // Extract detailed error message from Axios response
      let errorMessage = '请检查邮箱和密码'
      if (error instanceof AxiosError) {
        errorMessage = error.response?.data?.message || error.response?.data?.detail || error.message
      } else if (error instanceof Error) {
        errorMessage = error.message
      }

      toast({
        title: '登录失败',
        description: errorMessage,
        variant: 'destructive',
      })
    }
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl text-center">登录</CardTitle>
        <CardDescription className="text-center">
          输入您的邮箱和密码登录
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>邮箱</FormLabel>
                  <FormControl>
                    <Input
                      type="email"
                      placeholder="your@email.com"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>密码</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="••••••" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full" disabled={isLoggingIn}>
              {isLoggingIn ? '登录中...' : '登录'}
            </Button>
          </form>
        </Form>
      </CardContent>
      <CardFooter className="flex justify-center">
        <p className="text-sm text-muted-foreground">
          还没有账号？{' '}
          <Link href="/register" className="text-primary hover:underline">
            立即注册
          </Link>
        </p>
      </CardFooter>
    </Card>
  )
}
