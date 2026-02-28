import { useState, useRef, useEffect } from 'react'
import type { VersionInfo } from '../../types'

interface VersionSelectorProps {
  versions: VersionInfo[]
  currentVersion: VersionInfo
  onVersionSelect: (version: string) => void
}

export function VersionSelector({
  versions,
  currentVersion,
  onVersionSelect,
}: VersionSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  // 外側クリックで閉じる
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false)
      }
    }
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [])

  const handleVersionClick = (version: string) => {
    onVersionSelect(version)
    setIsOpen(false)
  }

  return (
    <div ref={containerRef} className="relative inline-block">
      {/* ピル型ボタン */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-1.5 px-4 py-2 border border-gray-200 rounded-full bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition shadow-sm"
      >
        <span>{currentVersion.label}</span>
        <svg
          className={`w-3 h-3 text-gray-500 transition-transform ${
            isOpen ? 'rotate-90' : ''
          }`}
          viewBox="0 0 12 12"
        >
          <path
            d="M4.5 3L7.5 6L4.5 9"
            stroke="currentColor"
            strokeWidth="1.5"
            fill="none"
          />
        </svg>
      </button>

      {/* バルーン */}
      {isOpen && (
        <div className="absolute top-full left-1/2 -translate-x-1/2 mt-3 min-w-60 bg-white border border-gray-200 rounded-2xl shadow-lg z-50 py-2">
          {/* 三角形ポインタ */}
          <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-0 h-0 border-l-[12px] border-l-transparent border-r-[12px] border-r-transparent border-b-[12px] border-b-gray-200" />
          <div className="absolute -top-2.5 left-1/2 -translate-x-1/2 w-0 h-0 border-l-[11px] border-l-transparent border-r-[11px] border-r-transparent border-b-[11px] border-b-white" />

          {versions.map((version, index) => (
            <div key={version.value}>
              {index > 0 && <div className="h-px bg-gray-200 my-2" />}
              <button
                onClick={() => handleVersionClick(version.value)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-100 transition"
              >
                <span className="text-sm font-medium text-gray-900">
                  {version.label}
                  {version.isLatest && '（最新）'}
                </span>
                {version.value === currentVersion.value && (
                  <svg className="w-4 h-4 text-gray-900" viewBox="0 0 16 16">
                    <path
                      d="M13.5 4.5L6 12L2.5 8.5"
                      stroke="currentColor"
                      strokeWidth="2"
                      fill="none"
                    />
                  </svg>
                )}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
