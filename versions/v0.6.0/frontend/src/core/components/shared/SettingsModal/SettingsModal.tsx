import type { ReactNode } from 'react'
import { Settings } from 'lucide-react'
import { Modal } from '../../ui/Modal'
import { ProgramInfoSection } from './ProgramInfoSection'
import { ConfigFileSection } from './ConfigFileSection'
import { LlmSettingsSection } from './LlmSettingsSection'
import { PromptPresetsSection } from './PromptPresetsSection'
import type { AppInfo, LlmSettings, SystemPromptPreset } from '../../../types'

interface SettingsModalSections {
  programInfo?: boolean
  configFile?: boolean
  llmSettings?: boolean
  promptPresets?: boolean
}

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
  appInfo: AppInfo
  sections?: SettingsModalSections
  // 設定ファイルセクション用
  onConfigFileLoad?: (content: string, filename: string) => void
  onSaveToStorage?: () => void
  onClearStorage?: () => void
  loadedConfigFilename?: string
  configLoadStatus?: {
    llm?: string
    specTypes?: string
    prompts?: string
  }
  configGeneratorUrl?: string
  // LLM設定セクション用
  llmSettings?: LlmSettings
  onModelChange?: (model: string) => void
  onTestConnection?: () => Promise<boolean>
  isSystemFallback?: boolean
  // プロンプトプリセットセクション用
  systemPromptPresets?: SystemPromptPreset[]
  // 拡張セクション
  extensionSections?: ReactNode[]
}

const defaultSections: SettingsModalSections = {
  programInfo: true,
  configFile: true,
  llmSettings: true,
  promptPresets: true,
}

export function SettingsModal({
  isOpen,
  onClose,
  appInfo,
  sections = defaultSections,
  onConfigFileLoad,
  onSaveToStorage,
  onClearStorage,
  loadedConfigFilename,
  configLoadStatus,
  configGeneratorUrl,
  llmSettings,
  onModelChange,
  onTestConnection,
  isSystemFallback,
  systemPromptPresets = [],
  extensionSections,
}: SettingsModalProps) {
  const mergedSections = { ...defaultSections, ...sections }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={<span className="flex items-center gap-2"><Settings className="w-5 h-5" /> 設定</span>}>
      {/* プログラム情報 */}
      {mergedSections.programInfo && <ProgramInfoSection appInfo={appInfo} />}

      {/* 設定ファイル */}
      {mergedSections.configFile &&
        onConfigFileLoad &&
        onSaveToStorage &&
        onClearStorage && (
          <ConfigFileSection
            onFileLoad={onConfigFileLoad}
            onSaveToBrowser={onSaveToStorage}
            onClearSaved={onClearStorage}
            loadedFilename={loadedConfigFilename}
            loadStatus={configLoadStatus}
            generatorUrl={configGeneratorUrl}
          />
        )}

      {/* LLM設定 */}
      {mergedSections.llmSettings &&
        llmSettings &&
        onModelChange &&
        onTestConnection && (
          <LlmSettingsSection
            settings={llmSettings}
            onModelChange={onModelChange}
            onTestConnection={onTestConnection}
            isSystemFallback={isSystemFallback}
          />
        )}

      {/* プロンプトプリセット */}
      {mergedSections.promptPresets && (
        <PromptPresetsSection presets={systemPromptPresets} />
      )}

      {/* 拡張セクション */}
      {extensionSections?.map((section, index) => (
        <div key={index}>{section}</div>
      ))}
    </Modal>
  )
}
