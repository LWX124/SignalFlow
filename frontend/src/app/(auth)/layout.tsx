import Link from 'next/link'

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <Link href="/" className="font-bold text-2xl mb-8">
        SignalFlow
      </Link>
      {children}
    </div>
  )
}
