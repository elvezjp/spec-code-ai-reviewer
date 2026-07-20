import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useConfigState } from '@features/config-file-generator/hooks/useConfigState'

describe('useConfigState', () => {
  describe('初期状態', () => {
    it('デフォルトプロバイダーはbedrock', () => {
      const { result } = renderHook(() => useConfigState())
      expect(result.current.formState.provider).toBe('bedrock')
    })

    it('specTypesが初期化されている', () => {
      const { result } = renderHook(() => useConfigState())
      expect(result.current.formState.specTypes.length).toBeGreaterThan(0)
    })

    it('systemPromptsが初期化されている', () => {
      const { result } = renderHook(() => useConfigState())
      expect(result.current.formState.systemPrompts.length).toBeGreaterThan(0)
    })
  })

  describe('handleProviderChange', () => {
    it('プロバイダーを変更できる', () => {
      const { result } = renderHook(() => useConfigState())

      act(() => {
        result.current.handleProviderChange('anthropic')
      })

      expect(result.current.formState.provider).toBe('anthropic')
    })

    it('プロバイダー変更時にLLMフィールドがリセットされる', () => {
      const { result } = renderHook(() => useConfigState())

      // 初期値を変更
      act(() => {
        result.current.handleLlmFieldChange('maxTokens', 5000)
      })

      // プロバイダー変更
      act(() => {
        result.current.handleProviderChange('openai')
      })

      // リセットされているはず
      expect(result.current.formState.llmFields.provider).toBe('openai')
    })
  })

  describe('handleLlmFieldChange', () => {
    it('LLMフィールドを変更できる', () => {
      const { result } = renderHook(() => useConfigState())

      act(() => {
        result.current.handleLlmFieldChange('maxTokens', 5000)
      })

      expect(result.current.formState.llmFields.maxTokens).toBe(5000)
    })
  })

  describe('handleArrayItemChange', () => {
    it('配列アイテムを変更できる', () => {
      const { result } = renderHook(() => useConfigState())

      // まず配列にアイテムがあることを確認
      const initialLength = result.current.formState.llmFields.models.length
      expect(initialLength).toBeGreaterThan(0)

      act(() => {
        result.current.handleArrayItemChange(0, 'new-model')
      })

      expect(result.current.formState.llmFields.models[0]).toBe('new-model')
    })
  })

  describe('handleArrayItemAdd', () => {
    it('配列にアイテムを追加できる', () => {
      const { result } = renderHook(() => useConfigState())

      const initialLength = result.current.formState.llmFields.models.length

      act(() => {
        result.current.handleArrayItemAdd()
      })

      expect(result.current.formState.llmFields.models.length).toBe(initialLength + 1)
      expect(result.current.formState.llmFields.models[initialLength]).toBe('')
    })
  })

  describe('handleArrayItemRemove', () => {
    it('配列からアイテムを削除できる', () => {
      const { result } = renderHook(() => useConfigState())

      const initialLength = result.current.formState.llmFields.models.length

      act(() => {
        result.current.handleArrayItemRemove(0)
      })

      expect(result.current.formState.llmFields.models.length).toBe(initialLength - 1)
    })
  })

  describe('handleSpecTypeChange', () => {
    it('specTypeを変更できる', () => {
      const { result } = renderHook(() => useConfigState())

      act(() => {
        result.current.handleSpecTypeChange(0, 'type', '新しい種別')
      })

      expect(result.current.formState.specTypes[0].type).toBe('新しい種別')
    })

    it('noteフィールドを変更できる', () => {
      const { result } = renderHook(() => useConfigState())

      act(() => {
        result.current.handleSpecTypeChange(0, 'note', '新しい注意事項')
      })

      expect(result.current.formState.specTypes[0].note).toBe('新しい注意事項')
    })
  })

  describe('handleSpecTypeAdd', () => {
    it('specTypeを追加できる', () => {
      const { result } = renderHook(() => useConfigState())

      const initialLength = result.current.formState.specTypes.length

      act(() => {
        result.current.handleSpecTypeAdd()
      })

      expect(result.current.formState.specTypes.length).toBe(initialLength + 1)
      expect(result.current.formState.specTypes[initialLength]).toEqual({ type: '', note: '' })
    })
  })

  describe('handleSpecTypeRemove', () => {
    it('specTypeを削除できる', () => {
      const { result } = renderHook(() => useConfigState())

      const initialLength = result.current.formState.specTypes.length

      act(() => {
        result.current.handleSpecTypeRemove(0)
      })

      expect(result.current.formState.specTypes.length).toBe(initialLength - 1)
    })
  })

  describe('handleSystemPromptChange', () => {
    it('systemPromptを変更できる', () => {
      const { result } = renderHook(() => useConfigState())

      act(() => {
        result.current.handleSystemPromptChange(0, 'name', '新しいプリセット名')
      })

      expect(result.current.formState.systemPrompts[0].name).toBe('新しいプリセット名')
    })

    it('roleフィールドを変更できる', () => {
      const { result } = renderHook(() => useConfigState())

      act(() => {
        result.current.handleSystemPromptChange(0, 'role', '新しいロール')
      })

      expect(result.current.formState.systemPrompts[0].role).toBe('新しいロール')
    })
  })

  describe('handleSystemPromptAdd', () => {
    it('systemPromptを追加できる', () => {
      const { result } = renderHook(() => useConfigState())

      const initialLength = result.current.formState.systemPrompts.length

      act(() => {
        result.current.handleSystemPromptAdd()
      })

      expect(result.current.formState.systemPrompts.length).toBe(initialLength + 1)
      expect(result.current.formState.systemPrompts[initialLength]).toEqual({
        name: '',
        role: '',
        purpose: '',
        format: '',
        notes: '',
      })
    })
  })

  describe('handleSystemPromptRemove', () => {
    it('systemPromptを削除できる', () => {
      const { result } = renderHook(() => useConfigState())

      const initialLength = result.current.formState.systemPrompts.length

      act(() => {
        result.current.handleSystemPromptRemove(0)
      })

      expect(result.current.formState.systemPrompts.length).toBe(initialLength - 1)
    })
  })
})
