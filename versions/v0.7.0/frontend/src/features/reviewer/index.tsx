import { useEffect, useMemo, useCallback } from 'react'
import { Settings, FileText } from 'lucide-react'
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
  MarkdownOrganizer,
} from './components'
import { useFileConversion, useReviewExecution, useReviewerSettings, useZipExport } from './hooks'
import { testLlmConnection } from './services/api'

const APP_INFO = {
  name: 'spec-code-ai-reviewer',
  version: 'v0.7.0',
  description: '設計書-Javaプログラム突合 AIレビュアー',
  copyright: '© 株式会社エルブズ',
  url: 'https://elvez.co.jp',
}

export function Reviewer() {
  const settingsModal = useModal()
  const screenManager = useScreenManager()
  const { versions, currentVersion, switchVersion } = useVersions()

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

  const isReviewEnabled = specMarkdown && codeWithLineNumbers

  const handleReviewExecute = async () => {
    if (!specMarkdown || !codeWithLineNumbers) return

    screenManager.showExecuting()

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
          <button
            onClick={settingsModal.open}
            className="text-gray-500 hover:text-gray-700"
            title="設定"
          >
            <Settings className="w-6 h-6" />
          </button>
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
        isWarning={tokenEstimation.isWarning}
        isVisible={!!(specMarkdown || codeWithLineNumbers)}
      />

      {/* Review button */}
      <Card>
        <Button
          variant="success"
          size="lg"
          disabled={!isReviewEnabled}
          onClick={handleReviewExecute}
        >
          レビュー実行
        </Button>
        {!isReviewEnabled && (
          <p className="text-xs text-orange-500 mt-3 text-center">
            ※ レビューを実行するには、設計書とプログラムを両方変換してください。
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

  const executingScreen = <ExecutingScreen currentExecution={currentExecutionNumber} totalExecutions={2} />

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
    />
  )

  return (
    <ScreenContainer
      currentScreen={screenManager.currentScreen as ScreenState}
      mainScreen={mainScreen}
      executingScreen={executingScreen}
      resultScreen={resultScreen}
    />
  )
}
