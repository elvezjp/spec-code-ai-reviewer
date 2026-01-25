import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import type { SystemPromptPreset } from '../../types'

interface SystemPromptEditorProps {
  presets: SystemPromptPreset[]
  selectedPreset: string
  currentValues: {
    role: string
    purpose: string
    format: string
    notes: string
  }
  onPresetChange: (presetName: string) => void
  onValueChange: (
    field: 'role' | 'purpose' | 'format' | 'notes',
    value: string
  ) => void
  isCollapsible?: boolean
  defaultExpanded?: boolean
}

export function SystemPromptEditor({
  presets,
  selectedPreset,
  currentValues,
  onPresetChange,
  onValueChange,
  isCollapsible = true,
  defaultExpanded = false,
}: SystemPromptEditorProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  const content = (
    <div className="mt-4 space-y-4">
      {/* プリセット選択 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          プロンプトプリセット
        </label>
        <select
          value={selectedPreset}
          onChange={(e) => onPresetChange(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          {presets.map((preset) => (
            <option key={preset.name} value={preset.name}>
              {preset.name}
            </option>
          ))}
        </select>
        <p className="text-xs text-gray-400 mt-1">
          選択したプリセットで各入力欄が更新されます。プリセットライブラリのプリセットを選択すると、設計書種別も更新されます。
        </p>
      </div>

      {/* 役割 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          役割
        </label>
        <textarea
          value={currentValues.role}
          onChange={(e) => onValueChange('role', e.target.value)}
          rows={2}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <p className="text-xs text-gray-400 mt-1">
          AIの役割を簡潔に記載します
        </p>
      </div>

      {/* 目的 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          目的
        </label>
        <textarea
          value={currentValues.purpose}
          onChange={(e) => onValueChange('purpose', e.target.value)}
          rows={7}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <p className="text-xs text-gray-400 mt-1">
          どのようなタスクを行うか（レビュー観点を含む）
        </p>
      </div>

      {/* 出力形式 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          出力形式
        </label>
        <textarea
          value={currentValues.format}
          onChange={(e) => onValueChange('format', e.target.value)}
          rows={7}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <p className="text-xs text-gray-400 mt-1">
          出力のフォーマットを指定します
        </p>
      </div>

      {/* 注意事項 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          注意事項
        </label>
        <textarea
          value={currentValues.notes}
          onChange={(e) => onValueChange('notes', e.target.value)}
          rows={7}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <p className="text-xs text-gray-400 mt-1">
          実行上の制約、判断基準、例外時の対応を記載します
        </p>
      </div>
    </div>
  )

  if (!isCollapsible) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-800">
          システムプロンプト設定
        </h2>
        <p className="text-xs text-gray-400 mt-2">
          AIへの指示内容が設定されています。変更したい場合に編集してください。
        </p>
        {content}
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex justify-between items-center text-lg font-semibold text-gray-800"
      >
        <span>システムプロンプト設定</span>
        <ChevronDown
          className={`w-5 h-5 text-gray-500 transition-transform ${
            isExpanded ? 'rotate-180' : ''
          }`}
        />
      </button>
      <p className="text-xs text-gray-400 mt-2">
        AIへの指示内容が設定されています。変更したい場合に編集してください。
      </p>

      <div className={isExpanded ? '' : 'hidden'}>{content}</div>
    </div>
  )
}
