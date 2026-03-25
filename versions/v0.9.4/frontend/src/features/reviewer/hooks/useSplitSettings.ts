import { useState, useCallback, useMemo, useRef } from 'react'
import type {
  SplitSettings,
  SplitPreviewResult,
  DocumentPart,
  CodePart,
  LlmConfig,
  HeadingInfo,
  PreImportantSplitSettings,
} from '../types'
import * as api from '../services/api'

const DEFAULT_PRE_IMPORTANT_SPLIT_SETTINGS: PreImportantSplitSettings = {
  splitMode: 'ai',
  headingLevel: 2,
  splitInstructions: '',
  maxSubsections: 5,
  summaryMode: 'ai',
  summaryMaxChars: 100,
}

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

  // 事前重要指定 State
  headings: HeadingInfo[]
  isLoadingHeadings: boolean
  headingsError: string | null
  preImportantSections: number[]
  preImportantSplitSettings: PreImportantSplitSettings
  normalSplitSettings: PreImportantSplitSettings
  preExcludedSections: number[]

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
  toggleExcludedDocPart: (partId: string) => void
  executeSummarize: (llmConfig?: LlmConfig | null) => Promise<void>
  fetchHeadingsForContent: (content: string) => Promise<void>
  togglePreImportantSection: (startLine: number) => void
  togglePreExcludedSection: (startLine: number) => void
  setPreImportantSplitSettings: (settings: PreImportantSplitSettings) => void
  setNormalSplitSettings: (settings: PreImportantSplitSettings) => void
  clearHeadingsCache: () => void

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

  // 事前重要指定 State
  const [headings, setHeadings] = useState<HeadingInfo[]>([])
  const [isLoadingHeadings, setIsLoadingHeadings] = useState(false)
  const [headingsError, setHeadingsError] = useState<string | null>(null)
  const [preImportantSections, setPreImportantSections] = useState<number[]>([])
  const [preExcludedSections, setPreExcludedSections] = useState<number[]>([])
  const [preImportantSplitSettings, setPreImportantSplitSettings] = useState<PreImportantSplitSettings>(
    { ...DEFAULT_PRE_IMPORTANT_SPLIT_SETTINGS, summaryMaxChars: 300 }
  )
  const [normalSplitSettings, setNormalSplitSettings] = useState<PreImportantSplitSettings>(
    { ...DEFAULT_PRE_IMPORTANT_SPLIT_SETTINGS }
  )
  // Cache tracking: store the markdown content hash that was used for the last heading fetch
  const headingsCacheContentRef = useRef<string | null>(null)

  const togglePinnedDocPart = useCallback((partId: string) => {
    setPinnedDocPartIds(prev =>
      prev.includes(partId)
        ? prev.filter(id => id !== partId)
        : [...prev, partId]
    )
  }, [])

  const toggleExcludedDocPart = useCallback((partId: string) => {
    setPreviewResult((prev) => {
      if (!prev || !prev.documentParts) return prev
      const target = prev.documentParts.find((p) => p.id === partId)
      if (!target) return prev
      const newExcluded = !target.excluded
      return {
        ...prev,
        documentParts: prev.documentParts.map((p) =>
          p.id === partId
            ? {
                ...p,
                excluded: newExcluded,
                // 除外ON時は「要約」を解除
                ...(newExcluded ? { summarizeMode: 'original' as const } : {}),
              }
            : p
        ),
      }
    })
    // 除外ON時は「重要」も解除（setPreviewResultと同期が取れないため現在値を直接参照できないが、
    // setPinnedDocPartIdsのコールバック内では除外方向のみ解除する）
    setPinnedDocPartIds((prev) => {
      if (!prev.includes(partId)) return prev
      return prev.filter((id) => id !== partId)
    })
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

  // 見出し一覧取得（キャッシュ対応）
  const fetchHeadingsForContent = useCallback(async (content: string) => {
    // キャッシュヒット: 同じコンテンツなら再取得しない
    if (headingsCacheContentRef.current === content && headings.length > 0) {
      return
    }

    setIsLoadingHeadings(true)
    setHeadingsError(null)
    try {
      const result = await api.fetchHeadings(content)
      if (result.success === false) {
        setHeadingsError(result.error || '見出し一覧の取得に失敗しました')
        setHeadings([])
      } else {
        setHeadings(result.headings || [])
        headingsCacheContentRef.current = content
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : '見出し一覧の取得に失敗しました'
      console.error('見出し一覧の取得に失敗しました:', err)
      setHeadingsError(message)
      setHeadings([])
    } finally {
      setIsLoadingHeadings(false)
    }
  }, [headings.length])

  // 見出しキャッシュのクリア（MD変更時に呼び出す）
  const clearHeadingsCache = useCallback(() => {
    headingsCacheContentRef.current = null
    setHeadings([])
    setHeadingsError(null)
    setPreImportantSections([])
    setPreExcludedSections([])
  }, [])

  // 事前重要指定セクションの切り替え
  const togglePreImportantSection = useCallback((startLine: number) => {
    setPreImportantSections(prev =>
      prev.includes(startLine)
        ? prev.filter(sl => sl !== startLine)
        : [...prev, startLine]
    )
    // 排他制御: 事前除外から除外
    setPreExcludedSections(prev => prev.filter(s => s !== startLine))
    // 事前重要指定が変更されたらプレビュー結果をクリア
    setPreviewResult(null)
    setPinnedDocPartIds([])
    setError(null)
  }, [])

  // 事前除外指定セクションの切り替え
  const togglePreExcludedSection = useCallback((startLine: number) => {
    setPreExcludedSections(prev =>
      prev.includes(startLine)
        ? prev.filter(s => s !== startLine)
        : [...prev, startLine]
    )
    // 排他制御: 事前重要から除外
    setPreImportantSections(prev => prev.filter(s => s !== startLine))
    setPreviewResult(null)
    setPinnedDocPartIds([])
    setError(null)
  }, [])

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
        // 事前重要指定セクションがある場合は新しいパラメータを使用
        const hasPreImportant = preImportantSections.length > 0

        const response = await api.splitMarkdown({
          content: designMarkdown,
          filename: designFilename,
          maxDepth: hasPreImportant ? normalSplitSettings.headingLevel : settings.documentMaxDepth,
          splitMode: hasPreImportant ? normalSplitSettings.splitMode : settings.documentSplitMode,
          llmConfig: (hasPreImportant ? normalSplitSettings.splitMode === 'ai' : settings.documentSplitMode === 'ai')
            ? (llmConfig ?? undefined) : undefined,
          aiPromptExtraNotes: hasPreImportant
            ? (normalSplitSettings.splitMode === 'ai' && normalSplitSettings.splitInstructions
              ? normalSplitSettings.splitInstructions
              : undefined)
            : (settings.documentSplitMode === 'ai' && settings.aiPromptExtraNotes
              ? settings.aiPromptExtraNotes
              : undefined),
          // 事前重要指定がない場合でも、通常セクション設定（UIの通常セクション）を反映する
          summaryMode: normalSplitSettings.summaryMode,
          summaryMaxChars: normalSplitSettings.summaryMaxChars,
          maxSubsections: normalSplitSettings.maxSubsections,
          ...(hasPreImportant ? {
            preImportantSections,
            preImportantSplitSettings: {
              splitMode: preImportantSplitSettings.splitMode,
              headingLevel: preImportantSplitSettings.headingLevel,
              splitInstructions: preImportantSplitSettings.splitInstructions,
              maxSubsections: preImportantSplitSettings.maxSubsections,
              summaryMode: preImportantSplitSettings.summaryMode,
              summaryMaxChars: preImportantSplitSettings.summaryMaxChars,
            },
            normalSplitSettings: {
              splitMode: normalSplitSettings.splitMode,
              headingLevel: normalSplitSettings.headingLevel,
              splitInstructions: normalSplitSettings.splitInstructions,
              maxSubsections: normalSplitSettings.maxSubsections,
              summaryMode: normalSplitSettings.summaryMode,
              summaryMaxChars: normalSplitSettings.summaryMaxChars,
            },
          } : {}),
          ...(preExcludedSections.length > 0 ? { preExcludedSections } : {}),
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

      // 事前重要指定セクションのうち、サブスプリットされていないパートを自動的に重要=ONにする
      const autoPinnedIds: string[] = []
      if (documentParts && preImportantSections.length > 0) {
        for (const part of documentParts) {
          if (part.preImportant && !part.displayName.includes(': part-')) {
            autoPinnedIds.push(part.id)
          }
        }
      }

      setPreviewResult({
        documentParts: documentParts?.map((p) => ({ ...p, summarizeMode: 'original' as const, excluded: false })) || null,
        codeParts,
        documentIndex,
        documentMapJson,
        codeIndex,
        codeMapJson,
        codeLanguage,
        pinnedDocPartIds: autoPinnedIds,
        codeWarnings: allCodeWarnings,
      })
      setPinnedDocPartIds(autoPinnedIds)
    } catch (err) {
      const message = err instanceof Error ? err.message : '分割プレビューに失敗しました'
      setError(message)
      setPreviewResult(null)
    } finally {
      setIsExecutingPreview(false)
    }
  }, [settings.reviewMode, settings.documentMaxDepth, settings.documentSplitMode, settings.aiPromptExtraNotes, preImportantSections, preImportantSplitSettings, normalSplitSettings, preExcludedSections])

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
    headings,
    isLoadingHeadings,
    headingsError,
    preImportantSections,
    preImportantSplitSettings,
    normalSplitSettings,
    preExcludedSections,
    setSettings: handleSetSettings,
    executePreview,
    clearPreview,
    clearError,
    togglePinnedDocPart,
    toggleSummarizeMode,
    toggleExcludedDocPart,
    executeSummarize,
    fetchHeadingsForContent,
    togglePreImportantSection,
    togglePreExcludedSection,
    setPreImportantSplitSettings,
    setNormalSplitSettings,
    clearHeadingsCache,
    isSplitEnabled,
    reviewMode,
    estimatedReviewCount,
    hasPendingSummarize,
  }
}
