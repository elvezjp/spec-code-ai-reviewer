import { useState, useCallback, useEffect } from 'react'
import type { LlmConfig, SystemPromptValues } from '../types'
import type { SpecType, SystemPromptPreset, ReviewerConfig, LlmSettings } from '@core/types'
import {
  DEFAULT_SPEC_TYPES,
  DEFAULT_SYSTEM_PROMPTS,
  DEFAULT_LLM_SETTINGS,
} from '@core/hooks/useSettings'

export interface ConfigLoadStatus {
  llm?: string
  specTypes?: string
  prompts?: string
}

interface UseReviewerSettingsReturn {
  // LLM settings
  llmConfig: LlmConfig | null
  selectedModel: string
  setSelectedModel: (model: string) => void

  // Spec types
  specTypesConfig: SpecType[]
  getTypeNote: (type: string) => string
  getSpecTypesList: () => string[]

  // System prompts
  systemPromptPresets: SystemPromptPreset[]
  selectedPreset: string
  currentPromptValues: SystemPromptValues
  selectPreset: (presetName: string) => void
  updatePromptValue: (field: keyof SystemPromptValues, value: string) => void

  // Config file
  reviewerConfig: ReviewerConfig | null
  configFilename: string | null
  configModified: boolean
  configLoadStatus: ConfigLoadStatus | null
  loadConfigFile: (file: File) => Promise<void>
  saveConfigToBrowser: () => void
  clearSavedConfig: () => void
  hasSavedConfig: () => boolean
}

const STORAGE_KEY = 'reviewer-config'
const SELECTED_PROMPT_KEY = 'selected-system-prompt'

