'use client'

import { useCallback } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Bell, Menu, Search, User, LogOut, Settings } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { useAuth } from '@/hooks'
import { useUIStore, useNotificationStore } from '@/stores'
import { Badge } from '@/components/ui/badge'

export function Header() {
  const router = useRouter()
  const { user, isAuthenticated, logout } = useAuth()
  const { setMobileMenuOpen } = useUIStore()
  const unreadCount = useNotificationStore((s) => s.unreadCount)

  // Memoized navigation handlers to prevent unnecessary re-renders
  const handleOpenMobileMenu = useCallback(() => setMobileMenuOpen(true), [setMobileMenuOpen])
  const handleNavigateNotifications = useCallback(() => router.push('/notifications'), [router])
  const handleNavigateAccount = useCallback(() => router.push('/account'), [router])
  const handleNavigateSubscriptions = useCallback(() => router.push('/subscriptions'), [router])
  const handleNavigateLogin = useCallback(() => router.push('/login'), [router])
  const handleNavigateRegister = useCallback(() => router.push('/register'), [router])

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        {/* Mobile menu button */}
        <Button
          variant="ghost"
          size="icon"
          className="mr-2 lg:hidden"
          onClick={handleOpenMobileMenu}
        >
          <Menu className="h-5 w-5" />
          <span className="sr-only">Toggle menu</span>
        </Button>

        {/* Logo */}
        <Link href="/" className="mr-6 flex items-center space-x-2">
          <span className="font-bold text-xl">SignalFlow</span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden lg:flex items-center space-x-6 text-sm font-medium">
          <Link
            href="/marketplace"
            className="transition-colors hover:text-foreground/80 text-foreground/60"
          >
            策略广场
          </Link>
          <Link
            href="/signals"
            className="transition-colors hover:text-foreground/80 text-foreground/60"
          >
            信号流
          </Link>
          <Link
            href="/instruments"
            className="transition-colors hover:text-foreground/80 text-foreground/60"
          >
            标的
          </Link>
          {isAuthenticated && (
            <Link
              href="/subscriptions"
              className="transition-colors hover:text-foreground/80 text-foreground/60"
            >
              我的订阅
            </Link>
          )}
        </nav>

        {/* Right side */}
        <div className="flex flex-1 items-center justify-end space-x-4">
          {/* Search */}
          <div className="hidden md:flex w-full max-w-sm items-center space-x-2">
            <div className="relative w-full">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="搜索策略或标的..."
                className="pl-8 w-full"
              />
            </div>
          </div>

          {isAuthenticated ? (
            <>
              {/* Notifications */}
              <Button
                variant="ghost"
                size="icon"
                className="relative"
                onClick={handleNavigateNotifications}
              >
                <Bell className="h-5 w-5" />
                {unreadCount > 0 && (
                  <Badge
                    className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs"
                    variant="destructive"
                  >
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </Badge>
                )}
                <span className="sr-only">Notifications</span>
              </Button>

              {/* User menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="relative h-8 w-8 rounded-full"
                  >
                    <Avatar className="h-8 w-8">
                      <AvatarImage src={user?.avatarUrl} alt={user?.nickname} />
                      <AvatarFallback>
                        {user?.nickname?.charAt(0).toUpperCase() || 'U'}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end" forceMount>
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium leading-none">
                        {user?.nickname}
                      </p>
                      <p className="text-xs leading-none text-muted-foreground">
                        {user?.email}
                      </p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleNavigateAccount}>
                    <User className="mr-2 h-4 w-4" />
                    <span>账户设置</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={handleNavigateSubscriptions}>
                    <Settings className="mr-2 h-4 w-4" />
                    <span>订阅管理</span>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={logout}>
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>退出登录</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          ) : (
            <div className="flex items-center space-x-2">
              <Button variant="ghost" onClick={handleNavigateLogin}>
                登录
              </Button>
              <Button onClick={handleNavigateRegister}>注册</Button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
