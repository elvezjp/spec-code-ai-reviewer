import { AlertTriangle } from 'lucide-react'

interface TokenEstimatorProps {
  totalTokens: number
  specTokens?: number
  codeTokens?: number
  promptTokens?: number
  isWarning: boolean
  isVisible?: boolean
}

export function TokenEstimator({
  totalTokens,
  specTokens,
  codeTokens,
  promptTokens,
  isWarning,
  isVisible = true,
}: TokenEstimatorProps) {
  if (!isVisible) return null

  const showBreakdown = specTokens !== undefined || codeTokens !== undefined || promptTokens !== undefined

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">推定入力トークン数</h2>
        <span
          className={`text-sm font-bold ${
            isWarning ? 'text-orange-600' : 'text-gray-800'
          }`}
        >
          {totalTokens.toLocaleString()} トークン
        </span>
      </div>
      {showBreakdown && (
        <div className="mt-3 text-sm text-gray-600 space-y-1">
          {specTokens !== undefined && specTokens > 0 && (
            <div className="flex justify-between">
              <span>設計書:</span>
              <span>{specTokens.toLocaleString()} トークン</span>
            </div>
          )}
          {codeTokens !== undefined && codeTokens > 0 && (
            <div className="flex justify-between">
              <span>プログラム:</span>
              <span>{codeTokens.toLocaleString()} トークン</span>
            </div>
          )}
          {promptTokens !== undefined && promptTokens > 0 && (
            <div className="flex justify-between">
              <span>システムプロンプト:</span>
              <span>{promptTokens.toLocaleString()} トークン</span>
            </div>
          )}
        </div>
      )}

      {isWarning && (
        <p className="text-xs text-orange-600 mt-2 flex items-center gap-1">
          <AlertTriangle className="w-4 h-4 inline shrink-0" />
          トークン数が多いため、処理に時間がかかったり、エラーになる可能性があります。
        </p>
      )}
      <p className="text-xs text-gray-400 mt-2">
        日本語: 約1.5文字/トークン、英数字:
        約4文字/トークンで算出しています。
      </p>
      <p className="text-xs text-gray-400">
        トークン数がAIの入力上限を超えると、エラーになる可能性があります。
      </p>
    </div>
  )
}
