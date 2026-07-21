/**
 * API レスポンスチェックの単体テスト
 *
 * テストケース:
 * - UT-ARCK-001: assertResponseOk() - 2xx レスポンスで何もスローしない
 * - UT-ARCK-002: assertResponseOk() - 404 レスポンスでエラーをスロー
 * - UT-ARCK-003: assertResponseOk() - 405 レスポンスでエラーをスロー（ボディ付き）
 * - UT-ARCK-004: assertResponseOk() - 500 レスポンスでエラーをスロー
 * - UT-ARCK-005: assertResponseOk() - ボディ読み取り失敗時もエラーをスロー
 * - UT-ARCK-006: fetchHeadings() - 200 正常レスポンス
 * - UT-ARCK-007: fetchHeadings() - 405 レスポンスでエラーオブジェクトを返す
 * - UT-ARCK-008: fetchHeadings() - 500 レスポンスでエラーオブジェクトを返す
 * - UT-ARCK-009: splitMarkdown() - 500 レスポンスでエラーをスロー
 * - UT-ARCK-010: splitCode() - 500 レスポンスでエラーをスロー
 * - UT-ARCK-011: executeStructureMatching() - 500 レスポンスでエラーをスロー
 * - UT-ARCK-012: executeGroupReview() - 500 レスポンスでエラーをスロー
 * - UT-ARCK-013: executeIntegrate() - 500 レスポンスでエラーをスロー
 * - UT-ARCK-014: executeSummarize() - 500 レスポンスでエラーをスロー
 * - UT-ARCK-015: convertExcelToMarkdown() - 500 レスポンスでエラーをスロー
 * - UT-ARCK-016: addLineNumbers() - 500 レスポンスでエラーをスロー
 * - UT-ARCK-017: executeReview() - 500 レスポンスでエラーをスロー
 * - UT-ARCK-018: testLlmConnection() - 500 レスポンスでエラーをスロー
 * - UT-ARCK-019: organizeMarkdown() - 500 レスポンスでエラーをスロー
 * - UT-ARCK-020: fetchHealth() - 正常レスポンス
 * - UT-ARCK-021: fetchHealth() - 非2xxレスポンスでnullを返す
 * - UT-ARCK-022: fetchHealth() - ネットワークエラーでnullを返す
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  assertResponseOk,
  fetchHealth,
  fetchHeadings,
  splitMarkdown,
  splitCode,
  executeStructureMatching,
  executeGroupReview,
  executeIntegrate,
  executeSummarize,
  convertExcelToMarkdown,
  addLineNumbers,
  executeReview,
  testLlmConnection,
  organizeMarkdown,
} from '@features/reviewer/services/api'

// fetchのモック
global.fetch = vi.fn()

describe('assertResponseOk', () => {
  it('UT-ARCK-001: 2xx レスポンスで何もスローしない', async () => {
    const response = new Response('ok', { status: 200 })
    await expect(assertResponseOk(response, 'テスト')).resolves.toBeUndefined()
  })

  it('UT-ARCK-002: 404 レスポンスでエラーをスロー', async () => {
    const response = new Response('Not Found', { status: 404 })
    await expect(assertResponseOk(response, 'リソース取得に失敗しました')).rejects.toThrow(
      'リソース取得に失敗しました (HTTP 404: Not Found)'
    )
  })

  it('UT-ARCK-003: 405 レスポンスでエラーをスロー（ボディ付き）', async () => {
    const response = new Response('Method Not Allowed', { status: 405 })
    await expect(assertResponseOk(response, '処理に失敗しました')).rejects.toThrow(
      '処理に失敗しました (HTTP 405: Method Not Allowed)'
    )
  })

  it('UT-ARCK-004: 500 レスポンスでエラーをスロー', async () => {
    const response = new Response('Internal Server Error', { status: 500 })
    await expect(assertResponseOk(response, 'サーバーエラー')).rejects.toThrow(
      'サーバーエラー (HTTP 500: Internal Server Error)'
    )
  })

  it('UT-ARCK-005: ボディが空でもエラーをスロー', async () => {
    const response = new Response('', { status: 502 })
    await expect(assertResponseOk(response, 'ゲートウェイエラー')).rejects.toThrow(
      'ゲートウェイエラー (HTTP 502)'
    )
  })
})

describe('fetchHeadings - response.ok チェック', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('UT-ARCK-006: 200 正常レスポンス', async () => {
    const mockResponse = {
      success: true,
      headings: [
        { title: '概要', level: 2, start_line: 1, end_line: 10, estimated_chars: 100 },
      ],
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    })

    const result = await fetchHeadings('# 概要\n\n内容')
    expect(result.headings).toHaveLength(1)
    expect(result.headings[0].title).toBe('概要')
    expect(result.error).toBeUndefined()
  })

  it('UT-ARCK-007: 405 レスポンスでエラーオブジェクトを返す', async () => {
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 405,
    })

    const result = await fetchHeadings('# テスト')
    expect(result.success).toBe(false)
    expect(result.headings).toEqual([])
    expect(result.error).toBe('見出し一覧の取得に失敗しました (HTTP 405)')
  })

  it('UT-ARCK-008: 500 レスポンスでエラーオブジェクトを返す', async () => {
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 500,
    })

    const result = await fetchHeadings('# テスト')
    expect(result.success).toBe(false)
    expect(result.headings).toEqual([])
    expect(result.error).toBe('見出し一覧の取得に失敗しました (HTTP 500)')
  })
})

describe('各 API 関数 - 非 2xx レスポンスでエラーをスロー', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mockErrorResponse = {
    ok: false,
    status: 500,
    text: async () => 'Internal Server Error',
  }

  it('UT-ARCK-009: splitMarkdown() - 500 レスポンス', async () => {
    ;(global.fetch as any).mockResolvedValueOnce(mockErrorResponse)
    await expect(
      splitMarkdown({ content: '# Test', filename: 'test.md', maxDepth: 2 })
    ).rejects.toThrow('分割処理に失敗しました (HTTP 500')
  })

  it('UT-ARCK-010: splitCode() - 500 レスポンス', async () => {
    ;(global.fetch as any).mockResolvedValueOnce(mockErrorResponse)
    await expect(
      splitCode({ content: 'def hello(): pass', filename: 'test.py' })
    ).rejects.toThrow('コード分割に失敗しました (HTTP 500')
  })

  it('UT-ARCK-011: executeStructureMatching() - 500 レスポンス', async () => {
    ;(global.fetch as any).mockResolvedValueOnce(mockErrorResponse)
    await expect(
      executeStructureMatching({
        document: { indexMd: '', mapJson: { sections: [] } },
        codeFiles: [],
      })
    ).rejects.toThrow('構造マッチングに失敗しました (HTTP 500')
  })

  it('UT-ARCK-012: executeGroupReview() - 500 レスポンス', async () => {
    ;(global.fetch as any).mockResolvedValueOnce(mockErrorResponse)
    await expect(
      executeGroupReview({
        groupId: 'g1',
        groupName: 'テスト',
        documentContent: '',
        codeContent: '',
      })
    ).rejects.toThrow('グループレビューに失敗しました (HTTP 500')
  })

  it('UT-ARCK-013: executeIntegrate() - 500 レスポンス', async () => {
    ;(global.fetch as any).mockResolvedValueOnce(mockErrorResponse)
    await expect(
      executeIntegrate({
        structureMatching: { success: true, totalGroups: 0, groups: [] },
        groupReviews: [],
      })
    ).rejects.toThrow('結果統合に失敗しました (HTTP 500')
  })

  it('UT-ARCK-014: executeSummarize() - 500 レスポンス', async () => {
    ;(global.fetch as any).mockResolvedValueOnce(mockErrorResponse)
    await expect(
      executeSummarize({
        text: 'テスト',
        targetType: 'design',
      })
    ).rejects.toThrow('要約処理に失敗しました (HTTP 500')
  })

  it('UT-ARCK-015: convertExcelToMarkdown() - 500 レスポンス', async () => {
    ;(global.fetch as any).mockResolvedValueOnce(mockErrorResponse)
    const file = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    await expect(
      convertExcelToMarkdown(file, 'markitdown')
    ).rejects.toThrow('Excel変換に失敗しました (HTTP 500')
  })

  it('UT-ARCK-016: addLineNumbers() - 500 レスポンス', async () => {
    ;(global.fetch as any).mockResolvedValueOnce(mockErrorResponse)
    const file = new File(['test'], 'test.py', { type: 'text/plain' })
    await expect(
      addLineNumbers(file)
    ).rejects.toThrow('行番号付与に失敗しました (HTTP 500')
  })

  it('UT-ARCK-017: executeReview() - 500 レスポンス', async () => {
    ;(global.fetch as any).mockResolvedValueOnce(mockErrorResponse)
    await expect(
      executeReview({
        designs: [],
        programs: [],
      } as any)
    ).rejects.toThrow('レビュー実行に失敗しました (HTTP 500')
  })

  it('UT-ARCK-018: testLlmConnection() - 500 レスポンス', async () => {
    ;(global.fetch as any).mockResolvedValueOnce(mockErrorResponse)
    await expect(
      testLlmConnection({})
    ).rejects.toThrow('接続テストに失敗しました (HTTP 500')
  })

  it('UT-ARCK-019: organizeMarkdown() - 500 レスポンス', async () => {
    ;(global.fetch as any).mockResolvedValueOnce(mockErrorResponse)
    await expect(
      organizeMarkdown({ markdown: '# Test', policy: 'test' })
    ).rejects.toThrow('マークダウン整形に失敗しました (HTTP 500')
  })
})

describe('fetchHealth', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('UT-ARCK-020: 正常レスポンス', async () => {
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'healthy', version: '0.9.6' }),
    })

    const result = await fetchHealth()
    expect(result.ok).toBe(true)
    if (result.ok) {
      expect(result.data).toEqual({ status: 'healthy', version: '0.9.6' })
    }
    expect(global.fetch).toHaveBeenCalledWith('/api/health')
  })

  it('UT-ARCK-021: 非2xxレスポンスでhttp_errorを返す', async () => {
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 404,
    })

    const result = await fetchHealth()
    expect(result.ok).toBe(false)
    if (!result.ok && result.reason === 'http_error') {
      expect(result.status).toBe(404)
    }
  })

  it('UT-ARCK-022: ネットワークエラーでnetwork_errorを返す', async () => {
    ;(global.fetch as any).mockRejectedValueOnce(new Error('Network error'))

    const result = await fetchHealth()
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.reason).toBe('network_error')
    }
  })
})

describe('testLlmConnection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('OpenAI互換APIのbaseUrlをPOST本文に含める', async () => {
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'connected', provider: 'openai', model: 'moonshot-v1-8k' }),
    })

    await testLlmConnection({
      provider: 'openai',
      model: 'moonshot-v1-8k',
      apiKey: 'test-key',
      baseUrl: 'https://api.moonshot.ai/v1',
    })

    expect(global.fetch).toHaveBeenCalledWith('/api/test-connection', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider: 'openai',
        model: 'moonshot-v1-8k',
        apiKey: 'test-key',
        baseUrl: 'https://api.moonshot.ai/v1',
      }),
    })
  })
})
