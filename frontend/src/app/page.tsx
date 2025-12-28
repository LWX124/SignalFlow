import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Activity, LayoutGrid, Bell, TrendingUp } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b">
        <div className="container flex h-16 items-center justify-between">
          <Link href="/" className="font-bold text-xl">
            SignalFlow
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/marketplace">
              <Button variant="ghost">策略广场</Button>
            </Link>
            <Link href="/login">
              <Button variant="ghost">登录</Button>
            </Link>
            <Link href="/register">
              <Button>注册</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="container py-24 text-center">
        <h1 className="text-4xl font-bold tracking-tight sm:text-6xl mb-6">
          智能投资信号订阅平台
        </h1>
        <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
          实时推送精选投资策略信号，助您把握每一个投资机会
        </p>
        <div className="flex justify-center gap-4">
          <Link href="/marketplace">
            <Button size="lg">浏览策略</Button>
          </Link>
          <Link href="/register">
            <Button size="lg" variant="outline">
              免费注册
            </Button>
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="container py-24">
        <h2 className="text-3xl font-bold text-center mb-12">核心功能</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardContent className="pt-6">
              <LayoutGrid className="h-12 w-12 mb-4 text-primary" />
              <h3 className="font-semibold text-lg mb-2">策略广场</h3>
              <p className="text-sm text-muted-foreground">
                浏览精选投资策略，选择适合您的投资风格
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <Activity className="h-12 w-12 mb-4 text-primary" />
              <h3 className="font-semibold text-lg mb-2">实时信号</h3>
              <p className="text-sm text-muted-foreground">
                第一时间接收策略产生的投资信号
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <Bell className="h-12 w-12 mb-4 text-primary" />
              <h3 className="font-semibold text-lg mb-2">多渠道推送</h3>
              <p className="text-sm text-muted-foreground">
                支持站内、邮件、微信等多种通知方式
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <TrendingUp className="h-12 w-12 mb-4 text-primary" />
              <h3 className="font-semibold text-lg mb-2">AI 解读</h3>
              <p className="text-sm text-muted-foreground">
                智能分析信号背后的投资逻辑
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12">
        <div className="container text-center text-sm text-muted-foreground">
          <p>&copy; 2024 SignalFlow. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
