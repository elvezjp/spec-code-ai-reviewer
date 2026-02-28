import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { estimateTokens } from '../utils/tokenEstimate'
import { executeSummarize } from '../services/api'
import type { GroupSummarizeState, LlmConfig } from '../types'

interface RetrySettingsPanelProps {
  groupId: string
  documentContent: string
  codeContent: string
  summarizeState?: GroupSummarizeState
  llmConfig?: LlmConfig
  onSummarizeComplete: (groupId: string, state: GroupSummarizeState) => void
  onModeChange?: (docMode: 'original' | 'summarize', codeMode: 'original' | 'summarize') => void
}

function SummarizedTextPreview({ label, text }: { label: string; text: string }) {
  const [isOpen, setIsOpen] = useState(false)
  return (
    <div className="mt-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
      >
        {isOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        {label}
      </button>
      {isOpen && (
        <div className="mt-1 p-2 bg-gray-50 border rounded text-xs text-gray-700 whitespace-pre-wrap max-h-[200px] overflow-y-auto">
          {text}
        </div>
      )}
    </div>
  )
}

export function RetrySettingsPanel({
  groupId,
  documentContent,
  codeContent,
  summarizeState,
  llmConfig,
  onSummarizeComplete,
  onModeChange,
}: RetrySettingsPanelProps) {
  const [docMode, setDocMode] = useState<'original' | 'summarize'>('original')
  const [codeMode, setCodeMode] = useState<'original' | 'summarize'>('original')
  const [docSummarizing, setDocSummarizing] = useState(false)
  const [codeSummarizing, setCodeSummarizing] = useState(false)
  const [summarizeError, setSummarizeError] = useState<string | null>(null)

  const docOriginalTokens = summarizeState?.documentOriginalTokens ?? estimateTokens(documentContent)
  const codeOriginalTokens = summarizeState?.codeOriginalTokens ?? estimateTokens(codeContent)

  const docSummarized = summarizeState?.documentSummarized
  const codeSummarized = summarizeState?.codeSummarized
  const docSummarizedTokens = summarizeState?.documentSummarizedTokens
  const codeSummarizedTokens = summarizeState?.codeSummarizedTokens

  const hasPendingSummarize =
    (docMode === 'summarize' && !docSummarized) ||
    (codeMode === 'summarize' && !codeSummarized)

  const isSummarizing = docSummarizing || codeSummarizing

  const handleExecuteSummarize = async () => {
    const newState: GroupSummarizeState = { ...summarizeState }
    setSummarizeError(null)

    const targets: Array<{ type: 'design' | 'code'; text: string }> = []
    if (docMode === 'summarize' && !docSummarized) {
      targets.push({ type: 'design', text: documentContent })
    }
    if (codeMode === 'summarize' && !codeSummarized) {
      targets.push({ type: 'code', text: codeContent })
    }

    if (targets.length === 0) return

    for (const t of targets) {
      if (t.type === 'design') setDocSummarizing(true)
      else setCodeSummarizing(true)

      try {
        const response = await executeSummarize({
          text: t.text,
          targetType: t.type,
          llmConfig: llmConfig || undefined,
        })

        if (response.success && response.summarizedText) {
          if (t.type === 'design') {
            newState.documentSummarized = response.summarizedText
            newState.documentOriginalTokens = response.originalTokens
            newState.documentSummarizedTokens = response.summarizedTokens
          } else {
            newState.codeSummarized = response.summarizedText
            newState.codeOriginalTokens = response.originalTokens
            newState.codeSummarizedTokens = response.summarizedTokens
          }
          onSummarizeComplete(groupId, { ...newState })
        } else {
          const label = t.type === 'design' ? '設計書' : 'プログラム'
          setSummarizeError(`${label}の要約に失敗しました: ${response.error || '不明なエラー'}`)
          break
        }
      } catch (err) {
        const label = t.type === 'design' ? '設計書' : 'プログラム'
        const message = err instanceof Error ? err.message : '不明なエラー'
        setSummarizeError(`${label}の要約に失敗しました: ${message}`)
        break
      } finally {
        if (t.type === 'design') setDocSummarizing(false)
        else setCodeSummarizing(false)
      }
    }
  }

  const formatTokens = (tokens: number) => `~${tokens.toLocaleString()} トークン`

  const formatReduction = (original: number, summarized: number) => {
    const reduction = Math.round((1 - summarized / original) * 100)
    return `${formatTokens(summarized)} ${reduction}%削減`
  }

  return (
    <div className="mt-3 p-3 bg-gray-50 border rounded-md">
      <p className="text-sm font-medium text-gray-700 mb-2 text-center">リトライ設定</p>

      {/* 注意文 */}
      <div className="p-2 bg-amber-50 border border-amber-200 rounded-md mb-3">
        <p className="text-xs text-amber-800">
          <span className="font-medium">⚠ 注意:</span>{' '}
          要約によって微妙なニュアンスや制約が失われることがあるため、品質検証が必要です。
        </p>
      </div>

      {/* 設計書 */}
      <div className="mb-3">
        <p className="text-xs font-medium text-gray-600 mb-1 text-center">設計書</p>
        <div className="flex items-center justify-center gap-4 text-xs">
          <label className="flex items-center gap-1 cursor-pointer">
            <input
              type="radio"
              name={`doc-mode-${groupId}`}
              checked={docMode === 'original'}
              onChange={() => { setDocMode('original'); onModeChange?.('original', codeMode) }}
              className="text-blue-600"
            />
            そのまま（{formatTokens(docOriginalTokens)}）
          </label>
          <label className="flex items-center gap-1 cursor-pointer">
            <input
              type="radio"
              name={`doc-mode-${groupId}`}
              checked={docMode === 'summarize'}
              onChange={() => { setDocMode('summarize'); onModeChange?.('summarize', codeMode) }}
              className="text-blue-600"
            />
            要約（{docSummarizing
              ? '⟳ 要約中...'
              : docSummarized && docSummarizedTokens
                ? formatReduction(docOriginalTokens, docSummarizedTokens)
                : '未実行'}）
          </label>
        </div>
        {docMode === 'summarize' && docSummarized && (
          <SummarizedTextPreview label="要約結果を表示" text={docSummarized} />
        )}
      </div>

      {/* プログラム */}
      <div className="mb-3">
        <p className="text-xs font-medium text-gray-600 mb-1 text-center">プログラム</p>
        <div className="flex items-center justify-center gap-4 text-xs">
          <label className="flex items-center gap-1 cursor-pointer">
            <input
              type="radio"
              name={`code-mode-${groupId}`}
              checked={codeMode === 'original'}
              onChange={() => { setCodeMode('original'); onModeChange?.(docMode, 'original') }}
              className="text-blue-600"
            />
            そのまま（{formatTokens(codeOriginalTokens)}）
          </label>
          <label className="flex items-center gap-1 cursor-pointer">
            <input
              type="radio"
              name={`code-mode-${groupId}`}
              checked={codeMode === 'summarize'}
              onChange={() => { setCodeMode('summarize'); onModeChange?.(docMode, 'summarize') }}
              className="text-blue-600"
            />
            要約（{codeSummarizing
              ? '⟳ 要約中...'
              : codeSummarized && codeSummarizedTokens
                ? formatReduction(codeOriginalTokens, codeSummarizedTokens)
                : '未実行'}）
          </label>
        </div>
        {codeMode === 'summarize' && codeSummarized && (
          <SummarizedTextPreview label="要約結果を表示" text={codeSummarized} />
        )}
      </div>

      {/* 選択した要約を実行ボタン */}
      {hasPendingSummarize && (
        <div className="text-center">
          <button
            onClick={handleExecuteSummarize}
            disabled={isSummarizing}
            className="px-3 py-1.5 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white text-xs rounded-md transition"
          >
            {isSummarizing ? '要約実行中...' : '選択した要約を実行'}
          </button>
        </div>
      )}

      {/* 要約実行エラー */}
      {summarizeError && (
        <p className="text-xs text-red-600 mt-2 text-center">{summarizeError}</p>
      )}
    </div>
  )
}

export { SummarizedTextPreview }
