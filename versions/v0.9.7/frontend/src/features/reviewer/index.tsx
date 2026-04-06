import { useEffect, useMemo, useCallback, useState, useRef } from 'react'
import { Settings, FileText, BookOpen, AlertTriangle, X } from 'lucide-react'
import { Link } from 'react-router-dom'
import {
  Layout,
  Header,
  Card,
  Button,
  FileInputButton,
  SettingsModal,
  TokenEstimator,
  SystemPromptEditor,
  VersionSelector,
  ScreenContainer,
  useModal,
  useScreenManager,
  useTokenEstimation,
  useVersions,
} from '@core/index'
import type { ScreenState } from '@core/types'
import {
  SpecTypesSection,
  SpecFileList,
  CodeFileList,
  ReviewResult,
  ExecutingScreen,
  SplitExecutingScreen,
  MarkdownOrganizer,
  SplitSettingsSection,
} from './components'
import { useFileConversion, useReviewExecution, useReviewerSettings, useZipExport, useSplitSettings } from './hooks'
import { testLlmConnection, executeStructureMatching, executeGroupReview, executeIntegrate, fetchHealth } from './services/api'
import type { SplitReviewState, GroupReviewState, GroupSummarizeState, IntegrateSummarizeState, ReviewExecutionData } from './types'

const APP_INFO = {
  name: 'spec-code-ai-reviewer',
  version: 'v0.9.6',
  description: '設計書-Javaプログラム突合 AIレビュアー',
  copyright: '© 株式会社エルブズ',
  url: 'https://elvez.co.jp',
}

