import { useState, useCallback, useMemo } from 'react'
import type {
  SplitSettings,
  SplitPreviewResult,
  DocumentPart,
  CodePart,
  LlmConfig,
} from '../types'
import * as api from '../services/api'

interface UseSplitSettingsReturn {
  // State
  settings: SplitSettings
  previewResult: SplitPreviewResult | null
  isExecutingPreview: boolean
  error: string | null
  pinnedDocPartIds: string[]
  isSummarizing: boolean
  summarizingPartIds: Set<string>
  summarizeError: string | null

  // Actions
  setSettings: (settings: SplitSettings) => void
  executePreview: (
    designMarkdown: string | null,
    designFilename: string,
    codeFiles: Array<{ filename: string; content: string }>,
    llmConfig?: LlmConfig | null,
  ) => Promise<void>
  clearPreview: () => void
  clearError: () => void
  togglePinnedDocPart: (partId: string) => void
  toggleSummarizeMode: (partId: string) => void
  executeSummarize: (llmConfig?: LlmConfig | null) => Promise<void>

  // Computed
  isSplitEnabled: boolean
  reviewMode: 'batch' | 'split'
  estimatedReviewCount: number
  hasPendingSummarize: boolean
}

const DEFAULT_SETTINGS: SplitSettings = {
  reviewMode: 'batch',
  documentMaxDepth: 2,
  documentSplitMode: 'ai',
  aiPromptExtraNotes: '',
}

