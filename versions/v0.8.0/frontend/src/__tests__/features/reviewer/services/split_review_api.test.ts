/**
 * Split Review API (v0.8.0) の単体テスト
 *
 * テストケース:
 * - UT-SRVA-001: executeStructureMatching() - 正常系（基本的なマッチング）
 * - UT-SRVA-002: executeStructureMatching() - 正常系（複数グループ）
 * - UT-SRVA-003: executeStructureMatching() - エラー（JSON解析失敗）
 * - UT-SRVA-004: executeStructureMatching() - LLM設定あり
 * - UT-SRVA-005: executeStructureMatching() - ネットワークエラー
 * - UT-SRVA-006: executeGroupReview() - 正常系
 * - UT-SRVA-007: executeGroupReview() - カスタムシステムプロンプト
 * - UT-SRVA-008: executeGroupReview() - エラー
 * - UT-SRVA-009: executeGroupReview() - ネットワークエラー
 * - UT-SRVA-010: executeIntegrate() - 正常系
 * - UT-SRVA-011: executeIntegrate() - カスタムシステムプロンプト
 * - UT-SRVA-012: executeIntegrate() - エラー
 * - UT-SRVA-013: executeIntegrate() - ネットワークエラー
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  executeStructureMatching,
  executeGroupReview,
  executeIntegrate,
} from '@features/reviewer/services/api'

// fetchのモック
global.fetch = vi.fn()

describe('executeStructureMatching', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('UT-SRVA-001: 正常系（基本的なマッチング）', async () => {
    const mockResponse = {
      success: true,
      groups: [
        {
          groupId: 'group1',
          groupName: 'ユーザー管理',
          docSections: [
            { id: 'MD1', title: 'ユーザー管理機能', path: 'ユーザー管理機能' },
          ],
          codeSymbols: [
            { id: 'CD1', filename: 'user_service.py', symbol: 'UserService' },
          ],
          reason: 'ユーザー管理に関連する設計とコード',
          estimatedTokens: 500,
        },
      ],
      totalGroups: 1,
      tokensUsed: { input: 1000, output: 200 },
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    const result = await executeStructureMatching({
      document: {
        indexMd: '# INDEX\n- MD1: ユーザー管理機能',
        mapJson: { sections: [] },
      },
      codeFiles: [
        {
          filename: 'user_service.py',
          indexMd: '# CODE INDEX\n- CD1: UserService',
          mapJson: { symbols: [] },
        },
      ],
    })

    expect(result.success).toBe(true)
    expect(result.totalGroups).toBe(1)
    expect(result.groups).toHaveLength(1)
    expect(result.groups[0].groupId).toBe('group1')
    expect(result.groups[0].groupName).toBe('ユーザー管理')
    expect(result.groups[0].docSections).toHaveLength(1)
    expect(result.groups[0].codeSymbols).toHaveLength(1)
    expect(result.tokensUsed?.input).toBe(1000)
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/review/structure-matching',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
    )
  })

  it('UT-SRVA-002: 正常系（複数グループ）', async () => {
    const mockResponse = {
      success: true,
      groups: [
        {
          groupId: 'group1',
          groupName: 'ユーザー管理',
          docSections: [{ id: 'MD1', title: 'ユーザー管理', path: 'ユーザー管理' }],
          codeSymbols: [{ id: 'CD1', filename: 'user.py', symbol: 'User' }],
          reason: 'ユーザー管理',
          estimatedTokens: 300,
        },
        {
          groupId: 'group2',
          groupName: '認証機能',
          docSections: [{ id: 'MD2', title: '認証', path: '認証' }],
          codeSymbols: [{ id: 'CD2', filename: 'auth.py', symbol: 'Auth' }],
          reason: '認証機能',
          estimatedTokens: 400,
        },
      ],
      totalGroups: 2,
      tokensUsed: { input: 1500, output: 300 },
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    const result = await executeStructureMatching({
      document: {
        indexMd: '# INDEX',
        mapJson: { sections: [] },
      },
      codeFiles: [],
    })

    expect(result.success).toBe(true)
    expect(result.totalGroups).toBe(2)
    expect(result.groups).toHaveLength(2)
    expect(result.groups[0].groupName).toBe('ユーザー管理')
    expect(result.groups[1].groupName).toBe('認証機能')
  })

  it('UT-SRVA-003: エラー（JSON解析失敗）', async () => {
    const mockResponse = {
      success: false,
      groups: [],
      totalGroups: 0,
      error: 'AIの応答をJSONとして解析できませんでした: Unexpected token',
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    const result = await executeStructureMatching({
      document: {
        indexMd: '# INDEX',
        mapJson: { sections: [] },
      },
      codeFiles: [],
    })

    expect(result.success).toBe(false)
    expect(result.error).toContain('JSON')
  })

  it('UT-SRVA-004: LLM設定あり', async () => {
    const mockResponse = {
      success: true,
      groups: [],
      totalGroups: 0,
      tokensUsed: { input: 500, output: 100 },
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    await executeStructureMatching({
      document: {
        indexMd: '# INDEX',
        mapJson: { sections: [] },
      },
      codeFiles: [],
      llmConfig: {
        provider: 'anthropic',
        model: 'claude-sonnet-4-20250514',
        maxTokens: 16384,
        apiKey: 'test-api-key',
      },
    })

    const callArgs = (global.fetch as any).mock.calls[0]
    const requestBody = JSON.parse(callArgs[1].body)

    expect(requestBody.llmConfig).toEqual({
      provider: 'anthropic',
      model: 'claude-sonnet-4-20250514',
      maxTokens: 16384,
      apiKey: 'test-api-key',
    })
  })

  it('UT-SRVA-005: ネットワークエラー', async () => {
    ;(global.fetch as any).mockRejectedValueOnce(new Error('Network error'))

    await expect(
      executeStructureMatching({
        document: {
          indexMd: '# INDEX',
          mapJson: { sections: [] },
        },
        codeFiles: [],
      })
    ).rejects.toThrow('Network error')
  })
})

describe('executeGroupReview', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('UT-SRVA-006: 正常系', async () => {
    const mockResponse = {
      success: true,
      groupId: 'group1',
      reviewResult: {
        report: '## サマリー\n\n整合性は概ね良好です。\n\n## 突合結果一覧\n\n| 設計書 | コード | 判定 |\n|--------|--------|------|\n| ユーザー登録 | register() | OK |',
      },
      tokensUsed: { input: 2000, output: 500 },
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    const result = await executeGroupReview({
      groupId: 'group1',
      groupName: 'ユーザー管理',
      documentContent: '### ユーザー登録 (L1-L20)\n\n## ユーザー登録\n\nユーザーを登録する機能',
      codeContent: '### user_service.py:register (method, L10-L25)\n\n```\ndef register(self, user):\n    # 登録処理\n```',
    })

    expect(result.success).toBe(true)
    expect(result.groupId).toBe('group1')
    expect(result.reviewResult?.report).toContain('サマリー')
    expect(result.tokensUsed?.input).toBe(2000)
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/review/group',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
    )
  })

  it('UT-SRVA-007: カスタムシステムプロンプト', async () => {
    const mockResponse = {
      success: true,
      groupId: 'group1',
      reviewResult: {
        report: 'カスタムフォーマットのレビュー結果',
      },
      tokensUsed: { input: 1500, output: 300 },
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    await executeGroupReview({
      groupId: 'group1',
      groupName: 'テストグループ',
      documentContent: '',
      codeContent: '',
      systemPrompt: {
        role: 'カスタムレビュアー',
        purpose: 'カスタム目的',
        format: 'カスタムフォーマット',
        notes: 'カスタム注意事項',
      },
    })

    const callArgs = (global.fetch as any).mock.calls[0]
    const requestBody = JSON.parse(callArgs[1].body)

    expect(requestBody.systemPrompt).toEqual({
      role: 'カスタムレビュアー',
      purpose: 'カスタム目的',
      format: 'カスタムフォーマット',
      notes: 'カスタム注意事項',
    })
  })

  it('UT-SRVA-008: エラー', async () => {
    const mockResponse = {
      success: false,
      groupId: 'group1',
      error: 'グループレビュー中にエラーが発生しました: API rate limit exceeded',
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    const result = await executeGroupReview({
      groupId: 'group1',
      groupName: 'テスト',
      documentContent: '',
      codeContent: '',
    })

    expect(result.success).toBe(false)
    expect(result.groupId).toBe('group1')
    expect(result.error).toContain('エラー')
  })

  it('UT-SRVA-009: ネットワークエラー', async () => {
    ;(global.fetch as any).mockRejectedValueOnce(new Error('Connection timeout'))

    await expect(
      executeGroupReview({
        groupId: 'group1',
        groupName: 'テスト',
        documentContent: '',
        codeContent: '',
      })
    ).rejects.toThrow('Connection timeout')
  })
})

describe('executeIntegrate', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('UT-SRVA-010: 正常系', async () => {
    const mockResponse = {
      success: true,
      report: '# 統合レビューレポート\n\n## 全体サマリー\n\n2グループのレビューを統合しました。',
      integratedReport: {
        overallSummary: 'レビュー対象: 2グループ',
        consistencyScore: 0.85,
        keyIssues: [],
        crossGroupIssues: [],
        statistics: { totalGroupsReviewed: 2 },
        deduplicatedFindings: [],
      },
      reviewMeta: {
        version: 'v0.8.0',
        modelId: 'claude-sonnet-4-20250514',
        provider: 'anthropic',
        executedAt: '2026-02-06T12:00:00Z',
        designs: [],
        programs: [],
        inputTokens: 3000,
        outputTokens: 800,
      },
      tokensUsed: { input: 3000, output: 800 },
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    const result = await executeIntegrate({
      structureMatching: {
        success: true,
        totalGroups: 2,
        groups: [
          { groupId: 'group1', groupName: 'ユーザー管理', docSections: [], codeSymbols: [], reason: '', estimatedTokens: 0 },
          { groupId: 'group2', groupName: '認証', docSections: [], codeSymbols: [], reason: '', estimatedTokens: 0 },
        ],
      },
      groupReviews: [
        {
          groupId: 'group1',
          groupName: 'ユーザー管理',
          report: 'ユーザー管理のレビュー結果',
        },
        {
          groupId: 'group2',
          groupName: '認証',
          report: '認証のレビュー結果',
        },
      ],
    })

    expect(result.success).toBe(true)
    expect(result.report).toContain('統合レビューレポート')
    expect(result.integratedReport?.overallSummary).toContain('2グループ')
    expect(result.reviewMeta?.version).toBe('v0.8.0')
    expect(result.tokensUsed?.input).toBe(3000)
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/review/integrate',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
    )
  })

  it('UT-SRVA-011: カスタムシステムプロンプト', async () => {
    const mockResponse = {
      success: true,
      report: 'カスタムフォーマットの統合レポート',
      integratedReport: {
        overallSummary: 'レビュー対象: 1グループ',
        consistencyScore: 0.9,
        keyIssues: [],
        crossGroupIssues: [],
        statistics: {},
        deduplicatedFindings: [],
      },
      tokensUsed: { input: 2000, output: 600 },
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    await executeIntegrate({
      structureMatching: { success: true, totalGroups: 0, groups: [] },
      groupReviews: [
        {
          groupId: 'group1',
          groupName: 'テスト',
          report: 'テストレポート',
        },
      ],
      systemPrompt: {
        role: 'カスタム統合者',
        purpose: 'カスタム統合目的',
        format: 'カスタム出力形式',
        notes: 'カスタム注意事項',
      },
    })

    const callArgs = (global.fetch as any).mock.calls[0]
    const requestBody = JSON.parse(callArgs[1].body)

    expect(requestBody.systemPrompt).toEqual({
      role: 'カスタム統合者',
      purpose: 'カスタム統合目的',
      format: 'カスタム出力形式',
      notes: 'カスタム注意事項',
    })
  })

  it('UT-SRVA-012: エラー', async () => {
    const mockResponse = {
      success: false,
      error: '結果統合中にエラーが発生しました: Service unavailable',
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    const result = await executeIntegrate({
      structureMatching: { success: true, totalGroups: 0, groups: [] },
      groupReviews: [],
    })

    expect(result.success).toBe(false)
    expect(result.error).toContain('エラー')
  })

  it('UT-SRVA-013: ネットワークエラー', async () => {
    ;(global.fetch as any).mockRejectedValueOnce(new Error('Service unavailable'))

    await expect(
      executeIntegrate({
        structureMatching: { success: true, totalGroups: 0, groups: [] },
        groupReviews: [],
      })
    ).rejects.toThrow('Service unavailable')
  })
})
