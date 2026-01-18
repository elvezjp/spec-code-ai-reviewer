import { AlertTriangle } from 'lucide-react'

interface TokenEstimatorProps {
  totalTokens: number
  isWarning: boolean
  isVisible?: boolean
}

export function TokenEstimator({
  totalTokens,
  isWarning,
  isVisible = true,
}: TokenEstimatorProps) {
  if (!isVisible) return null

  return (
    <div className="bg-white rounded-lg shadow-md p-4 mb-6">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">
          推定入力トークン数
        </span>
        <span
          className={`text-sm font-bold ${
            isWarning ? 'text-orange-600' : 'text-gray-800'
          }`}
        >
          {totalTokens.toLocaleString()} トークン
        </span>
      </div>
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
