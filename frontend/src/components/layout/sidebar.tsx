'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutGrid,
  Activity,
  PieChart,
  Bell,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { useUIStore } from '@/stores'
import { useAuth } from '@/hooks'

const navItems = [
  {
    title: '策略广场',
    href: '/marketplace',
    icon: LayoutGrid,
    public: true,
  },
  {
    title: '信号流',
    href: '/signals',
    icon: Activity,
    public: false,
  },
  {
    title: '标的',
    href: '/instruments',
    icon: PieChart,
    public: true,
  },
  {
    title: '我的订阅',
    href: '/subscriptions',
    icon: Settings,
    public: false,
  },
  {
    title: '通知中心',
    href: '/notifications',
    icon: Bell,
    public: false,
  },
]

export function Sidebar() {
  const pathname = usePathname()
  const { isAuthenticated } = useAuth()
  const { sidebarCollapsed, setSidebarCollapsed } = useUIStore()

  const filteredNavItems = navItems.filter(
    (item) => item.public || isAuthenticated
  )

  return (
    <aside
      className={cn(
        'hidden lg:flex flex-col border-r bg-background transition-all duration-300',
        sidebarCollapsed ? 'w-16' : 'w-64'
      )}
    >
      <div className="flex-1 overflow-y-auto py-4">
        <nav className="flex flex-col gap-1 px-2">
          {filteredNavItems.map((item) => {
            const isActive = pathname.startsWith(item.href)
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
              >
                <item.icon className="h-5 w-5 shrink-0" />
                {!sidebarCollapsed && <span>{item.title}</span>}
              </Link>
            )
          })}
        </nav>
      </div>

      {/* Collapse button */}
      <div className="border-t p-2">
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-center"
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4 mr-2" />
              <span>收起</span>
            </>
          )}
        </Button>
      </div>
    </aside>
  )
}
