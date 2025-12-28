'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LayoutGrid, Activity, PieChart, User } from 'lucide-react'

import { cn } from '@/lib/utils'
import { useAuth } from '@/hooks'

const navItems = [
  {
    title: '策略',
    href: '/marketplace',
    icon: LayoutGrid,
  },
  {
    title: '信号',
    href: '/signals',
    icon: Activity,
  },
  {
    title: '标的',
    href: '/instruments',
    icon: PieChart,
  },
  {
    title: '我的',
    href: '/account',
    icon: User,
  },
]

export function MobileNav() {
  const pathname = usePathname()
  const { isAuthenticated } = useAuth()

  return (
    <nav className="fixed bottom-0 inset-x-0 z-50 bg-background border-t lg:hidden">
      <div className="flex items-center justify-around h-16">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href)
          const href =
            item.href === '/account' && !isAuthenticated ? '/login' : item.href

          return (
            <Link
              key={item.href}
              href={href}
              className={cn(
                'flex flex-col items-center justify-center gap-1 w-full h-full text-xs',
                isActive
                  ? 'text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              <item.icon className="h-5 w-5" />
              <span>{item.title}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