export function useSplitSettings(): UseSplitSettingsReturn {
  const [settings, setSettings] = useState<SplitSettings>(DEFAULT_SETTINGS)
  const [previewResult, setPreviewResult] = useState<SplitPreviewResult | null>(null)
  const [isExecutingPreview, setIsExecutingPreview] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pinnedDocPartIds, setPinnedDocPartIds] = useState<string[]>([])
  const [isSummarizing, setIsSummarizing] = useState(false)
  const [summarizingPartIds, setSummarizingPartIds] = useState<Set<string>>(new Set())
  const [summarizeError, setSummarizeError] = useState<string | null>(null)

  const togglePinnedDocPart = useCallback((partId: string) => {
    setPinnedDocPartIds(prev =>
      prev.includes(partId)
        ? prev.filter(id => id !== partId)
        : [...prev, partId]
    )
  }, [])

  const toggleSummarizeMode = useCallback((partId: string) => {
    setPreviewResult((prev) => {
      if (!prev || !prev.documentParts) return prev
      return {
        ...prev,
        documentParts: prev.documentParts.map((p) =>
          p.id === partId
            ? {
                ...p,
                // summarizeMode のみ切替。summarizedContent / summarizedTokens は保持
                summarizeMode: p.summarizeMode === 'summarize' ? 'original' as const : 'summarize' as const,
              }
            : p
        ),
      }
    })
  }, [])

  const executeSummarize = useCallback(async (llmConfig?: LlmConfig | null) => {
    if (!previewResult?.documentParts) return

    const targets = previewResult.documentParts.filter(
      (p) => p.summarizeMode === 'summarize' && !p.summarizedContent
    )
    if (targets.length === 0) return

    setIsSummarizing(true)
    setSummarizeError(null)

    for (const part of targets) {
      setSummarizingPartIds(new Set([part.id]))

      try {
        const response = await api.executeSummarize({
          text: part.content,
          targetType: 'design',
          llmConfig: llmConfig || undefined,
        })

        if (response.success) {
          setPreviewResult((prev) => {
            if (!prev || !prev.documentParts) return prev
            return {
              ...prev,
              documentParts: prev.documentParts.map((p) =>
                p.id === part.id
                  ? {
                      ...p,
                      summarizedContent: response.summarizedText || undefined,
                      summarizedTokens: response.summarizedTokens || undefined,
                    }
                  : p
              ),
            }
          })
        } else {
          setSummarizeError(`「${part.displayName}」の要約に失敗しました: ${response.error || '不明なエラー'}`)
          break
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : '不明なエラー'
        setSummarizeError(`「${part.displayName}」の要約に失敗しました: ${message}`)
        break
      }
    }

    setSummarizingPartIds(new Set())
    setIsSummarizing(false)
  }, [previewResult])

  const executePreview = useCallback(async (
    designMarkdown: string | null,
    designFilename: string,
    codeFiles: Array<{ filename: string; content: string }>,
    llmConfig?: LlmConfig | null,
  ) => {
    setIsExecutingPreview(true)
    setError(null)

    try {
      if (settings.reviewMode === 'split') {
        if (!designMarkdown) {
          throw new Error('分割レビューには設計書が必要です')
        }
        if (codeFiles.length === 0) {
          throw new Error('分割レビューにはプログラムが必要です')
        }
      }

      let documentParts: DocumentPart[] | null = null
      let documentIndex: string | null = null
      let documentMapJson: Record<string, unknown>[] | null = null
      let codeParts: CodePart[] | null = null
      let codeIndex: string | null = null
      let codeMapJson: Record<string, unknown>[] | null = null
      let codeLanguage: string | null = null

      // 設計書分割
      if (settings.reviewMode === 'split' && designMarkdown) {
        const response = await api.splitMarkdown({
          content: designMarkdown,
          filename: designFilename,
          maxDepth: settings.documentMaxDepth,
          splitMode: settings.documentSplitMode,
          llmConfig: settings.documentSplitMode === 'ai' ? (llmConfig ?? undefined) : undefined,
          aiPromptExtraNotes: settings.documentSplitMode === 'ai' && settings.aiPromptExtraNotes
            ? settings.aiPromptExtraNotes
            : undefined,
        })

        if (response.success) {
          documentParts = response.parts
          documentIndex = response.indexContent || null
          documentMapJson = response.mapJson || null
        } else {
          throw new Error(response.error || '設計書の分割に失敗しました')
        }
      }

      // コード分割（対応言語のファイルのみ）
      const allCodeWarnings: string[] = []
      if (settings.reviewMode === 'split' && codeFiles.length > 0) {
        const allCodeParts: CodePart[] = []
        const allIndexContents: string[] = []
        const allMapJsonEntries: Record<string, unknown>[] = []
        const unsupportedFiles: string[] = []

        for (const codeFile of codeFiles) {
          const ext = codeFile.filename.toLowerCase().split('.').pop()
          if (ext !== 'py' && ext !== 'java') {
            unsupportedFiles.push(codeFile.filename)
            continue // 未対応言語はスキップ
          }

          const response = await api.splitCode({
            content: codeFile.content,
            filename: codeFile.filename,
          })

          if (response.success) {
            allCodeParts.push(...response.parts)
            if (response.indexContent) {
              allIndexContents.push(response.indexContent)
            }
            if (response.mapJson) {
              allMapJsonEntries.push(...response.mapJson)
            }
            if (response.language && !codeLanguage) {
              codeLanguage = response.language
            }
            if (response.warnings && response.warnings.length > 0) {
              allCodeWarnings.push(...response.warnings.map(w => `${codeFile.filename}: ${w}`))
            }
          } else {
            if (response.warnings && response.warnings.length > 0) {
              allCodeWarnings.push(...response.warnings.map(w => `${codeFile.filename}: ${w}`))
            }
            if (response.error) {
              allCodeWarnings.push(`${codeFile.filename}: ${response.error}`)
            }
          }
        }

        if (unsupportedFiles.length > 0) {
          throw new Error(
            `未対応言語が含まれるため分割できません: ${unsupportedFiles.join(', ')}`
          )
        }

        if (allCodeParts.length > 0) {
          codeParts = allCodeParts
          codeIndex = allIndexContents.join('\n\n---\n\n')
          codeMapJson = allMapJsonEntries.length > 0 ? allMapJsonEntries : null
        }
      }

      setPreviewResult({
        documentParts: documentParts?.map((p) => ({ ...p, summarizeMode: 'original' as const })) || null,
        codeParts,
        documentIndex,
        documentMapJson,
        codeIndex,
        codeMapJson,
        codeLanguage,
        pinnedDocPartIds: [],
        codeWarnings: allCodeWarnings,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : '分割プレビューに失敗しました'
      setError(message)
      setPreviewResult(null)
    } finally {
      setIsExecutingPreview(false)
    }
  }, [settings.reviewMode, settings.documentMaxDepth, settings.documentSplitMode])

  const clearPreview = useCallback(() => {
    setPreviewResult(null)
    setPinnedDocPartIds([])
    setError(null)
  }, [])

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  const handleSetSettings = useCallback((newSettings: SplitSettings) => {
    setSettings(newSettings)
    // 設定が変更されたらプレビュー結果をクリア
    setPreviewResult(null)
    setPinnedDocPartIds([])
    setError(null)
  }, [])

  // Computed values
  const isSplitEnabled = settings.reviewMode === 'split'

  const hasPendingSummarize = useMemo(() => {
    if (!previewResult?.documentParts) return false
    return previewResult.documentParts.some(
      (p) => p.summarizeMode === 'summarize' && !p.summarizedContent
    )
  }, [previewResult])

  const reviewMode = settings.reviewMode

  // レビュー回数の推定
  const estimatedReviewCount = (() => {
    if (!previewResult) return 1

    const docCount = previewResult.documentParts?.length || 0
    const codeCount = previewResult.codeParts?.length || 0

    switch (reviewMode) {
      case 'split':
        // フェーズ1: 構造マッチング 1回
        // フェーズ2: ペアレビュー（最大 docCount + codeCount、実際は関連ペアのみ）
        return 1 + docCount + codeCount
      default:
        return 1
    }
  })()

  return {
    settings,
    previewResult,
    isExecutingPreview,
    error,
    pinnedDocPartIds,
    isSummarizing,
    summarizingPartIds,
    summarizeError,
    setSettings: handleSetSettings,
    executePreview,
    clearPreview,
    clearError,
    togglePinnedDocPart,
    toggleSummarizeMode,
    executeSummarize,
    isSplitEnabled,
    reviewMode,
    estimatedReviewCount,
    hasPendingSummarize,
  }
}
