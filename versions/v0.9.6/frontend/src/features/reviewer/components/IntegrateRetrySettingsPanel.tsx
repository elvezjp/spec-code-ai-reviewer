import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { estimateTokens } from '../utils/tokenEstimate'
import { executeSummarize } from '../services/api'
import type { GroupReviewState, IntegrateSummarizeState, IntegrateGroupSummarizeEntry, LlmConfig } from '../types'

interface IntegrateRetrySettingsPanelProps {
  groupReviews: GroupReviewState[]
  summarizeState: IntegrateSummarizeState
  llmConfig?: LlmConfig
  onSummarizeComplete: (state: IntegrateSummarizeState) => void
  onModeChange?: (hasPending: boolean) => void
}

export function IntegrateRetrySettingsPanel({
  groupReviews,
  summarizeState,
  llmConfig,
  onSummarizeComplete,
  onModeChange,
}: IntegrateRetrySettingsPanelProps) {
  const completedGroups = groupReviews.filter((g) => g.status === 'completed' && g.result)

  const [groupModes, setGroupModes] = useState<Record<string, 'original' | 'summarize'>>(() => {
    const initial: Record<string, 'original' | 'summarize'> = {}
    for (const g of completedGroups) {
      const entry = summarizeState.groups.find((s) => s.groupId === g.groupId)
      initial[g.groupId] = entry?.mode || 'original'
    }
    return initial
  })

  const [summarizingGroupIds, setSummarizingGroupIds] = useState<Set<string>>(new Set())
  const [previewOpen, setPreviewOpen] = useState<Record<string, boolean>>({})
  const [summarizeError, setSummarizeError] = useState<string | null>(null)

  const getEntry = (groupId: string): IntegrateGroupSummarizeEntry | undefined =>
    summarizeState.groups.find((s) => s.groupId === groupId)

  const computeHasPending = (modes: Record<string, 'original' | 'summarize'>) =>
    completedGroups.some(
      (g) => modes[g.groupId] === 'summarize' && !getEntry(g.groupId)?.summarizedReport
    )

  const hasPendingSummarize = computeHasPending(groupModes)

  const isSummarizing = summarizingGroupIds.size > 0

  const handleExecuteSummarize = async () => {
    const targets = completedGroups.filter(
      (g) => groupModes[g.groupId] === 'summarize' && !getEntry(g.groupId)?.summarizedReport
    )

    if (targets.length === 0) return

    setSummarizeError(null)
    const updatedGroups = [...summarizeState.groups]

    for (const g of targets) {
      setSummarizingGroupIds(new Set([g.groupId]))

      try {
        const response = await executeSummarize({
          text: g.result!.report,
          targetType: 'review_result',
          llmConfig: llmConfig || undefined,
        })

        if (response.success && response.summarizedText) {
          const entry: IntegrateGroupSummarizeEntry = {
            groupId: g.groupId,
            mode: 'summarize',
            summarizedReport: response.summarizedText,
            originalTokens: response.originalTokens,
            summarizedTokens: response.summarizedTokens,
          }
          const existingIndex = updatedGroups.findIndex((s) => s.groupId === g.groupId)
          if (existingIndex >= 0) {
            updatedGroups[existingIndex] = entry
          } else {
            updatedGroups.push(entry)
          }
          onSummarizeComplete({ groups: [...updatedGroups] })
        } else {
          setSummarizeError(`「${g.groupName}」の要約に失敗しました: ${response.error || '不明なエラー'}`)
          break
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : '不明なエラー'
        setSummarizeError(`「${g.groupName}」の要約に失敗しました: ${message}`)
        break
      }
    }

    setSummarizingGroupIds(new Set())
  }

  const handleModeChange = (groupId: string, mode: 'original' | 'summarize') => {
    const newModes = { ...groupModes, [groupId]: mode }
    setGroupModes(newModes)
    onModeChange?.(computeHasPending(newModes))
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

      {/* 各グループの設定 */}
      <div className="flex flex-col items-center mb-3">
        <div className="inline-flex flex-col gap-2">
          {completedGroups.map((g) => {
            const entry = getEntry(g.groupId)
            const originalTokens = entry?.originalTokens ?? estimateTokens(g.result!.report)
            const mode = groupModes[g.groupId] || 'original'
            const isSummarizingThis = summarizingGroupIds.has(g.groupId)
            const isPreviewOpen = previewOpen[g.groupId] || false

            return (
              <div key={g.groupId}>
                <div className="flex items-center gap-4 text-xs">
                  <span className="font-medium text-gray-600 min-w-0">{g.groupName}</span>
                  <label className="flex items-center gap-1 cursor-pointer whitespace-nowrap">
                    <input
                      type="radio"
                      name={`integrate-mode-${g.groupId}`}
                      checked={mode === 'original'}
                      onChange={() => handleModeChange(g.groupId, 'original')}
                      className="text-blue-600"
                    />
                    そのまま（{formatTokens(originalTokens)}）
                  </label>
                  <label className="flex items-center gap-1 cursor-pointer whitespace-nowrap">
                    <input
                      type="radio"
                      name={`integrate-mode-${g.groupId}`}
                      checked={mode === 'summarize'}
                      onChange={() => handleModeChange(g.groupId, 'summarize')}
                      className="text-blue-600"
                    />
                    要約（{isSummarizingThis
                      ? '⟳ 要約中...'
                      : entry?.summarizedReport && entry?.summarizedTokens
                        ? formatReduction(originalTokens, entry.summarizedTokens)
                        : '未実行'}）
                  </label>
                </div>
                {mode === 'summarize' && entry?.summarizedReport && (
                  <div className="mt-1 ml-4">
                    <button
                      onClick={() => setPreviewOpen((prev) => ({ ...prev, [g.groupId]: !isPreviewOpen }))}
                      className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
                    >
                      {isPreviewOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                      要約結果を表示
                    </button>
                    {isPreviewOpen && (
                      <div className="mt-1 p-2 bg-gray-50 border rounded text-xs text-gray-700 whitespace-pre-wrap text-left max-h-[200px] overflow-y-auto">
                        {entry.summarizedReport}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
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
