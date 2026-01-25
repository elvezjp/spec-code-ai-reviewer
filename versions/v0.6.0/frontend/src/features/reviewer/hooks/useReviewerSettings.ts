import { useState, useCallback, useEffect, useMemo } from 'react'
import type { LlmConfig, SystemPromptValues } from '../types'
import type { SpecType, SystemPromptPreset, ReviewerConfig, LlmSettings, Preset } from '@core/types'
import {
  DEFAULT_SPEC_TYPES,
  DEFAULT_SYSTEM_PROMPTS,
  DEFAULT_LLM_SETTINGS,
} from '@core/hooks/useSettings'
import { PRESET_CATALOG } from '@core/data/presetCatalog'

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
  applyPreset: (preset: Preset) => void
}

const STORAGE_KEY = 'reviewer-config'
const SELECTED_MODEL_KEY = 'selected-model'
const SELECTED_PROMPT_KEY = 'selected-system-prompt'

// 最初の:でのみ分割（モデル名に:が含まれる場合に対応）
const parseSelectedModelKey = (key: string): { provider: string; model: string } | null => {
  const firstColonIndex = key.indexOf(':')
  if (firstColonIndex === -1) return null
  return {
    provider: key.substring(0, firstColonIndex),
    model: key.substring(firstColonIndex + 1),
  }
}

