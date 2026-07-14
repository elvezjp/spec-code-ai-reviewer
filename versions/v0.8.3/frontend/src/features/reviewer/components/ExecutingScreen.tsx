interface ExecutingScreenProps {
  currentExecution: number
  totalExecutions?: number
}

export function ExecutingScreen({
  currentExecution,
  totalExecutions = 2,
}: ExecutingScreenProps) {
  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-md p-12 text-center">
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
    </div>
  )
}
