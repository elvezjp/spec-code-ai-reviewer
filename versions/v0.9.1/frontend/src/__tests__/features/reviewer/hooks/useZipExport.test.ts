import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useZipExport } from '@features/reviewer/hooks/useZipExport'
import type { SplitExportData } from '@features/reviewer/hooks/useZipExport'

// JSZipのモック
const mockZipFile = vi.fn()
const mockGenerateAsync = vi.fn().mockResolvedValue(new Blob(['mock']))

vi.mock('jszip', () => {
  const file = (...args: unknown[]) => mockZipFile(...args)
  const generateAsync = (...args: unknown[]) => mockGenerateAsync(...args)
  return {
    default: class {
      file = file
      generateAsync = generateAsync
    },
  }
})

// DOM APIのモック
const mockCreateObjectURL = vi.fn(() => 'blob:mock-url')
const mockRevokeObjectURL = vi.fn()
const mockClick = vi.fn()
const mockClipboardWriteText = vi.fn()

// 元のcreateElementを保存
const originalCreateElement = document.createElement.bind(document)

beforeEach(() => {
  vi.clearAllMocks()

  // URL APIのモック
  global.URL.createObjectURL = mockCreateObjectURL
  global.URL.revokeObjectURL = mockRevokeObjectURL

  // document.createElementのモック（aタグのみ）
  vi.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
    if (tagName === 'a') {
      return {
        href: '',
        download: '',
        click: mockClick,
        setAttribute: vi.fn(),
        style: {},
      } as unknown as HTMLAnchorElement
    }
    // それ以外は元の実装を使用
    return originalCreateElement(tagName)
  })

  // navigator.clipboardのモック
  Object.defineProperty(navigator, 'clipboard', {
    value: { writeText: mockClipboardWriteText },
    writable: true,
    configurable: true,
  })
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('useZipExport', () => {
  describe('downloadReport', () => {
    it('レポートをマークダウンファイルとしてダウンロードできる', () => {
      const { result } = renderHook(() => useZipExport())

      result.current.downloadReport('# Review Result', 1)

      expect(mockCreateObjectURL).toHaveBeenCalledWith(expect.any(Blob))
      expect(mockClick).toHaveBeenCalled()
      expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
    })
  })

  describe('copyReport', () => {
    it('レポートをクリップボードにコピーできる', async () => {
      const { result } = renderHook(() => useZipExport())

      await result.current.copyReport('# Review Result')

      expect(mockClipboardWriteText).toHaveBeenCalledWith('# Review Result')
    })
  })

  describe('downloadSpecMarkdown', () => {
    it('設計書マークダウンをダウンロードできる', () => {
      const { result } = renderHook(() => useZipExport())

      result.current.downloadSpecMarkdown('# Spec Markdown')

      expect(mockCreateObjectURL).toHaveBeenCalledWith(expect.any(Blob))
      expect(mockClick).toHaveBeenCalled()
      expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
    })
  })

  describe('downloadCodeWithLineNumbers', () => {
    it('行番号付きコードをダウンロードできる', () => {
      const { result } = renderHook(() => useZipExport())

      result.current.downloadCodeWithLineNumbers('1: function main() {}')

      expect(mockCreateObjectURL).toHaveBeenCalledWith(expect.any(Blob))
      expect(mockClick).toHaveBeenCalled()
      expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
    })
  })

  describe('downloadZip', () => {
    const mockReviewData = {
      systemPrompt: { role: 'レビュアー', purpose: '突合', format: 'Markdown', notes: '' },
      specMarkdown: '# 設計書',
      codeWithLineNumbers: '1: function main() {}',
      report: '# レビュー結果',
      reviewMeta: {
        version: 'v0.9.1',
        modelId: 'test-model',
        executedAt: '2026/03/13 14:30:00',
        inputTokens: 1000,
        outputTokens: 500,
      },
    }

    beforeEach(() => {
      mockZipFile.mockClear()
      mockGenerateAsync.mockClear()
    })

    it('分割レビュー時にグループレビュー個別結果がZIPに含まれる', async () => {
      const { result } = renderHook(() => useZipExport())
      const splitData: SplitExportData = {
        groupReviews: [
          { groupId: 'group1', groupName: 'ユーザー管理', report: '## サマリー\n\nグループ1の結果' },
          { groupId: 'group2', groupName: '注文処理', report: '## サマリー\n\nグループ2の結果' },
        ],
      }

      await act(async () => {
        await result.current.downloadZip(mockReviewData, 1, splitData)
      })

      expect(mockZipFile).toHaveBeenCalledWith('split/review-result-group1.md', '## サマリー\n\nグループ1の結果')
      expect(mockZipFile).toHaveBeenCalledWith('split/review-result-group2.md', '## サマリー\n\nグループ2の結果')
    })

    it('splitDataにgroupReviewsがない場合はグループレビューファイルが含まれない', async () => {
      const { result } = renderHook(() => useZipExport())
      const splitData: SplitExportData = {}

      await act(async () => {
        await result.current.downloadZip(mockReviewData, 1, splitData)
      })

      const fileNames = mockZipFile.mock.calls.map((call: unknown[]) => call[0] as string)
      expect(fileNames.filter((n: string) => n.includes('review-result-'))).toHaveLength(0)
    })
  })
})