export function Reviewer() {
  const settingsModal = useModal()
  const screenManager = useScreenManager()
  const { versions, currentVersion, switchVersion } = useVersions()
  const [toastMessage, setToastMessage] = useState('')
  const toastTimerRef = useRef<number | null>(null)
  const [versionMismatch, setVersionMismatch] = useState<{ frontend: string; backend: string } | null>(null)

  // File conversion
  const {
    specFiles,
    specMarkdown,
    isSpecConverting,
    specStatus,
    addSpecFiles,
    setMainSpec,
    setSpecType,
    setSpecTool,
    applyToolToAll,
    convertSpecs,
    applyOrganizedMarkdown,
    codeFiles,
    codeWithLineNumbers,
    isCodeConverting,
    codeStatus,
    addCodeFiles,
    convertCodes,
    availableTools,
    loadTools,
  } = useFileConversion()

  // Settings
  const {
    llmConfig,
    selectedModel,
    setSelectedModel,
    specTypesConfig,
    getTypeNote,
    getSpecTypesList,
    systemPromptPresets,
    selectedPreset,
    currentPromptValues,
    selectPreset,
    updatePromptValue,
    reviewerConfig,
    configFilename,
    configModified,
    configLoadStatus,
    loadConfigFile,
    saveConfigToBrowser,
    clearSavedConfig,
    hasSavedConfig,
  } = useReviewerSettings()

  // Review execution
  const {
    reviewResults,
    currentExecutionNumber,
    currentTab,
    executeReview,
    setCurrentTab,
    getSimpleJudgment,
  } = useReviewExecution()

  // Zip export
  const { downloadZip: rawDownloadZip, downloadReport, copyReport, downloadSpecMarkdown, downloadCodeWithLineNumbers } =
    useZipExport()

  // Split settings
  const {
    settings: splitSettings,
    previewResult: splitPreviewResult,
    isExecutingPreview: isSplitPreviewExecuting,
    error: splitPreviewError,
    pinnedDocPartIds,
    isSummarizing,
    summarizingPartIds,
    summarizeError,
    pinnedCodePartIds,
    isCodeSummarizing,
    codeSummarizingPartIds,
    codeSummarizeError,
    headings: splitHeadings,
    isLoadingHeadings: isSplitLoadingHeadings,
    headingsError: splitHeadingsError,
    preImportantSections,
    preExcludedSections,
    preImportantSplitSettings,
    normalSplitSettings,
    setSettings: setSplitSettings,
    executePreview: executeSplitPreview,
    clearPreview: clearSplitPreview,
    togglePinnedDocPart,
    toggleSummarizeMode,
    toggleExcludedDocPart,
    fetchHeadingsForContent,
    togglePreImportantSection,
    togglePreExcludedSection,
    setPreImportantSplitSettings,
    setNormalSplitSettings,
    clearHeadingsCache,
    togglePinnedCodePart,
    toggleCodeSummarizeMode,
    toggleExcludedCodePart,
    executeAllSummarize,
    isSplitEnabled,
    hasAnyPendingSummarize,
  } = useSplitSettings()

  // Split review execution state
  const [splitReviewState, setSplitReviewState] = useState<SplitReviewState>({
    phase: 'idle',
    groupReviews: [],
    currentGroupIndex: 0,
  })

  // 「分割」選択時に見出し一覧を取得
  useEffect(() => {
    if (splitSettings.reviewMode === 'split' && specMarkdown) {
      fetchHeadingsForContent(specMarkdown)
    }
  }, [splitSettings.reviewMode, specMarkdown, fetchHeadingsForContent])

  // 設計書マークダウンが変更されたら見出しキャッシュをクリア
  const prevSpecMarkdownRef = useRef(specMarkdown)
  useEffect(() => {
    if (prevSpecMarkdownRef.current !== specMarkdown) {
      prevSpecMarkdownRef.current = specMarkdown
      clearHeadingsCache()
    }
  }, [specMarkdown, clearHeadingsCache])

  // Wrap downloadZip to inject splitData when in split mode
  const downloadZip = useCallback(
    async (data: ReviewExecutionData, executionNumber: number) => {
      const splitData = splitPreviewResult
        ? {
            documentIndex: splitPreviewResult.documentIndex || undefined,
            documentMapJson: splitPreviewResult.documentMapJson || undefined,
            codeIndex: splitPreviewResult.codeIndex || undefined,
            codeMapJson: splitPreviewResult.codeMapJson || undefined,
            // グループレビュー個別結果を追加
            groupReviews: splitReviewState.groupReviews
              .filter((g) => g.status === 'completed' && g.result?.report)
              .map((g) => ({
                groupId: g.groupId,
                groupName: g.groupName,
                report: g.result!.report,
              })),
          }
        : undefined
      await rawDownloadZip(data, executionNumber, splitData)
    },
    [rawDownloadZip, splitPreviewResult, splitReviewState.groupReviews]
  )
  const [integrateSummarizeState, setIntegrateSummarizeState] = useState<IntegrateSummarizeState>({ groups: [] })
  const [batchReviewError, setBatchReviewError] = useState<string | null>(null)
  const errorActionRef = useRef<{ action: 'retry' | 'skip'; groupId: string; docMode?: 'original' | 'summarize'; codeMode?: 'original' | 'summarize' } | null>(null)
  const summarizeStateRef = useRef<Map<string, GroupSummarizeState>>(new Map())

  // System prompt text for token estimation
  const systemPromptText = useMemo(() => {
    return [
      currentPromptValues.role,
      currentPromptValues.purpose,
      currentPromptValues.format,
      currentPromptValues.notes,
    ].join('\n')
  }, [currentPromptValues])

  // Token estimation
  const tokenEstimation = useTokenEstimation(
    specMarkdown || '',
    codeWithLineNumbers || '',
    systemPromptText
  )

  // Load tools and check backend version on mount
  useEffect(() => {
    loadTools()

    // バックエンドバージョンチェック（非同期、UIをブロックしない）
    fetchHealth().then((result) => {
      if (result.ok) {
        const feVersion = APP_INFO.version.replace(/^v/, '')
        const beVersion = result.data.version.replace(/^v/, '')
        if (feVersion !== beVersion) {
          setVersionMismatch({ frontend: APP_INFO.version, backend: `v${beVersion}` })
        }
      } else if (result.reason === 'http_error') {
        // 古いバックエンドで /api/health が未実装（404, 405等）
        setVersionMismatch({ frontend: APP_INFO.version, backend: '不明（バージョン確認API未対応）' })
      }
      // network_error の場合は何もしない（バックエンド未起動は他のAPIで検知される）
    })
  }, [loadTools])

  const showToast = useCallback((message: string) => {
    setToastMessage(message)
    if (toastTimerRef.current) {
      window.clearTimeout(toastTimerRef.current)
    }
    toastTimerRef.current = window.setTimeout(() => setToastMessage(''), 3000)
  }, [])


  useEffect(() => {
    const message = sessionStorage.getItem('preset-toast')
    if (!message) return

    sessionStorage.removeItem('preset-toast')
    showToast(message)
    return () => {
      if (toastTimerRef.current) {
        window.clearTimeout(toastTimerRef.current)
      }
    }
  }, [showToast])

  const isReviewEnabled = specMarkdown && codeWithLineNumbers

  // Handler for split preview execution
  const handleSplitPreviewExecute = useCallback(async () => {
    // 元のコードファイル内容を取得（行番号なし）
    const codeFilesForSplit = await Promise.all(
      codeFiles.map(async (cf) => ({
        filename: cf.filename,
        content: await cf.file.text(),
      }))
    )

    await executeSplitPreview(
      specMarkdown,
      specFiles.find(f => f.isMain)?.filename || 'design.md',
      codeFilesForSplit,
      llmConfig,
    )
  }, [codeFiles, specMarkdown, specFiles, executeSplitPreview, llmConfig])

  const handleRetryGroup = useCallback((groupId: string, docMode?: 'original' | 'summarize', codeMode?: 'original' | 'summarize') => {
    errorActionRef.current = { action: 'retry', groupId, docMode, codeMode }
  }, [])

  const handleSkipGroup = useCallback((groupId: string) => {
    errorActionRef.current = { action: 'skip', groupId }
  }, [])

  const handleSummarizeComplete = useCallback((groupId: string, summarizeState: GroupSummarizeState) => {
    summarizeStateRef.current.set(groupId, summarizeState)
    setSplitReviewState((prev) => ({
      ...prev,
      groupReviews: prev.groupReviews.map((g) =>
        g.groupId === groupId ? { ...g, summarizeState } : g
      ),
    }))
  }, [])

  const handleIntegrateSummarizeComplete = useCallback((state: IntegrateSummarizeState) => {
    setIntegrateSummarizeState(state)
  }, [])

  // Integrate retry handler - re-execute only the integration phase
  const handleRetryIntegrate = useCallback(async () => {
    const { structureMatchingResult, groupReviews } = splitReviewState

    if (!structureMatchingResult) return

    setSplitReviewState((prev) => ({
      ...prev,
      phase: 'integrate',
      error: undefined,
    }))

    try {
      const groupReviewSummaries = groupReviews
        .filter((g) => g.status === 'completed' && g.result)
        .filter((g) => {
          const entry = integrateSummarizeState.groups.find((s) => s.groupId === g.groupId)
          return entry?.mode !== 'skip'
        })
        .map((g) => {
          const entry = integrateSummarizeState.groups.find((s) => s.groupId === g.groupId)
          const useSummarized = entry?.mode === 'summarize' && entry?.summarizedReport
          return {
            groupId: g.groupId,
            groupName: g.groupName,
            report: useSummarized ? entry.summarizedReport! : g.result!.report,
          }
        })

      const integrateResponse = await executeIntegrate({
        structureMatching: structureMatchingResult,
        groupReviews: groupReviewSummaries,
        systemPrompt: currentPromptValues,
        llmConfig: llmConfig || undefined,
        designs: specFiles.map((f) => ({ filename: f.filename, isMain: f.isMain, type: f.type, tool: f.tool })),
        codes: codeFiles.map((f) => ({ filename: f.filename })),
      })

      if (!integrateResponse.success) {
        throw new Error(integrateResponse.error || '結果統合に失敗しました')
      }

      setSplitReviewState((prev) => ({
        ...prev,
        phase: 'completed',
        integrateResult: integrateResponse,
      }))

      screenManager.showResult()
    } catch (error) {
      setSplitReviewState((prev) => ({
        ...prev,
        phase: 'error',
        error: error instanceof Error ? error.message : '結果統合に失敗しました',
      }))
    }
  }, [splitReviewState, llmConfig, currentPromptValues, screenManager, integrateSummarizeState])

  // Split review execution
  const executeSplitReviewFlow = useCallback(async () => {
    if (!splitPreviewResult) return

    // Reset state
    errorActionRef.current = null
    setSplitReviewState({
      phase: 'structure-matching',
      groupReviews: [],
      currentGroupIndex: 0,
    })

    try {
      // Phase 1: Structure Matching
      const documentIndexMd = splitPreviewResult.documentIndex || ''
      // 除外パーツのIDセットを構築
      const excludedDocPartIds = new Set(
        splitPreviewResult.documentParts?.filter(p => p.excluded).map(p => p.id) || []
      )
      // md2map生成のMAP.jsonをそのまま使用（is_subsplit, subsplit_title等を含む）、除外パーツを除去
      const documentMapJson = splitPreviewResult.documentMapJson
        ? {
            sections: splitPreviewResult.documentMapJson.filter(
              (s) => !excludedDocPartIds.has(s.id as string)
            )
          }
        : {
            sections: splitPreviewResult.documentParts
              ?.filter((p) => !p.excluded)
              .map((p) => ({
                id: p.id,
                title: p.section,
                level: p.level,
                path: p.path,
                startLine: p.startLine,
                endLine: p.endLine,
              })) || [],
          }

      // コードパートの除外フィルタリング
      const excludedCodePartIds = new Set(
        splitPreviewResult.codeParts?.filter(p => p.excluded).map(p => p.id) || []
      )

      const codeFileStructures = codeFiles.map((cf) => {
        const codeParts = (splitPreviewResult.codeParts || []).filter(p => !excludedCodePartIds.has(p.id))
        return {
          filename: cf.filename,
          indexMd: splitPreviewResult.codeIndex || '',
          mapJson: {
            symbols: codeParts.map((p) => ({
              id: p.id,  // IDを含める（LLMがマッチングに使用）
              name: p.symbol,
              symbolType: p.symbolType,
              parentSymbol: p.parentSymbol,
              startLine: p.startLine,
              endLine: p.endLine,
            })),
          },
        }
      })

      const structureMatchingResponse = await executeStructureMatching({
        document: { indexMd: documentIndexMd, mapJson: documentMapJson },
        codeFiles: codeFileStructures,
        systemPrompt: currentPromptValues,
        llmConfig: llmConfig || undefined,
      })

      if (!structureMatchingResponse.success) {
        throw new Error(structureMatchingResponse.error || '構造マッチングに失敗しました')
      }

      const groups = structureMatchingResponse.groups

      // IDのみのグループデータをフロントエンドのパーツ情報で復元
      // codeMapJson（code2mapの生MAP.json）からID→filenameのマッピングを構築
      const codeIdToFilename: Record<string, string> = {}
      if (splitPreviewResult.codeMapJson) {
        for (const entry of splitPreviewResult.codeMapJson) {
          const id = entry.id as string
          const filename = entry.original_file as string
          if (id && filename) {
            codeIdToFilename[id] = filename
          }
        }
      }

      for (const group of groups) {
        group.docSections = group.docSections
          .filter((ds) => !excludedDocPartIds.has(ds.id))  // 除外パーツを安全フィルタ
          .map((ds) => {
            const part = splitPreviewResult.documentParts?.find((p) => p.id === ds.id)
            return part
              ? { id: ds.id, title: part.displayName, path: part.path }
              : ds
          })
        group.codeSymbols = group.codeSymbols
          .filter((cs) => !excludedCodePartIds.has(cs.id))  // 除外コードパーツを安全フィルタ
          .map((cs) => {
          const part = splitPreviewResult.codeParts?.find((p) => p.id === cs.id)
          return part
            ? { id: cs.id, filename: codeIdToFilename[cs.id] || '', symbol: part.symbol }
            : cs
        })
      }

      // 重要パートを全グループに注入（重複除外）
      if (pinnedDocPartIds.length > 0) {
        const pinnedDocSections = pinnedDocPartIds
          .filter(id => !excludedDocPartIds.has(id))  // 除外パーツは注入しない
          .map(id => {
            const part = splitPreviewResult.documentParts?.find(p => p.id === id)
            if (!part) return null
            return { id: part.id, title: part.section, path: part.path }
          })
          .filter((s): s is { id: string; title: string; path: string } => s !== null)

        for (const group of groups) {
          const existingIds = new Set(group.docSections.map(s => s.id))
          for (const pinned of pinnedDocSections) {
            if (!existingIds.has(pinned.id)) {
              group.docSections.push(pinned)
            }
          }
        }
      }

      // 重要コードパートを全グループに注入（重複除外）
      if (pinnedCodePartIds.length > 0) {
        const pinnedCodeSymbols = pinnedCodePartIds
          .filter(id => !excludedCodePartIds.has(id))
          .map(id => {
            const part = splitPreviewResult.codeParts?.find(p => p.id === id)
            if (!part) return null
            return { id: part.id, filename: codeIdToFilename[part.id] || '', symbol: part.symbol }
          })
          .filter((s): s is { id: string; filename: string; symbol: string } => s !== null)

        for (const group of groups) {
          const existingIds = new Set(group.codeSymbols.map(s => s.id))
          for (const pinned of pinnedCodeSymbols) {
            if (!existingIds.has(pinned.id)) {
              group.codeSymbols.push(pinned)
            }
          }
        }
      }

      // Initialize group review states
      const initialGroupStates: GroupReviewState[] = groups.map((g) => ({
        groupId: g.groupId,
        groupName: g.groupName,
        status: 'pending',
      }))

      setSplitReviewState({
        phase: 'group-review',
        structureMatchingResult: structureMatchingResponse,
        groupReviews: initialGroupStates,
        currentGroupIndex: 0,
      })

      // Phase 2: Group Reviews
      const groupReviewResults: GroupReviewState[] = [...initialGroupStates]

      for (let i = 0; i < groups.length; i++) {
        const group = groups[i]

        // 設計書またはコードが空のグループは自動スキップ
        if (group.docSections.length === 0 || group.codeSymbols.length === 0) {
          const reason = group.docSections.length === 0
            ? '対応する設計書セクションがありません'
            : '対応するコードシンボルがありません'
          groupReviewResults[i] = {
            ...groupReviewResults[i],
            status: 'skipped',
            error: reason,
          }
          setSplitReviewState((prev) => ({
            ...prev,
            groupReviews: [...groupReviewResults],
          }))
          continue
        }

        // Build document content for this group
        // 設計書が一括モードの場合は全体のMarkdownを使用、分割モードの場合はIDベースでマッチング
        const documentContent = group.docSections.map((section) => {
          const part = splitPreviewResult.documentParts?.find((p) => p.id === section.id)
          const displayName = part?.displayName || section.title
          const startLine = part?.startLine || 0
          const endLine = part?.endLine || 0
          // 「要約」が選択されていて要約済みなら要約テキストを使用
          const content = (part?.summarizeMode === 'summarize' && part?.summarizedContent)
            ? part.summarizedContent
            : part?.content || ''
          const isSummarized = part?.summarizeMode === 'summarize' && !!part?.summarizedContent
          const header = isSummarized
            ? `### ${displayName} (L${startLine}-L${endLine}) [要約版]`
            : `### ${displayName} (L${startLine}-L${endLine})`
          return `${header}\n\n${content}`
        }).join('\n\n')

        // Build code content for this group
        // コードが一括モードの場合は全体のコードを使用、分割モードの場合はIDベースでマッチング
        const codeContent = group.codeSymbols.map((sym) => {
          const part = splitPreviewResult.codeParts?.find((p) => p.id === sym.id)
          const symbolType = part?.symbolType || 'unknown'
          const startLine = part?.startLine || 0
          const endLine = part?.endLine || 0
          const isSummarized = part?.summarizeMode === 'summarize' && !!part?.summarizedContent
          const content = isSummarized ? part.summarizedContent : (part?.content || '')
          const summaryMarker = isSummarized ? ' [要約版]' : ''
          return `### ${sym.filename}:${sym.symbol} (${symbolType}, L${startLine}-L${endLine})${summaryMarker}\n\n\`\`\`\n${content}\n\`\`\``
        }).join('\n\n')

        // Retry loop: execute group review, pause on error for retry/skip
        let resolved = false
        while (!resolved) {
          // Update status to in_progress
          groupReviewResults[i] = { ...groupReviewResults[i], status: 'in_progress', error: undefined }
          setSplitReviewState((prev) => ({
            ...prev,
            phase: 'group-review',
            groupReviews: [...groupReviewResults],
            currentGroupIndex: i,
          }))

          let failed = false
          let errorMessage = ''

          try {
            // リトライ時は要約版コンテンツを使用する可能性がある
            const currentGroupState = groupReviewResults[i]
            // summarizeStateはReact stateに保存されるため、ローカル配列には反映されない
            // refから最新の要約データを取得する
            const latestSummarizeState = summarizeStateRef.current.get(group.groupId) || currentGroupState.summarizeState
            const effectiveDocContent = latestSummarizeState?.documentSummarized
              && currentGroupState.usedSummarizedDoc
              ? latestSummarizeState.documentSummarized
              : documentContent
            const effectiveCodeContent = latestSummarizeState?.codeSummarized
              && currentGroupState.usedSummarizedCode
              ? latestSummarizeState.codeSummarized
              : codeContent

            const groupResponse = await executeGroupReview({
              groupId: group.groupId,
              groupName: group.groupName,
              documentContent: effectiveDocContent,
              codeContent: effectiveCodeContent,
              systemPrompt: currentPromptValues,
              llmConfig: llmConfig || undefined,
              documentIndexMd: splitPreviewResult.documentIndex || undefined,
              codeIndexMd: splitPreviewResult.codeIndex || undefined,
              allGroups: structureMatchingResponse.groups,
            })

            if (groupResponse.success && groupResponse.reviewResult) {
              groupReviewResults[i] = {
                ...groupReviewResults[i],
                status: 'completed',
                result: groupResponse.reviewResult,
                tokensUsed: groupResponse.tokensUsed,
              }
              resolved = true
            } else {
              failed = true
              errorMessage = groupResponse.error || 'グループレビューに失敗しました'
              groupReviewResults[i] = {
                ...groupReviewResults[i],
                errorCode: groupResponse.errorCode,
              }
            }
          } catch (error) {
            failed = true
            errorMessage = error instanceof Error ? error.message : 'グループレビューに失敗しました'
          }

          if (failed) {
            // Mark as error and pause for user action
            groupReviewResults[i] = {
              ...groupReviewResults[i],
              status: 'error',
              error: errorMessage,
            }
            errorActionRef.current = null
            setSplitReviewState((prev) => ({
              ...prev,
              phase: 'paused',
              groupReviews: [...groupReviewResults],
              currentGroupIndex: i,
            }))

            // Wait for user to choose retry or skip
            while (errorActionRef.current === null) {
              await new Promise((resolve) => setTimeout(resolve, 500))
            }

            const errorAction = errorActionRef.current as {
              action: 'retry' | 'skip'
              groupId: string
              docMode?: 'original' | 'summarize'
              codeMode?: 'original' | 'summarize'
            }
            errorActionRef.current = null
            const action = errorAction.action

            if (action === 'retry') {
              // 要約版を使用するかのフラグを設定
              if (errorAction.docMode === 'summarize' || errorAction.codeMode === 'summarize') {
                groupReviewResults[i] = {
                  ...groupReviewResults[i],
                  usedSummarizedDoc: errorAction.docMode === 'summarize',
                  usedSummarizedCode: errorAction.codeMode === 'summarize',
                }
              }
              continue
            } else {
              // Skip: mark as skipped and move on
              groupReviewResults[i] = {
                ...groupReviewResults[i],
                status: 'skipped',
              }
              resolved = true
            }
          }
        }

        setSplitReviewState((prev) => ({
          ...prev,
          groupReviews: [...groupReviewResults],
        }))
      }

      // Check if any completed groups exist before integration
      const hasCompletedGroups = groupReviewResults.some((g) => g.status === 'completed')
      if (!hasCompletedGroups) {
        throw new Error('完了したグループレビューがないため、結果統合を実行できません')
      }

      // Phase 3: Integration
      setSplitReviewState((prev) => ({ ...prev, phase: 'integrate' }))

      const groupReviewSummaries = groupReviewResults
        .filter((g) => g.status === 'completed' && g.result)
        .map((g) => ({
          groupId: g.groupId,
          groupName: g.groupName,
          report: g.result!.report,
        }))

      const integrateResponse = await executeIntegrate({
        structureMatching: structureMatchingResponse,
        groupReviews: groupReviewSummaries,
        systemPrompt: currentPromptValues,
        llmConfig: llmConfig || undefined,
        designs: specFiles.map((f) => ({ filename: f.filename, isMain: f.isMain, type: f.type, tool: f.tool })),
        codes: codeFiles.map((f) => ({ filename: f.filename })),
        documentIndexMd: splitPreviewResult.documentIndex || undefined,
        codeIndexMd: splitPreviewResult.codeIndex || undefined,
      })

      if (!integrateResponse.success) {
        throw new Error(integrateResponse.error || '結果統合に失敗しました')
      }

      setSplitReviewState((prev) => ({
        ...prev,
        phase: 'completed',
        integrateResult: integrateResponse,
      }))

      // Show result screen
      screenManager.showResult()
    } catch (error) {
      setSplitReviewState((prev) => ({
        ...prev,
        phase: 'error',
        error: error instanceof Error ? error.message : 'レビュー実行に失敗しました',
      }))
    }
  }, [splitPreviewResult, codeFiles, llmConfig, screenManager, currentPromptValues, pinnedDocPartIds, pinnedCodePartIds])

  // Structure matching retry handler - re-execute from the beginning
  const handleRetryStructureMatching = useCallback(() => {
    executeSplitReviewFlow()
  }, [executeSplitReviewFlow])

  const handleReviewExecute = async () => {
    if (!specMarkdown || !codeWithLineNumbers) return

    screenManager.showExecuting()

    // 分割モードの場合は分割レビューフローを実行
    if (isSplitEnabled && splitPreviewResult) {
      await executeSplitReviewFlow()
      return
    }

    // 一括モード
    setBatchReviewError(null)
    try {
      await executeReview({
        specFiles,
        codeFiles,
        specMarkdown,
        codeWithLineNumbers,
        systemPrompt: currentPromptValues,
        llmConfig: llmConfig || undefined,
      })
      screenManager.showResult()
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'レビュー実行に失敗しました'
      setBatchReviewError(errorMessage)
    }
  }

  const handleConvertSpecs = () => {
    convertSpecs(getTypeNote)
  }

  // Config file load handler - adapts File to string content
  const handleConfigFileLoad = async (content: string, filename: string) => {
    // Create a File object from the content
    const file = new File([content], filename, { type: 'text/markdown' })
    await loadConfigFile(file)
  }

  // LLM connection test handler
  const handleTestConnection = useCallback(async () => {
    try {
      // Build request based on config
      if (llmConfig) {
        const result = await testLlmConnection({
          provider: llmConfig.provider,
          model: selectedModel || llmConfig.model,
          apiKey: llmConfig.apiKey,
          accessKeyId: llmConfig.accessKeyId,
          secretAccessKey: llmConfig.secretAccessKey,
          region: llmConfig.region,
        })
        return {
          success: result.status === 'connected',
          model: result.model,
          provider: result.provider,
          error: result.error,
        }
      } else {
        // No config - test system LLM
        const result = await testLlmConnection({})
        return {
          success: result.status === 'connected',
          model: result.model,
          provider: result.provider,
          error: result.error,
        }
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : '接続エラー',
      }
    }
  }, [llmConfig, selectedModel])

  // Render main screen content
  const mainScreen = (
    <Layout>
      {/* Header */}
      <Header
        title={APP_INFO.description}
        leftContent={
          <VersionSelector
            versions={versions}
            currentVersion={currentVersion}
            onVersionSelect={switchVersion}
          />
        }
        rightContent={
          <div className="flex items-center gap-3">
            <Link
              to="/presets"
              className="flex items-center gap-1 text-gray-500 hover:text-gray-700 text-sm"
            >
              <BookOpen className="w-4 h-4" />
              プリセット
            </Link>
            <button
              onClick={settingsModal.open}
              className="text-gray-500 hover:text-gray-700"
              title="設定"
            >
              <Settings className="w-6 h-6" />
            </button>
          </div>
        }
      />

      {/* Spec files section */}
      {/* バージョン不一致警告バナー */}
      {versionMismatch && (
        <div className="mb-4 p-3 bg-amber-50 border border-amber-300 rounded-lg flex items-start gap-2">
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1 text-sm text-amber-800">
            バックエンド ({versionMismatch.backend}) とフロントエンド ({versionMismatch.frontend}) のバージョンが一致しません。正しく動作しない可能性があります。
          </div>
          <button
            onClick={() => setVersionMismatch(null)}
            className="text-amber-600 hover:text-amber-800 flex-shrink-0"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <Card className="mb-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">設計書 (Excel / Word)</h2>
        <div className="flex items-center gap-2 mb-2">
          <FileInputButton
            accept=".xlsx,.xls,.docx"
            multiple
            onFilesSelect={addSpecFiles}
            label="ファイルを選択"
          />
          <span className="text-gray-600 text-sm flex items-center gap-1">
            {specFiles.length > 0 ? (
              <>
                <FileText className="w-4 h-4" />
                {specFiles.map((f) => f.filename).join(', ')}
              </>
            ) : (
              '選択してください'
            )}
          </span>
        </div>
        <SpecFileList
          files={specFiles}
          availableTools={availableTools}
          specTypesList={getSpecTypesList()}
          specMarkdown={specMarkdown}
          specStatus={specStatus}
          isConverting={isSpecConverting}
          onMainChange={setMainSpec}
          onTypeChange={setSpecType}
          onToolChange={setSpecTool}
          onApplyToolToAll={applyToolToAll}
          onConvert={handleConvertSpecs}
          onDownload={() => specMarkdown && downloadSpecMarkdown(specMarkdown)}
        />
        <MarkdownOrganizer
          specMarkdown={specMarkdown}
          specFiles={specFiles}
          llmConfig={llmConfig || undefined}
          getTypeNote={getTypeNote}
          onAdopt={(organizedFiles) => applyOrganizedMarkdown(organizedFiles, getTypeNote)}
        />
      </Card>

      {/* Code files section */}
      <Card className="mb-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">プログラム</h2>
        <div className="flex items-center gap-2 mb-2">
          <FileInputButton
            multiple
            onFilesSelect={addCodeFiles}
            label="ファイルを選択"
          />
          <span className="text-gray-600 text-sm flex items-center gap-1">
            {codeFiles.length > 0 ? (
              <>
                <FileText className="w-4 h-4" />
                {codeFiles.map((f) => f.filename).join(', ')}
              </>
            ) : (
              '選択してください'
            )}
          </span>
        </div>
        <CodeFileList
          files={codeFiles}
          codeWithLineNumbers={codeWithLineNumbers}
          codeStatus={codeStatus}
          isConverting={isCodeConverting}
          onConvert={convertCodes}
          onDownload={() => codeWithLineNumbers && downloadCodeWithLineNumbers(codeWithLineNumbers)}
        />
      </Card>

      {/* System prompt settings */}
      <SystemPromptEditor
        presets={systemPromptPresets}
        selectedPreset={selectedPreset}
        currentValues={currentPromptValues}
        onPresetChange={selectPreset}
        onValueChange={updatePromptValue}
        isCollapsible={true}
        defaultExpanded={false}
      />

      {/* Token estimate */}
      <TokenEstimator
        totalTokens={tokenEstimation.totalTokens}
        specTokens={tokenEstimation.specTokens}
        codeTokens={tokenEstimation.codeTokens}
        promptTokens={tokenEstimation.promptTokens}
        isWarning={tokenEstimation.isWarning}
        isVisible={!!(specMarkdown || codeWithLineNumbers)}
      />

      {/* Split settings */}
      <div className="mb-6">
        <SplitSettingsSection
          settings={splitSettings}
          onSettingsChange={setSplitSettings}
          onShowToast={showToast}
          previewResult={splitPreviewResult}
          onExecutePreview={handleSplitPreviewExecute}
          onClearPreview={clearSplitPreview}
          isExecuting={isSplitPreviewExecuting}
          hasDesignDoc={!!specMarkdown}
          hasCodeFiles={!!codeWithLineNumbers}
          codeFilenames={codeFiles.map(f => f.filename)}
          pinnedDocPartIds={pinnedDocPartIds}
          onTogglePinnedDocPart={togglePinnedDocPart}
          isSummarizing={isSummarizing}
          summarizingPartIds={summarizingPartIds}
          summarizeError={summarizeError}
          onToggleSummarizeMode={toggleSummarizeMode}
          onToggleExcludedDocPart={toggleExcludedDocPart}
          previewError={splitPreviewError}
          headings={splitHeadings}
          isLoadingHeadings={isSplitLoadingHeadings}
          headingsError={splitHeadingsError}
          preImportantSections={preImportantSections}
          onTogglePreImportantSection={togglePreImportantSection}
          preExcludedSections={preExcludedSections}
          onTogglePreExcludedSection={togglePreExcludedSection}
          preImportantSplitSettings={preImportantSplitSettings}
          normalSplitSettings={normalSplitSettings}
          onPreImportantSplitSettingsChange={setPreImportantSplitSettings}
          onNormalSplitSettingsChange={setNormalSplitSettings}
          pinnedCodePartIds={pinnedCodePartIds}
          onTogglePinnedCodePart={togglePinnedCodePart}
          onToggleCodeSummarizeMode={toggleCodeSummarizeMode}
          onToggleExcludedCodePart={toggleExcludedCodePart}
          isCodeSummarizing={isCodeSummarizing}
          codeSummarizingPartIds={codeSummarizingPartIds}
          codeSummarizeError={codeSummarizeError}
          hasAnyPendingSummarize={hasAnyPendingSummarize}
          onExecuteAllSummarize={() => executeAllSummarize(llmConfig)}
        />
      </div>

      {/* Review button */}
      <Card>
        <Button
          variant="success"
          size="lg"
          disabled={!isReviewEnabled || (isSplitEnabled && !splitPreviewResult) || (isSplitEnabled && hasAnyPendingSummarize) || (isSplitEnabled && !!splitPreviewResult && !splitPreviewResult.codeParts?.length) || (isSplitEnabled && !!splitPreviewResult && !splitPreviewResult.documentParts?.length)}
          onClick={handleReviewExecute}
        >
          レビュー実行
        </Button>
        {!isReviewEnabled && (
          <p className="text-xs text-orange-500 mt-1 text-center">
            ※ レビューを実行するには、設計書とプログラムを両方変換してください。
          </p>
        )}
        {isSplitEnabled && !splitPreviewResult && (
          <p className="text-xs text-orange-500 mt-1 text-center">
            ※ 分割レビューを実行するには、分割設定で「分割プレビュー」を行ってください。
          </p>
        )}

        {isSplitEnabled && hasAnyPendingSummarize && (
          <p className="text-xs text-orange-500 mt-1 text-center">
            ⚠ 要約が選択されていますが未実行です。「選択した要約を実行」をクリックしてから、レビューを実行してください。
          </p>
        )}
        <p className="text-xs text-gray-400 mt-1 text-center">
          {isSplitEnabled
            ? '※ 設計書とプログラムの関連を分析して、いくつかのグループに分割してレビューを実行します。'
            : '※ 同じ設定でレビューを2回実行します。それぞれ個別に結果を確認できます。'}
        </p>
      </Card>

      {/* Settings modal */}
      <SettingsModal
        isOpen={settingsModal.isOpen}
        onClose={settingsModal.close}
        appInfo={APP_INFO}
        llmSettings={
          reviewerConfig?.llm
            ? { ...reviewerConfig.llm, selectedModel }
            : undefined
        }
        onModelChange={setSelectedModel}
        onConfigFileLoad={handleConfigFileLoad}
        onSaveToStorage={saveConfigToBrowser}
        onClearStorage={clearSavedConfig}
        loadedConfigFilename={configFilename || undefined}
        configLoadStatus={configLoadStatus || undefined}
        isConfigSavedToBrowser={hasSavedConfig()}
        isConfigModified={configModified}
        onTestConnection={handleTestConnection}
        isSystemFallback={!reviewerConfig?.llm}
        systemPromptPresets={systemPromptPresets}
        extensionSections={[<SpecTypesSection key="spec-types" specTypes={specTypesConfig} />]}
      />
    </Layout>
  )

  const executingScreen = isSplitEnabled ? (
    <SplitExecutingScreen
      state={splitReviewState}
      onBack={screenManager.showMain}
      onRetryStructureMatching={handleRetryStructureMatching}
      onRetryGroup={handleRetryGroup}
      onSkipGroup={handleSkipGroup}
      onRetryIntegrate={handleRetryIntegrate}
      currentDocumentContent={(() => {
        const errorGroup = splitReviewState.groupReviews.find((g) => g.status === 'error')
        if (!errorGroup || !splitReviewState.structureMatchingResult) return undefined
        const group = splitReviewState.structureMatchingResult.groups.find((g) => g.groupId === errorGroup.groupId)
        if (!group) return undefined
        return group.docSections.map((section) => {
          const part = splitPreviewResult?.documentParts?.find((p) => p.id === section.id)
          return part?.content || ''
        }).join('\n\n')
      })()}
      currentCodeContent={(() => {
        const errorGroup = splitReviewState.groupReviews.find((g) => g.status === 'error')
        if (!errorGroup || !splitReviewState.structureMatchingResult) return undefined
        const group = splitReviewState.structureMatchingResult.groups.find((g) => g.groupId === errorGroup.groupId)
        if (!group) return undefined
        return group.codeSymbols.map((sym) => {
          const part = splitPreviewResult?.codeParts?.find((p) => p.id === sym.id)
          return part?.content || ''
        }).join('\n\n')
      })()}
      llmConfig={llmConfig || undefined}
      onSummarizeComplete={handleSummarizeComplete}
      integrateSummarizeState={integrateSummarizeState}
      onIntegrateSummarizeComplete={handleIntegrateSummarizeComplete}
    />
  ) : (
    <ExecutingScreen
      currentExecution={currentExecutionNumber}
      totalExecutions={2}
      onBack={screenManager.showMain}
      error={batchReviewError || undefined}
      onRetry={handleReviewExecute}
    />
  )

  // 分割レビュー用のダウンロードデータを構築
  // reviewMetaはAPIから取得し、designs/programs・トークン合計はローカルで補完
  const splitReviewData: ReviewExecutionData | undefined = (() => {
    if (!isSplitEnabled || splitReviewState.phase !== 'completed' || !splitReviewState.integrateResult?.report) {
      return undefined
    }

    // 全フェーズのトークンを合計
    const structureTokens = splitReviewState.structureMatchingResult?.tokensUsed || { input: 0, output: 0 }
    const groupTokens = splitReviewState.groupReviews.reduce(
      (acc, g) => ({
        input: acc.input + (g.tokensUsed?.input || 0),
        output: acc.output + (g.tokensUsed?.output || 0),
      }),
      { input: 0, output: 0 }
    )
    const integrateTokens = splitReviewState.integrateResult.tokensUsed || { input: 0, output: 0 }
    const totalInputTokens = structureTokens.input + groupTokens.input + integrateTokens.input
    const totalOutputTokens = structureTokens.output + groupTokens.output + integrateTokens.output

    return {
      systemPrompt: currentPromptValues,
      specMarkdown: specMarkdown || '',
      codeWithLineNumbers: codeWithLineNumbers || '',
      report: splitReviewState.integrateResult.report,
      reviewMeta: {
        version: splitReviewState.integrateResult.reviewMeta?.version || 'unknown',
        modelId: splitReviewState.integrateResult.reviewMeta?.modelId || 'unknown',
        executedAt: splitReviewState.integrateResult.reviewMeta?.executedAt || new Date().toISOString(),
        inputTokens: totalInputTokens,
        outputTokens: totalOutputTokens,
        reviewMode: 'split' as const,
        // designs/programs/groupsはAPIに含まれないためローカルで構築
        designs: specFiles.map((f) => ({
          filename: f.filename,
          role: f.isMain ? 'メイン設計書' : '参考資料',
          type: f.type,
          tool: f.tool,
        })),
        programs: codeFiles.map((f) => ({
          filename: f.filename,
        })),
        groups: splitReviewState.structureMatchingResult?.groups || [],
      },
    }
  })()

  const resultScreen = (
    <ReviewResult
      results={reviewResults}
      currentTab={currentTab}
      onTabChange={setCurrentTab}
      onCopyReport={copyReport}
      onDownloadReport={downloadReport}
      onDownloadZip={downloadZip}
      getSimpleJudgment={getSimpleJudgment}
      onBack={screenManager.showMain}
      splitReviewState={splitReviewState}
      splitReviewData={splitReviewData}
      isSplitMode={isSplitEnabled && splitReviewState.phase === 'completed'}
    />
  )

  return (
    <>
      {toastMessage && (
        <div className="fixed right-6 top-6 z-50 rounded-md bg-gray-900 px-4 py-2 text-sm text-white shadow-lg">
          {toastMessage}
        </div>
      )}
      <ScreenContainer
        currentScreen={screenManager.currentScreen as ScreenState}
        mainScreen={mainScreen}
        executingScreen={executingScreen}
        resultScreen={resultScreen}
      />
    </>
  )
}
