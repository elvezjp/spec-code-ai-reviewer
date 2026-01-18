import { useCallback } from 'react'
import { Layout, Header } from '@core/index'
import { useConfigState } from './hooks/useConfigState'
import { useValidation } from './hooks/useValidation'
import {
  InfoSection,
  LlmSection,
  SpecTypesTable,
  SystemPromptsSection,
  DownloadButton,
} from './components'
import { generateMarkdown, downloadMarkdown } from './services/markdownGenerator'
import { CONFIG_SCHEMA } from './schema/configSchema'

export function ConfigGenerator() {
  const {
    formState,
    handleProviderChange,
    handleLlmFieldChange,
    handleArrayItemChange,
    handleArrayItemAdd,
    handleArrayItemRemove,
    handleSpecTypeChange,
    handleSpecTypeAdd,
    handleSpecTypeRemove,
    handleSystemPromptChange,
    handleSystemPromptAdd,
    handleSystemPromptRemove,
  } = useConfigState()

  const { validate, getFieldError } = useValidation()

  const handleDownload = useCallback(() => {
    const errors = validate(formState)
    if (errors.length > 0) {
      alert('入力内容にエラーがあります。赤字のメッセージを確認してください。')
      return
    }

    const markdown = generateMarkdown(formState)
    downloadMarkdown(markdown)
  }, [formState, validate])

  return (
    <Layout>
      {/* ヘッダー */}
      <Header title="設定ファイルジェネレーター">
        <p className="text-gray-600 text-sm text-center">
          {CONFIG_SCHEMA.meta.outputTitle}を作成します。<br />
          各項目を入力して「ダウンロード」ボタンを押してください。
        </p>
      </Header>

      {/* info セクション */}
      <InfoSection />

      {/* llm セクション */}
      <LlmSection
        formState={formState}
        onProviderChange={handleProviderChange}
        onFieldChange={handleLlmFieldChange}
        onArrayItemChange={handleArrayItemChange}
        onArrayItemAdd={handleArrayItemAdd}
        onArrayItemRemove={handleArrayItemRemove}
        getFieldError={getFieldError}
      />

      {/* specTypes セクション */}
      <SpecTypesTable
        specTypes={formState.specTypes}
        onSpecTypeChange={handleSpecTypeChange}
        onSpecTypeAdd={handleSpecTypeAdd}
        onSpecTypeRemove={handleSpecTypeRemove}
      />

      {/* systemPrompts セクション */}
      <SystemPromptsSection
        systemPrompts={formState.systemPrompts}
        onSystemPromptChange={handleSystemPromptChange}
        onSystemPromptAdd={handleSystemPromptAdd}
        onSystemPromptRemove={handleSystemPromptRemove}
      />

      {/* ダウンロードボタン */}
      <DownloadButton onDownload={handleDownload} />
    </Layout>
  )
}

export default ConfigGenerator
