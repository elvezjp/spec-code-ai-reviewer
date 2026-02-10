import type { ReviewMode } from '@core/types'

interface ModeSelectorProps {
  currentMode: ReviewMode
  onModeChange: (mode: ReviewMode) => void
}

export function ModeSelector({ currentMode, onModeChange }: ModeSelectorProps) {
  const modes = [
    { mode: 'review' as const, label: '突合モード', description: '設計書とコードの整合性を検証' },
    { mode: 'mapping' as const, label: 'マッピングモード', description: '設計項目と実装箇所を対応付け' },
  ]

  return (
    <div className="bg-white rounded-lg shadow-md p-4 mb-6">
      <div className="flex gap-2">
        {modes.map(({ mode, label, description }) => (
          <button
            key={mode}
            onClick={() => onModeChange(mode)}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition ${
              currentMode === mode
                ? 'text-white bg-blue-500'
                : 'text-gray-600 bg-gray-100 hover:bg-gray-200'
            }`}
          >
            <div>{label}</div>
            <div className="text-xs opacity-75">{description}</div>
          </button>
        ))}
      </div>
    </div>
  )
}
