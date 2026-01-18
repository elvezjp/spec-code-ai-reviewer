import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useValidation } from '@features/config-generator/hooks/useValidation'
import type { ConfigFormState } from '@features/config-generator/types'

// テスト用のformState作成ヘルパー
function createFormState(overrides: Partial<ConfigFormState> = {}): ConfigFormState {
  return {
    provider: 'bedrock',
    llmFields: {
      provider: 'bedrock',
      maxTokens: 10000,
      models: ['claude-3-5-sonnet'],
      accessKeyId: 'test-key',
      secretAccessKey: 'test-secret',
      region: 'us-east-1',
    },
    specTypes: [{ type: '設計書', note: 'テスト' }],
    systemPrompts: [{ name: 'test', role: '', purpose: '', format: '', notes: '' }],
    ...overrides,
  }
}

describe('useValidation', () => {
  describe('初期状態', () => {
    it('errorsは空配列', () => {
      const { result } = renderHook(() => useValidation())
      expect(result.current.errors).toEqual([])
    })
  })

  describe('validate', () => {
    it('有効なformStateでエラーなし', () => {
      const { result } = renderHook(() => useValidation())

      let errors: unknown[]
      act(() => {
        errors = result.current.validate(createFormState())
      })

      expect(errors!).toEqual([])
    })

    it('必須フィールドが空の場合エラー', () => {
      const { result } = renderHook(() => useValidation())

      let errors: { field: string; message: string }[]
      act(() => {
        errors = result.current.validate(
          createFormState({
            llmFields: {
              provider: 'bedrock',
              maxTokens: 10000,
              models: [],
              accessKeyId: '', // 空
              secretAccessKey: 'test-secret',
              region: 'us-east-1',
            },
          })
        )
      })

      expect(errors!.some((e) => e.field === 'accessKeyId')).toBe(true)
    })

    it('openaiプロバイダーでapiKeyが必須', () => {
      const { result } = renderHook(() => useValidation())

      let errors: { field: string; message: string }[]
      act(() => {
        errors = result.current.validate(
          createFormState({
            provider: 'openai',
            llmFields: {
              provider: 'openai',
              maxTokens: 10000,
              models: ['gpt-4'],
              apiKey: '', // 空
            },
          })
        )
      })

      expect(errors!.some((e) => e.field === 'apiKey')).toBe(true)
    })
  })

  describe('clearErrors', () => {
    it('エラーをクリアできる', () => {
      const { result } = renderHook(() => useValidation())

      // まずエラーを発生させる
      act(() => {
        result.current.validate(
          createFormState({
            llmFields: {
              provider: 'bedrock',
              maxTokens: 10000,
              models: [],
              accessKeyId: '',
              secretAccessKey: '',
              region: '',
            },
          })
        )
      })

      expect(result.current.errors.length).toBeGreaterThan(0)

      // クリア
      act(() => {
        result.current.clearErrors()
      })

      expect(result.current.errors).toEqual([])
    })
  })

  describe('getFieldError', () => {
    it('特定フィールドのエラーメッセージを取得できる', () => {
      const { result } = renderHook(() => useValidation())

      act(() => {
        result.current.validate(
          createFormState({
            llmFields: {
              provider: 'bedrock',
              maxTokens: 10000,
              models: [],
              accessKeyId: '',
              secretAccessKey: 'test',
              region: 'us-east-1',
            },
          })
        )
      })

      expect(result.current.getFieldError('accessKeyId')).toBeDefined()
      expect(result.current.getFieldError('nonexistent')).toBeUndefined()
    })
  })
})
