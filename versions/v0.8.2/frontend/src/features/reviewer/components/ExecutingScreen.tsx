import { RotateCcw } from 'lucide-react'
import { Card } from '@core/index'

interface ExecutingScreenProps {
  currentExecution: number
  totalExecutions?: number
  onBack: () => void
  error?: string
  onRetry?: () => void
}

export function ExecutingScreen({
  currentExecution,
  totalExecutions = 2,
  onBack,
  error,
  onRetry,
}: ExecutingScreenProps) {
  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <Card>
        <div className="flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-800">レビュー実行中</h1>
          <button onClick={onBack} className="text-blue-500 hover:text-blue-700">
            ← 戻る
          </button>
        </div>
      </Card>

      <Card>
        {error ? (
          <div className="text-center">
            {/* エラー内容 */}
            <div className="p-3 bg-red-50 border border-red-200 rounded-md text-left">
              <p className="text-sm font-medium text-red-800">
                レビュー実行中にエラーが発生しました。
              </p>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>

            {/* リトライボタン */}
            {onRetry && (
              <div className="flex items-center justify-center gap-3 mt-4">
                <button
                  onClick={onRetry}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded-md transition"
                >
                  <RotateCcw className="w-4 h-4" />
                  リトライ
                </button>
              </div>
            )}

            <p className="text-sm text-gray-600 mt-4">
              トークン上限の場合や同じエラーが繰り返される場合は、分割設定でのレビューをお試しください。
            </p>
          </div>
        ) : (
          <div className="py-6 text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-500 mx-auto mb-6"></div>
            <p className="text-gray-600 text-lg">AIがレビューを実行中...</p>
            <p className="text-gray-400 mt-2">
              {currentExecution}回目のレビューを実行しています
              {totalExecutions > 1 && ` (${currentExecution}/${totalExecutions})`}
            </p>
            <p className="text-gray-400 text-xs mt-4">
              ※ 5分以上かかる場合はタイムアウトする可能性があります
            </p>
          </div>
        )}
      </Card>
    </div>
  )
}
