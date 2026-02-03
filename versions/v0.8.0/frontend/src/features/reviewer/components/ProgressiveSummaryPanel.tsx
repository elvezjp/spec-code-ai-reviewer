import { useState, useEffect, useRef } from 'react'
import {
  Sparkles,
  ChevronDown,
  ChevronRight,
  Play,
  Square,
  Circle,
  CheckCircle,
  Loader2,
  XCircle,
} from 'lucide-react'
import type { DesignFile, CodeFile, LlmConfig, ChunkWithStatus } from '../types'
import { useProgressiveSummary } from '../hooks/useProgressiveSummary'

interface ProgressiveSummaryPanelProps {
  type: 'spec' | 'code'
  markdown: string | null
  files: DesignFile[] | CodeFile[]
  llmConfig?: LlmConfig
  onAdopt: (summary: string) => void
}

// ChunkList sub-component
function ChunkList({
  chunks,
  currentIndex,
}: {
  chunks: ChunkWithStatus[]
  currentIndex: number
}) {
  const getStatusIcon = (chunk: ChunkWithStatus) => {
    switch (chunk.status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'processing':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />
      default:
        return <Circle className="w-4 h-4 text-gray-300" />
    }
  }

  return (
    <div className="space-y-1 max-h-48 overflow-y-auto">
      {chunks.map((chunk, index) => (
        <div
          key={chunk.id}
          className={`flex items-center gap-2 text-xs p-1 rounded ${
            index === currentIndex ? 'bg-blue-50' : ''
          }`}
        >
          {getStatusIcon(chunk)}
          <span className="flex-1 truncate">
            {index + 1}. {chunk.title}
          </span>
          <span className="text-gray-400 whitespace-nowrap">
            (約 {chunk.tokenCount.toLocaleString()} トークン)
          </span>
        </div>
      ))}
    </div>
  )
}

// SummaryPreview sub-component
function SummaryPreview({ summary, title }: { summary: string; title: string }) {
  if (!summary) return null

  return (
    <div>
      <h4 className="text-xs font-medium text-gray-600 mb-1">{title}</h4>
      <div className="border border-gray-200 rounded-md p-3 max-h-64 overflow-y-auto bg-gray-50">
        <pre className="text-xs whitespace-pre-wrap font-mono">{summary}</pre>
      </div>
    </div>
  )
}

