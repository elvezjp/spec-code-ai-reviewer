import type { LlmSettings } from '../../../types'
import { Button } from '../../ui/Button'

interface LlmSettingsSectionProps {
  settings?: LlmSettings
  onModelChange: (model: string) => void
  onTestConnection: () => Promise<boolean>
  isSystemFallback?: boolean
}

// デフォルト設定（設定ファイルがない場合に使用）
const DEFAULT_SETTINGS: LlmSettings = {
  provider: 'bedrock',
  maxTokens: 0,
  models: [],
  selectedModel: undefined,
}

export function LlmSettingsSection({
  settings,
  onModelChange,
  onTestConnection,
  isSystemFallback = false,
}: LlmSettingsSectionProps) {
  // settingsがundefinedの場合はデフォルト値を使用
  const effectiveSettings = settings || DEFAULT_SETTINGS
  const handleTestConnection = async () => {
    const statusEl = document.getElementById('llm-connection-status')
    if (!statusEl) return

    statusEl.textContent = '接続テスト中...'
    statusEl.className = 'text-sm text-gray-500'
    statusEl.classList.remove('hidden')

    try {
      const success = await onTestConnection()
      if (success) {
        statusEl.textContent = '接続成功'
        statusEl.className = 'text-sm text-green-600'
      } else {
        statusEl.textContent = '接続失敗'
        statusEl.className = 'text-sm text-red-600'
      }
    } catch {
      statusEl.textContent = '接続エラー'
      statusEl.className = 'text-sm text-red-600'
    }
  }

  const providerDisplayName = {
    anthropic: 'Anthropic',
    bedrock: 'Amazon Bedrock',
    openai: 'OpenAI',
  }

  return (
    <div className="mb-6 border-t border-gray-200 pt-6">
      <h3 className="text-sm font-medium text-gray-700 mb-3">■ LLM設定</h3>

      {/* システムLLM使用時の表示 */}
      {isSystemFallback && (
        <div className="mb-4 p-3 border border-gray-300 rounded-lg">
          <p className="text-sm text-gray-700">
            LLM未設定のため、システムのデフォルトモデルを使用します。
          </p>
          <p className="text-xs text-gray-500 mt-1">
            独自のAPIキーを使用する場合は、設定ファイルをアップロードしてください。
          </p>
        </div>
      )}

      {/* プロバイダー表示 */}
      <div className="mb-4">
        <label className="block text-sm text-gray-600 mb-1">プロバイダー:</label>
        <div className={isSystemFallback ? 'text-gray-500' : 'text-gray-800'}>
          {!isSystemFallback && effectiveSettings.provider
            ? providerDisplayName[effectiveSettings.provider]
            : '-'}
        </div>
      </div>

      {/* 出力最大トークン数（設定ファイル指定時のみ表示） */}
      {!isSystemFallback && effectiveSettings.maxTokens > 0 && (
        <div className="mb-4">
          <label className="block text-sm text-gray-600 mb-1">
            出力最大トークン数:
          </label>
          <div className="text-gray-800">
            {effectiveSettings.maxTokens.toLocaleString()}
          </div>
        </div>
      )}

      {/* 使用モデル */}
      <div className="mb-4">
        <label className="block text-sm text-gray-600 mb-1">使用モデル:</label>
        <select
          value={effectiveSettings.selectedModel || ''}
          onChange={(e) => onModelChange(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
          disabled={isSystemFallback || effectiveSettings.models.length === 0}
        >
          {isSystemFallback || effectiveSettings.models.length === 0 ? (
            <option value="">システムのデフォルトモデルを使用</option>
          ) : (
            effectiveSettings.models.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))
          )}
        </select>
      </div>

      {/* 接続テスト */}
      <div className="flex items-center gap-3">
        <Button variant="secondary" size="sm" onClick={handleTestConnection}>
          接続テスト
        </Button>
        <span id="llm-connection-status" className="text-sm hidden">
          接続成功
        </span>
      </div>
    </div>
  )
}
