import { useState, useCallback, useEffect } from 'react'
import type { Settings, LlmSettings, SpecType, SystemPromptPreset, ReviewerConfig } from '../types'
import { PRESET_CATALOG, DEFAULT_PRESET_ID } from '../data/presetCatalog'

const STORAGE_KEY = 'reviewer-settings'

// デフォルトのLLM設定
const DEFAULT_LLM_SETTINGS: LlmSettings = {
  provider: 'bedrock',
  maxTokens: 10000,
  models: [],
  selectedModel: undefined,
}

// デフォルトプリセットをカタログから取得
const defaultPreset = PRESET_CATALOG.find((p) => p.id === DEFAULT_PRESET_ID)

// デフォルトの設計書種別（カタログのデフォルトプリセットから取得）
const DEFAULT_SPEC_TYPES: SpecType[] = defaultPreset?.specTypes ?? []

// デフォルトのシステムプロンプト（カタログのデフォルトプリセットから取得）
const DEFAULT_SYSTEM_PROMPTS: SystemPromptPreset[] = defaultPreset
  ? [
      {
        name: defaultPreset.name,
        role: defaultPreset.systemPrompt.role,
        purpose: defaultPreset.systemPrompt.purpose,
        format: defaultPreset.systemPrompt.format,
        notes: defaultPreset.systemPrompt.notes,
      },
    ]
  : []

const DEFAULT_SETTINGS: Settings = {
  llm: DEFAULT_LLM_SETTINGS,
  specTypes: DEFAULT_SPEC_TYPES,
  systemPrompts: DEFAULT_SYSTEM_PROMPTS,
}

interface UseSettingsReturn {
  settings: Settings
  updateLlmSettings: (llm: Partial<LlmSettings>) => void
  updateSpecTypes: (specTypes: SpecType[]) => void
  updateSystemPrompts: (prompts: SystemPromptPreset[]) => void
  loadFromConfig: (config: ReviewerConfig) => void
  saveToStorage: () => void
  clearStorage: () => void
  isModified: boolean
}

export function useSettings(): UseSettingsReturn {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS)
  const [isModified, setIsModified] = useState(false)

  // 初期読み込み
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const parsed = JSON.parse(saved) as Partial<Settings>
        setSettings({
          llm: { ...DEFAULT_LLM_SETTINGS, ...parsed.llm },
          specTypes: parsed.specTypes || DEFAULT_SPEC_TYPES,
          systemPrompts: parsed.systemPrompts || DEFAULT_SYSTEM_PROMPTS,
        })
      } catch {
        // パース失敗時はデフォルト値を使用
      }
    }
  }, [])

  const updateLlmSettings = useCallback((llm: Partial<LlmSettings>) => {
    setSettings((prev) => ({
      ...prev,
      llm: { ...prev.llm, ...llm },
    }))
    setIsModified(true)
  }, [])

  const updateSpecTypes = useCallback((specTypes: SpecType[]) => {
    setSettings((prev) => ({ ...prev, specTypes }))
    setIsModified(true)
  }, [])

  const updateSystemPrompts = useCallback((prompts: SystemPromptPreset[]) => {
    setSettings((prev) => ({ ...prev, systemPrompts: prompts }))
    setIsModified(true)
  }, [])

  const loadFromConfig = useCallback((config: ReviewerConfig) => {
    setSettings((prev) => ({
      llm: config.llm ? { ...prev.llm, ...config.llm } : prev.llm,
      specTypes: config.specTypes || prev.specTypes,
      systemPrompts: config.systemPrompts || prev.systemPrompts,
    }))
    setIsModified(true)
  }, [])

  const saveToStorage = useCallback(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
    setIsModified(false)
  }, [settings])

  const clearStorage = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
    setSettings(DEFAULT_SETTINGS)
    setIsModified(false)
  }, [])

  return {
    settings,
    updateLlmSettings,
    updateSpecTypes,
    updateSystemPrompts,
    loadFromConfig,
    saveToStorage,
    clearStorage,
    isModified,
  }
}

export { DEFAULT_SPEC_TYPES, DEFAULT_SYSTEM_PROMPTS, DEFAULT_LLM_SETTINGS }
