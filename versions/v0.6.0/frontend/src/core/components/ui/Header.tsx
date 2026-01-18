import type { ReactNode } from 'react'

interface HeaderProps {
  title: string
  subtitle?: string
  leftContent?: ReactNode
  rightContent?: ReactNode
  className?: string
}

export function Header({
  title,
  subtitle,
  leftContent,
  rightContent,
  className = '',
}: HeaderProps) {
  return (
    <div className={`bg-white rounded-lg shadow-md p-6 mb-6 ${className}`}>
      {(leftContent || rightContent) && (
        <div className="flex justify-between items-center mb-4">
          <div>{leftContent}</div>
          <div>{rightContent}</div>
        </div>
      )}
      <div className="flex flex-col items-center gap-3">
        <h1 className="text-xl font-bold text-gray-800">{title}</h1>
        {subtitle && (
          <p className="text-gray-600 text-sm text-center">{subtitle}</p>
        )}
      </div>
    </div>
  )
}