export function ProgressiveSummaryPanel({
  type,
  markdown,
  files,
  llmConfig,
  onAdopt,
}: ProgressiveSummaryPanelProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isStopping, setIsStopping] = useState(false)
  const prevMarkdownRef = useRef<string | null>(markdown)

  const {
    state,
    policy,
    setPolicy,
    splitMarkdown,
    startSummarization,
    stopSummarization,
    reset,
    defaultSpecPolicy,
    defaultCodePolicy,
  } = useProgressiveSummary()

  // Auto-split when markdown changes
  useEffect(() => {
    const prevMarkdown = prevMarkdownRef.current
    prevMarkdownRef.current = markdown

    if (markdown && markdown !== prevMarkdown) {
      const filenames = files.map((f) => f.filename)
      splitMarkdown(type, markdown, filenames)

      // Auto-open panel when markdown becomes available
      if (!prevMarkdown) {
        setIsOpen(true)
      }
    } else if (!markdown && prevMarkdown) {
      reset()
    }
  }, [markdown, type, files, splitMarkdown, reset])

  // Update default policy when type changes
  useEffect(() => {
    setPolicy(type === 'spec' ? defaultSpecPolicy : defaultCodePolicy)
  }, [type, setPolicy, defaultSpecPolicy, defaultCodePolicy])

  // Reset isStopping when status changes from summarizing
  useEffect(() => {
    if (state.status !== 'summarizing') {
      setIsStopping(false)
    }
  }, [state.status])

  const handleStart = () => {
    setIsStopping(false)
    startSummarization(llmConfig)
  }
  const handleStop = () => {
    setIsStopping(true)
    stopSummarization()
  }
  const handleResume = () => {
    setIsStopping(false)
    startSummarization(llmConfig)
  }

  const handleAdopt = () => {
    if (state.currentSummary) {
      onAdopt(state.currentSummary)
      setIsOpen(false)
    }
  }

  const handleDownload = () => {
    if (!state.currentSummary) return
    const blob = new Blob([state.currentSummary], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `summary-${type}-${new Date().toISOString().slice(0, 10)}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleDiscard = () => {
    reset()
    if (markdown) {
      const filenames = files.map((f) => f.filename)
      splitMarkdown(type, markdown, filenames)
    }
  }

  const typeLabel = type === 'spec' ? '設計書' : 'コード'
  const completedCount = state.chunks.filter((c) => c.status === 'completed').length
  const totalCount = state.chunks.length

  const isSplitting = state.status === 'splitting'
  const isReady = state.status === 'ready'
  const isSummarizing = state.status === 'summarizing'
  const isStopped = state.status === 'stopped'
  const isCompleted = state.status === 'completed'
  const isError = state.status === 'error'

  const canStart = isReady || isStopped
  const canStop = isSummarizing
  const hasResult = state.currentSummary.length > 0
  const canAdopt = (isCompleted || isStopped) && hasResult

  return (
    <div className="mt-4 border-t border-gray-200 pt-3">
      <div className="flex items-center justify-between gap-2">
        <button
          onClick={() => setIsOpen((prev) => !prev)}
          disabled={!markdown}
          className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900 disabled:text-gray-400 disabled:cursor-not-allowed"
        >
          <Sparkles className="w-4 h-4" />
          AIで段階的に要約する
          {isOpen ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
        </button>
        {!markdown && (
          <span className="text-xs text-gray-400">
            ※ 先に{typeLabel}を選択して変換してください
          </span>
        )}
      </div>

      {isOpen && (
        <div className="mt-3 space-y-3">
          {/* Policy input */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              要約方針
            </label>
            <textarea
              value={policy}
              onChange={(e) => setPolicy(e.target.value)}
              rows={4}
              disabled={!markdown || isSummarizing}
              className="w-full text-xs border border-gray-300 rounded-md p-2 font-mono disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="要約方針を入力してください"
            />
          </div>

          {/* Action buttons and status */}
          <div className="flex items-center gap-2 flex-wrap">
            {canStart && (
              <button
                onClick={isStopped ? handleResume : handleStart}
                disabled={!markdown || !policy.trim()}
                className="flex items-center gap-1 bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm transition disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                <Play className="w-4 h-4" />
                {isStopped ? '再開' : '要約を開始'}
              </button>
            )}
            {canStop && (
              <>
                <button
                  onClick={handleStop}
                  disabled={isStopping}
                  className="flex items-center gap-1 bg-highlight hover:brightness-95 text-black px-3 py-1 rounded text-sm transition disabled:bg-gray-400 disabled:text-gray-600 disabled:cursor-not-allowed"
                >
                  <Square className="w-4 h-4" />
                  停止
                </button>
                {isStopping && (
                  <span className="text-xs text-orange-600 flex items-center gap-1">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    応答を待っています。現在の要約処理が終了したら停止します。
                  </span>
                )}
              </>
            )}
            {isSplitting && (
              <span className="text-xs text-gray-500 flex items-center gap-1">
                <Loader2 className="w-4 h-4 animate-spin" />
                チャンク分割中...
              </span>
            )}
            {isSummarizing && (
              <span className="text-xs text-gray-500">
                処理中... ({completedCount}/{totalCount}){' '}
                {state.chunks[state.currentIndex]?.title || ''}
              </span>
            )}
            {isReady && (
              <span className="text-xs text-gray-500">
                合計: 約 {state.totalTokenCount.toLocaleString()} トークン
              </span>
            )}
            {isCompleted && (
              <span className="text-xs text-green-600 flex items-center gap-1">
                <CheckCircle className="w-4 h-4" />
                要約完了 ({completedCount}/{totalCount})
              </span>
            )}
            {isStopped && (
              <span className="text-xs text-orange-600">
                処理を中断しました ({completedCount}/{totalCount})
              </span>
            )}
            {isError && (
              <span className="text-xs text-red-600">
                エラー: {state.error}
              </span>
            )}
          </div>

          {/* Info note */}
          {isReady && (
            <p className="text-xs text-gray-400">
              ※ チャンクごとに繰り返し要約を実行します。
              途中経過サマリーの入力トークン数は段階的に大きくなります。
            </p>
          )}

          {/* Chunk list */}
          {state.chunks.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-gray-600 mb-1">
                チャンク一覧（{totalCount}件）:
              </h4>
              <ChunkList chunks={state.chunks} currentIndex={state.currentIndex} />
            </div>
          )}

          {/* Summary preview */}
          {hasResult && (
            <SummaryPreview
              summary={state.currentSummary}
              title={isCompleted ? 'サマリー結果:' : '現在のサマリー（途中結果）:'}
            />
          )}

          {/* Result action buttons */}
          {hasResult && (
            <div className="flex items-center gap-2">
              <button
                onClick={handleAdopt}
                disabled={!canAdopt}
                className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm transition disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                採用してレビュー入力に反映
              </button>
              <button
                onClick={handleDownload}
                className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-3 py-1 rounded text-sm transition"
              >
                サマリーをダウンロード
              </button>
              <button
                onClick={handleDiscard}
                className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-3 py-1 rounded text-sm transition"
              >
                破棄
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