export function useReviewerSettings(): UseReviewerSettingsReturn {
  const [reviewerConfig, setReviewerConfig] = useState<ReviewerConfig | null>(null)
  const [configFilename, setConfigFilename] = useState<string | null>(null)
  const [configModified, setConfigModified] = useState(false)
  const [configLoadStatus, setConfigLoadStatus] = useState<ConfigLoadStatus | null>(null)
  const [selectedModel, setSelectedModelState] = useState('')
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

  // システムプロンプトプリセット: 標準レビュープリセット（デフォルト） + カタログ + 設定ファイル
  const systemPromptPresets: SystemPromptPreset[] = useMemo(() => {
    // デフォルトプリセット（先頭に配置）
    const defaultPreset = DEFAULT_SYSTEM_PROMPTS[0]

    // プリセットカタログからSystemPromptPresetに変換
    const catalogPresets: SystemPromptPreset[] = PRESET_CATALOG.map((preset) => ({
      name: preset.name,
      role: preset.systemPrompt.role,
      purpose: preset.systemPrompt.purpose,
      format: preset.systemPrompt.format,
      notes: preset.systemPrompt.notes,
    }))

    // 設定ファイルのプリセット
    const configPrompts = reviewerConfig?.systemPrompts && reviewerConfig.systemPrompts.length > 0
      ? reviewerConfig.systemPrompts
      : []

    // 統合: デフォルトプリセット → カタログ → 設定ファイル
    const allPrompts = [
      ...(defaultPreset ? [defaultPreset] : []),
      ...catalogPresets,
      ...configPrompts,
    ]

    // 同名プリセットは先勝ちで重複排除
    return allPrompts.filter((item, index, array) => {
      return array.findIndex(entry => entry.name === item.name) === index
    })
  }, [reviewerConfig])

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

  // モデル選択変更時にlocalStorageにも保存
  const setSelectedModel = useCallback(
    (model: string) => {
      setSelectedModelState(model)
      // プロバイダーとモデルをセットで保存（v0.5.2互換）
      if (model && reviewerConfig?.llm?.provider) {
        localStorage.setItem(SELECTED_MODEL_KEY, `${reviewerConfig.llm.provider}:${model}`)
      }
    },
    [reviewerConfig?.llm?.provider]
  )

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

    // 設定ファイルのプリセット名にサフィックスを付けて、プリセットカタログとの衝突を回避
    if (result.systemPrompts && result.systemPrompts.length > 0) {
      result.systemPrompts = result.systemPrompts.map(preset => ({
        ...preset,
        name: `${preset.name} (設定ファイル)`,
      }))
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

    // 保存済みのモデル選択を復元、なければ最初のモデルを選択
    if (parsed.llm?.models && parsed.llm.models.length > 0) {
      const savedModelKey = localStorage.getItem(SELECTED_MODEL_KEY)
      let modelToSelect = parsed.llm.models[0] // デフォルトは最初のモデル

      if (savedModelKey) {
        const parsed_model = parseSelectedModelKey(savedModelKey)
        // プロバイダーが一致し、モデルリストに含まれている場合のみ復元
        if (parsed_model && parsed_model.provider === parsed.llm.provider && parsed.llm.models.includes(parsed_model.model)) {
          modelToSelect = parsed_model.model
        }
      }
      setSelectedModelState(modelToSelect)
    }
  }, [])

  const saveConfigToBrowser = useCallback(() => {
    if (!reviewerConfig) return
    localStorage.setItem(STORAGE_KEY, JSON.stringify(reviewerConfig))
    setConfigModified(false)
  }, [reviewerConfig])

  const applyPreset = useCallback(
    (preset: Preset) => {
      const systemPromptPreset: SystemPromptPreset = {
        name: preset.name,
        role: preset.systemPrompt.role,
        purpose: preset.systemPrompt.purpose,
        format: preset.systemPrompt.format,
        notes: preset.systemPrompt.notes,
      }

      // デフォルトプリセットを必ず保持
      const defaultPreset = DEFAULT_SYSTEM_PROMPTS[0]
      const basePrompts =
        reviewerConfig?.systemPrompts && reviewerConfig.systemPrompts.length > 0
          ? reviewerConfig.systemPrompts.filter(
              p => p.name !== defaultPreset?.name && p.name !== systemPromptPreset.name
            )
          : []

      // 適用するプリセットを先頭に、デフォルトプリセットを2番目に配置
      const mergedPrompts = (defaultPreset
        ? [systemPromptPreset, defaultPreset, ...basePrompts]
        : [systemPromptPreset, ...basePrompts]
      ).filter((item, index, array) => {
        return array.findIndex(entry => entry.name === item.name) === index
      })

      const nextConfig: ReviewerConfig = {
        info: reviewerConfig?.info || { version: '', created_at: '' },
        llm: reviewerConfig?.llm,
        specTypes: preset.specTypes,
        systemPrompts: mergedPrompts,
      }

      setReviewerConfig(nextConfig)
      setConfigFilename(`プリセット: ${preset.name}`)
      setConfigLoadStatus({
        llm: nextConfig.llm?.provider
          ? '・LLM設定は保持されました'
          : '・LLM設定は設定されていません',
        specTypes: `・設計書種別を更新しました（${preset.specTypes.length}件）`,
        prompts: `・システムプロンプトをプリセットで更新しました（${mergedPrompts.length}件）`,
      })
      setConfigModified(false)

      setSelectedPreset(systemPromptPreset.name)
      setCurrentPromptValues({
        role: systemPromptPreset.role,
        purpose: systemPromptPreset.purpose,
        format: systemPromptPreset.format,
        notes: systemPromptPreset.notes,
      })

      localStorage.setItem(STORAGE_KEY, JSON.stringify(nextConfig))
      localStorage.setItem(SELECTED_PROMPT_KEY, systemPromptPreset.name)
    },
    [reviewerConfig]
  )

  const clearSavedConfig = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(SELECTED_MODEL_KEY)
    localStorage.removeItem(SELECTED_PROMPT_KEY)
    setReviewerConfig(null)
    setConfigFilename(null)
    setConfigModified(false)
    setConfigLoadStatus(null)
    setSelectedModelState('')
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

        // 保存済みのモデル選択を復元
        if (parsed.llm?.models && parsed.llm.models.length > 0) {
          const savedModelKey = localStorage.getItem(SELECTED_MODEL_KEY)
          let modelToSelect = parsed.llm.models[0] // デフォルトは最初のモデル

          if (savedModelKey) {
            const parsed_model = parseSelectedModelKey(savedModelKey)
            // プロバイダーが一致し、モデルリストに含まれている場合のみ復元
            if (parsed_model && parsed_model.provider === parsed.llm.provider && parsed.llm.models.includes(parsed_model.model)) {
              modelToSelect = parsed_model.model
            }
          }
          setSelectedModelState(modelToSelect)
        }

        // 保存済みのプリセット選択を復元
        // 設定ファイルのプリセットを含めた全プリセットリストを構築して検索
        const savedPreset = localStorage.getItem(SELECTED_PROMPT_KEY)
        if (savedPreset) {
          // デフォルトプリセット
          const defaultPreset = DEFAULT_SYSTEM_PROMPTS[0]
          // プリセットカタログからSystemPromptPresetに変換
          const catalogPresets: SystemPromptPreset[] = PRESET_CATALOG.map((preset) => ({
            name: preset.name,
            role: preset.systemPrompt.role,
            purpose: preset.systemPrompt.purpose,
            format: preset.systemPrompt.format,
            notes: preset.systemPrompt.notes,
          }))
          // 設定ファイルのプリセット
          const configPrompts = parsed.systemPrompts && parsed.systemPrompts.length > 0
            ? parsed.systemPrompts
            : []
          // 全プリセットリスト: デフォルトプリセット → カタログ → 設定ファイル
          const allPresets = [
            ...(defaultPreset ? [defaultPreset] : []),
            ...catalogPresets,
            ...configPrompts,
          ]
          const exists = allPresets.some((p) => p.name === savedPreset)
          if (exists) {
            const preset = allPresets.find((p) => p.name === savedPreset)
            if (preset) {
              setSelectedPreset(preset.name)
              setCurrentPromptValues({
                role: normalizePromptText(preset.role),
                purpose: normalizePromptText(preset.purpose),
                format: normalizePromptText(preset.format),
                notes: normalizePromptText(preset.notes),
              })
            }
          }
        }
      } catch {
        // Ignore parse errors
      }
    }
  }, [])

  // Load saved preset selection and apply default preset
  // 設定ファイルがない場合のみ実行（設定ファイルがある場合は上のuseEffectで処理済み）
  useEffect(() => {
    // 設定ファイルが保存されている場合は、上のuseEffectで処理されるのでスキップ
    const savedConfig = localStorage.getItem(STORAGE_KEY)
    if (savedConfig) return

    if (systemPromptPresets.length === 0 || selectedPreset) return

    const savedPreset = localStorage.getItem(SELECTED_PROMPT_KEY)
    if (savedPreset) {
      const exists = systemPromptPresets.some((p) => p.name === savedPreset)
      if (exists) {
        selectPreset(savedPreset)
        return
      }
      // 保存されたプリセットが存在しない場合はフォールバック
    }

    // デフォルトとして最初のプリセットを選択
    selectPreset(systemPromptPresets[0].name)
  }, [systemPromptPresets, selectPreset, selectedPreset])

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
    applyPreset,
  }
}
