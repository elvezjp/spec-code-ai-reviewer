import { useEffect, useMemo } from 'react'
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
import { SpecTypesSection, SpecFileList, CodeFileList, ReviewResult, ExecutingScreen } from './components'
import { useFileConversion, useReviewExecution, useReviewerSettings, useZipExport } from './hooks'

const APP_INFO = {
  name: 'spec-code-ai-reviewer',
  version: 'v0.6.0',
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
    loadConfigFile,
    saveConfigToBrowser,
    clearSavedConfig,
  } = useReviewerSettings()

  // Review execution
  const {
    reviewResults,
    currentTab,
    reviewError,
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
    } catch {
      screenManager.showMain()
      if (reviewError) {
        alert(reviewError)
      }
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

  // Render main screen content
  const mainScreen = (
    <Layout>
      {/* Header */}
      <Card className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <VersionSelector
            versions={versions}
            currentVersion={currentVersion}
            onVersionSelect={switchVersion}
          />
          <button
            onClick={settingsModal.open}
            className="text-gray-500 hover:text-gray-700"
            title="設定"
          >
            <Settings className="w-6 h-6" />
          </button>
        </div>
        <Header title={APP_INFO.description} />
      </Card>

      {/* File upload section */}
      <Card className="mb-6">
        {/* Spec files */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">設計書 (Excel)</label>
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
        </div>

        {/* Code files */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">プログラム</label>
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
        </div>
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
          variant="primary"
          size="lg"
          className="w-full bg-green-500 hover:bg-green-600"
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
        llmSettings={reviewerConfig?.llm}
        onModelChange={setSelectedModel}
        onConfigFileLoad={handleConfigFileLoad}
        onSaveToStorage={saveConfigToBrowser}
        onClearStorage={clearSavedConfig}
        loadedConfigFilename={configFilename || undefined}
        onTestConnection={async () => {
          // TODO: Implement connection test
          return true
        }}
        isSystemFallback={!llmConfig}
        systemPromptPresets={systemPromptPresets}
        extensionSections={[<SpecTypesSection key="spec-types" specTypes={specTypesConfig} />]}
      />
    </Layout>
  )

  const executingScreen = <ExecutingScreen currentExecution={1} totalExecutions={2} />

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
