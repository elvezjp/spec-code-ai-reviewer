/**
 * Split API (v0.8.0) の単体テスト
 *
 * テストケース:
 * - UT-SPLA-001: splitMarkdown() - 正常系（基本的な分割）
 * - UT-SPLA-002: splitMarkdown() - 正常系（maxDepth指定）
 * - UT-SPLA-003: splitMarkdown() - セクションなし
 * - UT-SPLA-004: splitMarkdown() - エラー
 * - UT-SPLA-005: splitMarkdown() - ネットワークエラー
 * - UT-SPLA-006: splitCode() - 正常系（Python）
 * - UT-SPLA-007: splitCode() - 正常系（Java）
 * - UT-SPLA-008: splitCode() - シンボルなし
 * - UT-SPLA-009: splitCode() - エラー（未対応言語）
 * - UT-SPLA-010: splitCode() - ネットワークエラー
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { splitMarkdown, splitCode } from '@features/reviewer/services/api'

// fetchのモック
global.fetch = vi.fn()

describe('splitMarkdown', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('UT-SPLA-001: 正常系（基本的な分割）', async () => {
    const mockResponse = {
      success: true,
      parts: [
        {
          id: 'MD1',
          section: '概要',
          level: 1,
          path: '概要',
          startLine: 1,
          endLine: 10,
          content: '# 概要\n\nこれは概要です。',
          estimatedTokens: 50,
        },
        {
          id: 'MD2',
          section: '機能要件',
          level: 1,
          path: '機能要件',
          startLine: 11,
          endLine: 30,
          content: '# 機能要件\n\n機能の説明...',
          estimatedTokens: 100,
        },
      ],
      indexContent: '# INDEX\n\n- MD1: 概要\n- MD2: 機能要件\n',
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    const result = await splitMarkdown({
      content: '# 概要\n\nこれは概要です。\n\n# 機能要件\n\n機能の説明...',
      filename: 'design.md',
      maxDepth: 2,
    })

    expect(result.success).toBe(true)
    expect(result.parts).toHaveLength(2)
    expect(result.parts[0].id).toBe('MD1')
    expect(result.parts[0].section).toBe('概要')
    expect(result.parts[1].id).toBe('MD2')
    expect(result.indexContent).toContain('INDEX')
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/split/markdown',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
    )
  })

  it('UT-SPLA-002: 正常系（maxDepth指定）', async () => {
    const mockResponse = {
      success: true,
      parts: [
        {
          id: 'MD1',
          section: '第1章',
          level: 1,
          path: '第1章',
          startLine: 1,
          endLine: 5,
          content: '# 第1章',
          estimatedTokens: 20,
        },
        {
          id: 'MD2',
          section: '1.1 概要',
          level: 2,
          path: '第1章 > 1.1 概要',
          startLine: 6,
          endLine: 10,
          content: '## 1.1 概要',
          estimatedTokens: 30,
        },
        {
          id: 'MD3',
          section: '1.1.1 詳細',
          level: 3,
          path: '第1章 > 1.1 概要 > 1.1.1 詳細',
          startLine: 11,
          endLine: 15,
          content: '### 1.1.1 詳細',
          estimatedTokens: 25,
        },
      ],
      indexContent: '# INDEX\n\n- MD1: 第1章\n  - MD2: 1.1 概要\n    - MD3: 1.1.1 詳細\n',
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    const result = await splitMarkdown({
      content: '# 第1章\n\n## 1.1 概要\n\n### 1.1.1 詳細',
      filename: 'design.md',
      maxDepth: 3, // H3まで分割
    })

    expect(result.success).toBe(true)
    expect(result.parts).toHaveLength(3)
    expect(result.parts[2].level).toBe(3)

    // リクエストボディにmaxDepthが含まれていることを確認
    const callArgs = (global.fetch as any).mock.calls[0]
    const requestBody = JSON.parse(callArgs[1].body)
    expect(requestBody.maxDepth).toBe(3)
  })

  it('UT-SPLA-003: セクションなし', async () => {
    const mockResponse = {
      success: true,
      parts: [],
      indexContent: '# No sections found\n',
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    const result = await splitMarkdown({
      content: '見出しのないテキスト',
      filename: 'plain.md',
      maxDepth: 2,
    })

    expect(result.success).toBe(true)
    expect(result.parts).toHaveLength(0)
    expect(result.indexContent).toContain('No sections found')
  })

  it('UT-SPLA-004: エラー', async () => {
    const mockResponse = {
      success: false,
      parts: [],
      error: 'Markdown分割中にエラーが発生しました: Parse error',
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    const result = await splitMarkdown({
      content: '# 壊れたMarkdown',
      filename: 'broken.md',
      maxDepth: 2,
    })

    expect(result.success).toBe(false)
    expect(result.error).toContain('エラー')
  })

  it('UT-SPLA-005: ネットワークエラー', async () => {
    ;(global.fetch as any).mockRejectedValueOnce(new Error('Network error'))

    await expect(
      splitMarkdown({
        content: '# Markdown',
        filename: 'test.md',
        maxDepth: 2,
      })
    ).rejects.toThrow('Network error')
  })
})

describe('splitCode', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('UT-SPLA-006: 正常系（Python）', async () => {
    const mockResponse = {
      success: true,
      parts: [
        {
          id: 'CD1',
          symbol: 'UserService',
          symbolType: 'class',
          parentSymbol: null,
          startLine: 1,
          endLine: 50,
          content: 'class UserService:\n    def __init__(self):\n        pass',
          estimatedTokens: 200,
        },
        {
          id: 'CD2',
          symbol: 'create_user',
          symbolType: 'method',
          parentSymbol: 'UserService',
          startLine: 10,
          endLine: 25,
          content: '    def create_user(self, name):\n        pass',
          estimatedTokens: 80,
        },
      ],
      indexContent: '# CODE INDEX\n\n- CD1: UserService (class)\n  - CD2: create_user (method)\n',
      language: 'python',
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    const result = await splitCode({
      content: 'class UserService:\n    def create_user(self, name):\n        pass',
      filename: 'user_service.py',
    })

    expect(result.success).toBe(true)
    expect(result.language).toBe('python')
    expect(result.parts).toHaveLength(2)
    expect(result.parts[0].symbol).toBe('UserService')
    expect(result.parts[0].symbolType).toBe('class')
    expect(result.parts[1].symbol).toBe('create_user')
    expect(result.parts[1].parentSymbol).toBe('UserService')
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/split/code',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
    )
  })

  it('UT-SPLA-007: 正常系（Java）', async () => {
    const mockResponse = {
      success: true,
      parts: [
        {
          id: 'CD1',
          symbol: 'HelloWorld',
          symbolType: 'class',
          parentSymbol: null,
          startLine: 1,
          endLine: 10,
          content: 'public class HelloWorld { }',
          estimatedTokens: 150,
        },
        {
          id: 'CD2',
          symbol: 'main',
          symbolType: 'method',
          parentSymbol: 'HelloWorld',
          startLine: 2,
          endLine: 8,
          content: 'public static void main(String[] args) { }',
          estimatedTokens: 100,
        },
      ],
      indexContent: '# CODE INDEX\n\n- CD1: HelloWorld (class)\n  - CD2: main (method)\n',
      language: 'java',
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    const result = await splitCode({
      content: 'public class HelloWorld { public static void main(String[] args) { } }',
      filename: 'HelloWorld.java',
    })

    expect(result.success).toBe(true)
    expect(result.language).toBe('java')
    expect(result.parts).toHaveLength(2)
    expect(result.parts[0].symbol).toBe('HelloWorld')
    expect(result.parts[1].symbol).toBe('main')
    expect(result.parts[1].symbolType).toBe('method')
  })

  it('UT-SPLA-008: シンボルなし', async () => {
    const mockResponse = {
      success: true,
      parts: [],
      indexContent: '# No symbols found\n',
      language: 'python',
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    const result = await splitCode({
      content: '# コメントのみ\n# シンボルなし',
      filename: 'empty.py',
    })

    expect(result.success).toBe(true)
    expect(result.parts).toHaveLength(0)
    expect(result.language).toBe('python')
    expect(result.indexContent).toContain('No symbols found')
  })

  it('UT-SPLA-009: エラー（未対応言語）', async () => {
    const mockResponse = {
      success: false,
      parts: [],
      error: '未対応の言語です: .js (対応: .py, .java)',
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      json: async () => mockResponse,
    })

    const result = await splitCode({
      content: 'console.log("hello");',
      filename: 'test.js',
    })

    expect(result.success).toBe(false)
    expect(result.error).toContain('未対応')
    expect(result.error).toContain('.js')
  })

  it('UT-SPLA-010: ネットワークエラー', async () => {
    ;(global.fetch as any).mockRejectedValueOnce(new Error('Connection refused'))

    await expect(
      splitCode({
        content: 'def hello(): pass',
        filename: 'test.py',
      })
    ).rejects.toThrow('Connection refused')
  })
})