export function useReviewerSettings(): UseReviewerSettingsReturn {
  const [reviewerConfig, setReviewerConfig] = useState<ReviewerConfig | null>(null)
  const [configFilename, setConfigFilename] = useState<string | null>(null)
  const [configModified, setConfigModified] = useState(false)
  const [configLoadStatus, setConfigLoadStatus] = useState<ConfigLoadStatus | null>(null)
  const [selectedModel, setSelectedModel] = useState('')
  const [selectedPreset, setSelectedPreset] = useState('')
  const [currentPromptValues, setCurrentPromptValues] = useState<SystemPromptValues>({
    role: '',
    purpose: '',
    format: '',
    notes: '',
  })

  // Derived values
  const specTypesConfig: SpecType[] =
    reviewerConfig?.specTypes && reviewerConfig.specTypes.length > 0
      ? reviewerConfig.specTypes
      : DEFAULT_SPEC_TYPES

  const systemPromptPresets: SystemPromptPreset[] =
    reviewerConfig?.systemPrompts && reviewerConfig.systemPrompts.length > 0
      ? reviewerConfig.systemPrompts
      : DEFAULT_SYSTEM_PROMPTS

  const llmConfig: LlmConfig | null = reviewerConfig?.llm?.provider
    ? {
        provider: reviewerConfig.llm.provider as LlmConfig['provider'],
        model: selectedModel || reviewerConfig.llm.models?.[0] || '',
        maxTokens: reviewerConfig.llm.maxTokens || DEFAULT_LLM_SETTINGS.maxTokens,
        apiKey: reviewerConfig.llm.apiKey,
        accessKeyId: reviewerConfig.llm.accessKeyId,
        secretAccessKey: reviewerConfig.llm.secretAccessKey,
        region: reviewerConfig.llm.region,
      }
    : null

  const getTypeNote = useCallback(
    (type: string): string => {
      const found = specTypesConfig.find((item) => item.type === type)
      if (found) return found.note
      const defaultFound = DEFAULT_SPEC_TYPES.find((item) => item.type === type)
      return defaultFound ? defaultFound.note : ''
    },
    [specTypesConfig]
  )

  const getSpecTypesList = useCallback((): string[] => {
    return specTypesConfig.map((item) => item.type)
  }, [specTypesConfig])

  const normalizePromptText = (text: string | undefined): string => {
    if (!text) return ''
    return String(text).replace(/<br\s*\/?>/gi, '\n')
  }

  const selectPreset = useCallback(
    (presetName: string) => {
      const preset =
        systemPromptPresets.find((p) => p.name === presetName) || systemPromptPresets[0]
      if (!preset) return

      setSelectedPreset(preset.name)
      setCurrentPromptValues({
        role: normalizePromptText(preset.role),
        purpose: normalizePromptText(preset.purpose),
        format: normalizePromptText(preset.format),
        notes: normalizePromptText(preset.notes),
      })
      localStorage.setItem(SELECTED_PROMPT_KEY, preset.name)
    },
    [systemPromptPresets]
  )

  const updatePromptValue = useCallback((field: keyof SystemPromptValues, value: string) => {
    setCurrentPromptValues((prev) => ({
      ...prev,
      [field]: value,
    }))
  }, [])

  const parseReviewerConfig = (content: string): ReviewerConfig => {
    const result: ReviewerConfig = {
      info: { version: '', created_at: '' },
      llm: undefined,
      specTypes: [],
      systemPrompts: [],
    }

    // Initialize LLM with partial values - will be completed during parsing
    const llmData: Partial<LlmSettings> = {
      models: [],
    }

    const llmKeyMap: Record<string, string> = {
      api_key: 'apiKey',
      access_key_id: 'accessKeyId',
      secret_access_key: 'secretAccessKey',
      max_tokens: 'maxTokens',
    }
    const normalizeLLMKey = (key: string) => llmKeyMap[key] || key

    const lines = content.split('\n')
    let currentSection: string | null = null
    let currentSubSection: string | null = null
    let inModels = false
    let currentPrompt: Partial<SystemPromptPreset> | null = null
    let currentPromptField: string | null = null
    let currentPromptFieldContent: string[] = []

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      const trimmed = line.trim()

      // Section header detection
      if (trimmed.startsWith('## ')) {
        // Save current prompt if exists
        if (currentPrompt && currentPrompt.name) {
          if (currentPromptField && currentPromptFieldContent.length > 0) {
            (currentPrompt as Record<string, unknown>)[currentPromptField] = currentPromptFieldContent.join('\n')
          }
          if (!result.systemPrompts) result.systemPrompts = []
          result.systemPrompts.push(currentPrompt as SystemPromptPreset)
          currentPrompt = null
          currentPromptField = null
          currentPromptFieldContent = []
        }

        currentSection = trimmed.substring(3).toLowerCase().trim()
        currentSubSection = null
        inModels = false
        continue
      }

      // Sub-section header detection
      if (trimmed.startsWith('### ')) {
        // Save current prompt if exists
        if (currentPrompt && currentPrompt.name) {
          if (currentPromptField && currentPromptFieldContent.length > 0) {
            (currentPrompt as Record<string, unknown>)[currentPromptField] = currentPromptFieldContent.join('\n')
          }
          if (!result.systemPrompts) result.systemPrompts = []
          result.systemPrompts.push(currentPrompt as SystemPromptPreset)
        }

        currentSubSection = trimmed.substring(4).trim()
        currentPromptField = null
        currentPromptFieldContent = []

        if (currentSection === 'systemprompts') {
          currentPrompt = { name: currentSubSection }
        }
        continue
      }

      // Field header detection for systemPrompts
      if (currentSection === 'systemprompts' && currentPrompt && trimmed.startsWith('#### ')) {
        // Save previous field
        if (currentPromptField && currentPromptFieldContent.length > 0) {
          (currentPrompt as Record<string, unknown>)[currentPromptField] = currentPromptFieldContent.join('\n')
        }

        const fieldName = trimmed.substring(5).toLowerCase().trim()
        currentPromptField = fieldName
        currentPromptFieldContent = []
        continue
      }

      // Collect field content for systemPrompts
      if (currentSection === 'systemprompts' && currentPrompt && currentPromptField) {
        if (trimmed !== '') {
          currentPromptFieldContent.push(line)
        } else if (currentPromptFieldContent.length > 0) {
          currentPromptFieldContent.push('')
        }
        continue
      }

      // LLM section
      if (currentSection === 'llm') {
        // モデルリスト項目の処理（  - model-name）
        if (inModels && trimmed.startsWith('- ')) {
          const model = trimmed.substring(2).trim()
          if (model && llmData.models) {
            llmData.models.push(model)
          }
          continue
        }

        // - models: の検出
        if (trimmed === '- models:') {
          inModels = true
          llmData.models = []
          continue
        }

        // 通常のプロパティ（- key: value）
        const match = trimmed.match(/^-\s*(\w+):\s*(.+)$/)
        if (match) {
          inModels = false
          const key = normalizeLLMKey(match[1])
          let value: string | number = match[2]

          if (key === 'maxTokens') {
            value = parseInt(value as string, 10)
          }
          (llmData as Record<string, unknown>)[key] = value
        }
      }

      // specTypes section
      if (currentSection === 'spectypes') {
        if (trimmed.startsWith('|') && !trimmed.includes('---')) {
          const cells = trimmed.split('|').map((c) => c.trim()).filter(Boolean)
          if (cells.length >= 2 && cells[0] !== '種別' && cells[0] !== 'type') {
            if (!result.specTypes) result.specTypes = []
            result.specTypes.push({
              type: cells[0],
              note: cells[1] || '',
            })
          }
        }
      }

      // info section
      if (currentSection === 'info') {
        if (trimmed.startsWith('- ')) {
          const keyValue = trimmed.substring(2)
          const colonIndex = keyValue.indexOf(':')
          if (colonIndex !== -1) {
            const key = keyValue.substring(0, colonIndex).trim()
            const value = keyValue.substring(colonIndex + 1).trim()
            if (!result.info) result.info = { version: '', created_at: '' }
            if (key === 'version') {
              result.info.version = value
            } else if (key === 'generated_at' || key === 'created_at') {
              result.info.created_at = value
            }
          }
        }
      }
    }

    // Save last prompt
    if (currentPrompt && currentPrompt.name) {
      if (currentPromptField && currentPromptFieldContent.length > 0) {
        (currentPrompt as Record<string, unknown>)[currentPromptField] = currentPromptFieldContent.join('\n')
      }
      if (!result.systemPrompts) result.systemPrompts = []
      result.systemPrompts.push(currentPrompt as SystemPromptPreset)
    }

    // Only set llm if provider is set
    if (llmData.provider) {
      result.llm = llmData as LlmSettings
    }

    return result
  }

  const loadConfigFile = useCallback(async (file: File) => {
    if (!file.name.endsWith('.md')) {
      throw new Error('Markdownファイル (.md) を選択してください')
    }

    const content = await file.text()
    const parsed = parseReviewerConfig(content)

    setReviewerConfig(parsed)
    setConfigFilename(file.name)
    setConfigModified(true)

    // 更新結果のステータスを生成
    const llmUpdated = !!(parsed.llm && parsed.llm.provider)
    const specUpdated = !!(parsed.specTypes && parsed.specTypes.length > 0)
    const promptsUpdated = !!(parsed.systemPrompts && parsed.systemPrompts.length > 0)

    setConfigLoadStatus({
      llm: llmUpdated
        ? '・LLM設定を更新しました'
        : '・LLM設定は更新されませんでした',
      specTypes: specUpdated
        ? '・設計書種別と注意事項を更新しました'
        : '・設計書種別と注意事項は更新されませんでした',
      prompts: promptsUpdated
        ? `・システムプロンプトプリセットを更新しました（${parsed.systemPrompts?.length}件）`
        : '・システムプロンプトプリセットは更新されませんでした',
    })

    // Set initial model if available
    if (parsed.llm?.models && parsed.llm.models.length > 0) {
      setSelectedModel(parsed.llm.models[0])
    }
  }, [])

  const saveConfigToBrowser = useCallback(() => {
    if (!reviewerConfig) return
    localStorage.setItem(STORAGE_KEY, JSON.stringify(reviewerConfig))
    setConfigModified(false)
  }, [reviewerConfig])

  const clearSavedConfig = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
    setReviewerConfig(null)
    setConfigFilename(null)
    setConfigModified(false)
    setConfigLoadStatus(null)
    setSelectedModel('')
  }, [])

  const hasSavedConfig = useCallback((): boolean => {
    return localStorage.getItem(STORAGE_KEY) !== null
  }, [])

  // Load saved config on mount
  useEffect(() => {
    const savedConfig = localStorage.getItem(STORAGE_KEY)
    if (savedConfig) {
      try {
        const parsed = JSON.parse(savedConfig) as ReviewerConfig
        setReviewerConfig(parsed)
        setConfigFilename('保存済み設定')
        setConfigModified(false)

        // 保存済み設定のステータスを生成
        const llmUpdated = !!(parsed.llm && parsed.llm.provider)
        const specUpdated = !!(parsed.specTypes && parsed.specTypes.length > 0)
        const promptsUpdated = !!(parsed.systemPrompts && parsed.systemPrompts.length > 0)

        setConfigLoadStatus({
          llm: llmUpdated
            ? '・LLM設定を読み込みました'
            : '・LLM設定は設定されていません',
          specTypes: specUpdated
            ? '・設計書種別と注意事項を読み込みました'
            : '・設計書種別と注意事項は設定されていません',
          prompts: promptsUpdated
            ? `・システムプロンプトプリセットを読み込みました（${parsed.systemPrompts?.length}件）`
            : '・システムプロンプトプリセットは設定されていません',
        })

        if (parsed.llm?.models && parsed.llm.models.length > 0) {
          setSelectedModel(parsed.llm.models[0])
        }
      } catch {
        // Ignore parse errors
      }
    }
  }, [])

  // Load saved preset selection and apply default preset
  useEffect(() => {
    if (systemPromptPresets.length > 0) {
      const savedPreset = localStorage.getItem(SELECTED_PROMPT_KEY)
      const presetToSelect =
        systemPromptPresets.find((p) => p.name === savedPreset)?.name ||
        systemPromptPresets[0].name
      selectPreset(presetToSelect)
    }
  }, [systemPromptPresets, selectPreset])

  return {
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
  }
}
