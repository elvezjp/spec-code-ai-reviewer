import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useSettings, DEFAULT_SPEC_TYPES, DEFAULT_SYSTEM_PROMPTS } from '@core/hooks/useSettings'

// localStorageのモック
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      store = {}
    }),
  }
})()

Object.defineProperty(window, 'localStorage', { value: localStorageMock })

describe('useSettings', () => {
  beforeEach(() => {
    localStorageMock.clear()
    vi.clearAllMocks()
  })

  it('初期状態でデフォルト設定を持つ', () => {
    const { result } = renderHook(() => useSettings())

    expect(result.current.settings.llm.provider).toBe('bedrock')
    expect(result.current.settings.llm.maxTokens).toBe(10000)
    expect(result.current.settings.specTypes).toEqual(DEFAULT_SPEC_TYPES)
    expect(result.current.settings.systemPrompts).toEqual(DEFAULT_SYSTEM_PROMPTS)
    expect(result.current.isModified).toBe(false)
  })

  it('updateLlmSettingsでLLM設定を更新できる', () => {
    const { result } = renderHook(() => useSettings())

    act(() => {
      result.current.updateLlmSettings({ provider: 'anthropic', maxTokens: 5000 })
    })

    expect(result.current.settings.llm.provider).toBe('anthropic')
    expect(result.current.settings.llm.maxTokens).toBe(5000)
    expect(result.current.isModified).toBe(true)
  })

  it('updateSpecTypesで設計書種別を更新できる', () => {
    const { result } = renderHook(() => useSettings())

    const newSpecTypes = [{ type: 'カスタム種別', note: 'カスタム注意事項' }]

    act(() => {
      result.current.updateSpecTypes(newSpecTypes)
    })

    expect(result.current.settings.specTypes).toEqual(newSpecTypes)
    expect(result.current.isModified).toBe(true)
  })

  it('updateSystemPromptsでシステムプロンプトを更新できる', () => {
    const { result } = renderHook(() => useSettings())

    const newPrompts = [
      {
        name: 'カスタムプリセット',
        role: 'カスタムロール',
        purpose: 'カスタム目的',
        format: 'カスタムフォーマット',
        notes: 'カスタム注意事項',
      },
    ]

    act(() => {
      result.current.updateSystemPrompts(newPrompts)
    })

    expect(result.current.settings.systemPrompts).toEqual(newPrompts)
    expect(result.current.isModified).toBe(true)
  })

  it('saveToStorageでlocalStorageに保存される', () => {
    const { result } = renderHook(() => useSettings())

    act(() => {
      result.current.updateLlmSettings({ provider: 'openai' })
    })

    act(() => {
      result.current.saveToStorage()
    })

    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'reviewer-settings',
      expect.stringContaining('"provider":"openai"')
    )
    expect(result.current.isModified).toBe(false)
  })

  it('clearStorageでlocalStorageがクリアされデフォルトに戻る', () => {
    const { result } = renderHook(() => useSettings())

    act(() => {
      result.current.updateLlmSettings({ provider: 'openai' })
    })

    act(() => {
      result.current.clearStorage()
    })

    expect(localStorageMock.removeItem).toHaveBeenCalledWith('reviewer-settings')
    expect(result.current.settings.llm.provider).toBe('bedrock')
    expect(result.current.isModified).toBe(false)
  })

  it('loadFromConfigで設定を読み込める', () => {
    const { result } = renderHook(() => useSettings())

    const config = {
      llm: { provider: 'anthropic' as const, maxTokens: 8000, models: ['claude-3-5-sonnet'] },
      specTypes: [{ type: '新種別', note: '新注意事項' }],
    }

    act(() => {
      result.current.loadFromConfig(config)
    })

    expect(result.current.settings.llm.provider).toBe('anthropic')
    expect(result.current.settings.llm.maxTokens).toBe(8000)
    expect(result.current.settings.specTypes).toEqual(config.specTypes)
    expect(result.current.isModified).toBe(true)
  })
})
