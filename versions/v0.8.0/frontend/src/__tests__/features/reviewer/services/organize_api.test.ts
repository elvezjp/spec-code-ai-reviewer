import { describe, it, expect, vi, beforeEach } from 'vitest'
import { organizeMarkdown } from '@features/reviewer/services/api'

// fetchのモック
global.fetch = vi.fn()

describe('organizeMarkdown', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('正常系: 整理成功', async () => {
    const mockResponse = {
      success: true,
      organizedMarkdown: '# 整理済みMarkdown\n[ref:S1-P1] 内容',
      warnings: [],
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    const result = await organizeMarkdown({
      markdown: '# 元のMarkdown\n内容',
      policy: '要件/条件/例外で整理してください。',
    })

    expect(result.success).toBe(true)
    expect(result.organizedMarkdown).toBe(mockResponse.organizedMarkdown)
    expect(result.warnings).toEqual([])
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/organize-markdown',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
    )
  })

  it('警告あり: 整理成功だが警告が返る', async () => {
    const mockResponse = {
      success: true,
      organizedMarkdown: '# 整理済みMarkdown',
      warnings: [
        { code: 'ref_missing', message: '一部の項目に参照IDが付与されていません' },
      ],
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    const result = await organizeMarkdown({
      markdown: '# 元のMarkdown',
      policy: '要件/条件/例外で整理してください。',
    })

    expect(result.success).toBe(true)
    expect(result.warnings).toHaveLength(1)
    expect(result.warnings?.[0].code).toBe('ref_missing')
  })

  it('エラー: APIエラー', async () => {
    const mockResponse = {
      success: false,
      error: 'APIエラーが発生しました',
      errorCode: 'api_error',
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    const result = await organizeMarkdown({
      markdown: '# 元のMarkdown',
      policy: '要件/条件/例外で整理してください。',
    })

    expect(result.success).toBe(false)
    expect(result.error).toBe('APIエラーが発生しました')
    expect(result.errorCode).toBe('api_error')
  })

  it('エラー: トークン超過', async () => {
    const mockResponse = {
      success: false,
      error: '入力が長すぎます。章単位で分割してください。',
      errorCode: 'token_limit',
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    const result = await organizeMarkdown({
      markdown: '# 元のMarkdown',
      policy: '要件/条件/例外で整理してください。',
    })

    expect(result.success).toBe(false)
    expect(result.errorCode).toBe('token_limit')
  })

  it('ソース情報とLLM設定を含むリクエスト', async () => {
    const mockResponse = {
      success: true,
      organizedMarkdown: '# 整理済みMarkdown',
      warnings: [],
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    await organizeMarkdown({
      markdown: '# 元のMarkdown',
      policy: '要件/条件/例外で整理してください。',
      source: {
        filename: 'test.xlsx',
        tool: 'excel2md',
      },
      llmConfig: {
        provider: 'anthropic',
        model: 'claude-sonnet-4-20250514',
        maxTokens: 16384,
        apiKey: 'test-key',
      },
    })

    const callArgs = (global.fetch as any).mock.calls[0]
    const requestBody = JSON.parse(callArgs[1].body)

    expect(requestBody.source).toEqual({
      filename: 'test.xlsx',
      tool: 'excel2md',
    })
    expect(requestBody.llmConfig).toEqual({
      provider: 'anthropic',
      model: 'claude-sonnet-4-20250514',
      maxTokens: 16384,
      apiKey: 'test-key',
    })
  })

  it('ネットワークエラー時の処理', async () => {
    ;(global.fetch as any).mockRejectedValueOnce(new Error('Network error'))

    await expect(
      organizeMarkdown({
        markdown: '# 元のMarkdown',
        policy: '要件/条件/例外で整理してください。',
      })
    ).rejects.toThrow('Network error')
  })
})
