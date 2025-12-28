'use client'

import { Header } from './header'
import { Sidebar } from './sidebar'
import { MobileNav } from './mobile-nav'

interface MainLayoutProps {
  children: React.ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <div className="flex-1 flex">
        <Sidebar />
        <main className="flex-1 overflow-y-auto pb-16 lg:pb-0">{children}</main>
      </div>
      <MobileNav />
    </div>
  )
}
