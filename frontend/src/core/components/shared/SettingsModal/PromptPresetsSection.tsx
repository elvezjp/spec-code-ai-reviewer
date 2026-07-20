import type { SystemPromptPreset } from '../../../types'

interface PromptPresetsSectionProps {
  presets: SystemPromptPreset[]
}

export function PromptPresetsSection({ presets }: PromptPresetsSectionProps) {
  return (
    <div className="mb-6 border-t border-gray-200 pt-6">
      <h3 className="text-sm font-medium text-gray-700 mb-3">
        ■ システムプロンプトプリセット
      </h3>

      {presets.length === 0 ? (
        <p className="text-gray-500 text-sm">
          プリセットが設定されていません
        </p>
      ) : (
        <ul className="text-sm text-gray-700 space-y-1">
          {presets.map((preset) => (
            <li key={preset.name} className="flex items-center gap-2">
              <span className="text-gray-400">•</span>
              <span>{preset.name}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
