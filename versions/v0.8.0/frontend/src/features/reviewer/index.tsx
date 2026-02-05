import { useEffect, useMemo, useCallback, useState, useRef } from 'react'
import { Settings, FileText, BookOpen } from 'lucide-react'
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
import { testLlmConnection, executeStructureMatching, executeGroupReview, executeIntegrate } from './services/api'
import type { SplitReviewState, GroupReviewState, MatchedGroup, GroupDocumentPart, GroupCodePart } from './types'

const APP_INFO = {
  name: 'spec-code-ai-reviewer',
  version: 'v0.8.0',
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
  const { downloadZip, downloadReport, copyReport, downloadSpecMarkdown, downloadCodeWithLineNumbers } =
    useZipExport()

  // Split settings (v0.8.0)
  const {
    settings: splitSettings,
    previewResult: splitPreviewResult,
    isExecutingPreview: isSplitPreviewExecuting,
    setSettings: setSplitSettings,
    executePreview: executeSplitPreview,
    clearPreview: clearSplitPreview,
    isSplitEnabled,
  } = useSplitSettings()

  // Split review execution state (v0.8.0)
  const [splitReviewState, setSplitReviewState] = useState<SplitReviewState>({
    phase: 'idle',
    groupReviews: [],
    currentGroupIndex: 0,
  })
  const isPausedRef = useRef(false)

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

  // Load tools on mount
  useEffect(() => {
    loadTools()
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
      codeFilesForSplit
    )
  }, [codeFiles, specMarkdown, specFiles, executeSplitPreview])

  // Split review pause/resume handlers
  const handleSplitPause = useCallback(() => {
    isPausedRef.current = true
    setSplitReviewState((prev) => ({ ...prev, phase: 'paused' }))
  }, [])

  const handleSplitResume = useCallback(() => {
    isPausedRef.current = false
    setSplitReviewState((prev) => ({ ...prev, phase: 'group-review' }))
  }, [])

  // Split review execution
  const executeSplitReviewFlow = useCallback(async () => {
    if (!splitPreviewResult) return

    // Reset state
    isPausedRef.current = false
    setSplitReviewState({
      phase: 'structure-matching',
      groupReviews: [],
      currentGroupIndex: 0,
    })

    try {
      // Phase 1: Structure Matching
      const documentIndexMd = splitPreviewResult.documentIndex || ''
      const documentMapJson = {
        sections: splitPreviewResult.documentParts?.map((p) => ({
          title: p.section,
          level: p.level,
          path: p.path,
          startLine: p.startLine,
          endLine: p.endLine,
        })) || [],
      }

      const codeFileStructures = codeFiles.map((cf, index) => {
        const codeParts = splitPreviewResult.codeParts || []
        return {
          filename: cf.filename,
          indexMd: splitPreviewResult.codeIndex || '',
          mapJson: {
            symbols: codeParts.map((p) => ({
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
        llmConfig: llmConfig || undefined,
      })

      if (!structureMatchingResponse.success) {
        throw new Error(structureMatchingResponse.error || '構造マッチングに失敗しました')
      }

      const groups = structureMatchingResponse.groups

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
        // Check for pause
        if (isPausedRef.current) {
          setSplitReviewState((prev) => ({
            ...prev,
            phase: 'paused',
            currentGroupIndex: i,
            groupReviews: groupReviewResults,
          }))
          // Wait for resume
          while (isPausedRef.current) {
            await new Promise((resolve) => setTimeout(resolve, 500))
          }
        }

        const group = groups[i]

        // Update status to in_progress
        groupReviewResults[i] = { ...groupReviewResults[i], status: 'in_progress' }
        setSplitReviewState((prev) => ({
          ...prev,
          groupReviews: [...groupReviewResults],
          currentGroupIndex: i,
        }))

        // Build document parts for this group
        const documentParts: GroupDocumentPart[] = group.docSections.map((section) => {
          const part = splitPreviewResult.documentParts?.find((p) => p.path === section.path)
          return {
            title: section.title,
            path: section.path,
            startLine: part?.startLine || 0,
            endLine: part?.endLine || 0,
            content: part?.content || '',
          }
        })

        // Build code parts for this group
        const codeParts: GroupCodePart[] = group.codeSymbols.map((sym) => {
          const part = splitPreviewResult.codeParts?.find((p) => p.symbol === sym.symbol)
          return {
            filename: sym.filename,
            symbol: sym.symbol,
            symbolType: part?.symbolType || 'unknown',
            startLine: part?.startLine || 0,
            endLine: part?.endLine || 0,
            content: part?.content || '',
          }
        })

        try {
          const groupResponse = await executeGroupReview({
            groupId: group.groupId,
            groupName: group.groupName,
            documentParts,
            codeParts,
            llmConfig: llmConfig || undefined,
          })

          if (groupResponse.success && groupResponse.reviewResult) {
            groupReviewResults[i] = {
              ...groupReviewResults[i],
              status: 'completed',
              result: groupResponse.reviewResult,
            }
          } else {
            groupReviewResults[i] = {
              ...groupReviewResults[i],
              status: 'error',
              error: groupResponse.error || 'グループレビューに失敗しました',
            }
          }
        } catch (error) {
          groupReviewResults[i] = {
            ...groupReviewResults[i],
            status: 'error',
            error: error instanceof Error ? error.message : 'グループレビューに失敗しました',
          }
        }

        setSplitReviewState((prev) => ({
          ...prev,
          groupReviews: [...groupReviewResults],
        }))
      }

      // Phase 3: Integration
      setSplitReviewState((prev) => ({ ...prev, phase: 'integrate' }))

      const groupReviewSummaries = groupReviewResults
        .filter((g) => g.status === 'completed' && g.result)
        .map((g) => ({
          groupId: g.groupId,
          groupName: g.groupName,
          summary: g.result!.summary,
          findings: g.result!.findings,
        }))

      const integrateResponse = await executeIntegrate({
        structureMatching: structureMatchingResponse,
        groupReviews: groupReviewSummaries,
        systemPrompt: systemPromptText,
        llmConfig: llmConfig || undefined,
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
      // screenManager.showResult() // TODO: 画面確認用に一時無効化
    } catch (error) {
      setSplitReviewState((prev) => ({
        ...prev,
        phase: 'error',
        error: error instanceof Error ? error.message : 'レビュー実行に失敗しました',
      }))
    }
  }, [splitPreviewResult, codeFiles, llmConfig, screenManager, systemPromptText])

  const handleReviewExecute = async () => {
    if (!specMarkdown || !codeWithLineNumbers) return

    screenManager.showExecuting()

    // 分割モードの場合は分割レビューフローを実行
    if (isSplitEnabled && splitPreviewResult) {
      await executeSplitReviewFlow()
      return
    }

    // 通常モード
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
      screenManager.showMain()
      const errorMessage = error instanceof Error ? error.message : 'レビュー実行に失敗しました'
      alert(errorMessage)
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
      <Card className="mb-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">設計書 (Excel)</h2>
        <div className="flex items-center gap-2 mb-2">
          <FileInputButton
            accept=".xlsx,.xls"
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

      {/* Split settings (v0.8.0) */}
      <div className="mb-6">
        <SplitSettingsSection
          settings={splitSettings}
          onSettingsChange={setSplitSettings}
          previewResult={splitPreviewResult}
          onExecutePreview={handleSplitPreviewExecute}
          onClearPreview={clearSplitPreview}
          isExecuting={isSplitPreviewExecuting}
          hasDesignDoc={!!specMarkdown}
          hasCodeFiles={!!codeWithLineNumbers}
          codeFilenames={codeFiles.map(f => f.filename)}
        />
      </div>

      {/* Review button */}
      <Card>
        <Button
          variant="success"
          size="lg"
          disabled={!isReviewEnabled || (isSplitEnabled && !splitPreviewResult)}
          onClick={handleReviewExecute}
        >
          レビュー実行
        </Button>
        {!isReviewEnabled && (
          <p className="text-xs text-orange-500 mt-3 text-center">
            ※ レビューを実行するには、設計書とプログラムを両方変換してください。
          </p>
        )}
        {isSplitEnabled && !splitPreviewResult && (
          <p className="text-xs text-orange-500 mt-3 text-center">
            ※ 分割レビューを実行するには、先に「分割プレビュー実行」を行ってください。
          </p>
        )}
        <p className="text-xs text-gray-400 mt-1 text-center">
          ※ 同じ設定でレビューを2回実行します。それぞれ個別に結果を確認できます。
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
      onPause={handleSplitPause}
      onResume={handleSplitResume}
    />
  ) : (
    <ExecutingScreen currentExecution={currentExecutionNumber} totalExecutions={2} />
  )

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
