import type { ReactNode } from 'react'

interface LayoutProps {
  children: ReactNode
  className?: string
}

export function Layout({ children, className = '' }: LayoutProps) {
  return (
    <div className={`max-w-4xl mx-auto p-6 ${className}`}>
      {children}
    </div>
  )
}
