import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useReviewExecution } from '@features/reviewer/hooks/useReviewExecution'

// APIモジュールのモック
vi.mock('@features/reviewer/services/api', () => ({
  executeReview: vi.fn(),
}))

import * as api from '@features/reviewer/services/api'

describe('useReviewExecution', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('初期状態', () => {
    it('reviewResultsは[null, null]', () => {
      const { result } = renderHook(() => useReviewExecution())
      expect(result.current.reviewResults).toEqual([null, null])
    })

    it('isReviewingはfalse', () => {
      const { result } = renderHook(() => useReviewExecution())
      expect(result.current.isReviewing).toBe(false)
    })

    it('currentExecutionNumberは0', () => {
      const { result } = renderHook(() => useReviewExecution())
      expect(result.current.currentExecutionNumber).toBe(0)
    })

    it('currentTabは1', () => {
      const { result } = renderHook(() => useReviewExecution())
      expect(result.current.currentTab).toBe(1)
    })

    it('reviewErrorはnull', () => {
      const { result } = renderHook(() => useReviewExecution())
      expect(result.current.reviewError).toBe(null)
    })
  })

  describe('getSimpleJudgment', () => {
    it('空のレポートはunknownステータス', () => {
      const { result } = renderHook(() => useReviewExecution())
      const judgment = result.current.getSimpleJudgment('')
      expect(judgment.status).toBe('unknown')
      expect(judgment.ngCount).toBe(0)
      expect(judgment.warningCount).toBe(0)
      expect(judgment.okCount).toBe(0)
    })

    it('NGキーワードがあればngステータス', () => {
      const { result } = renderHook(() => useReviewExecution())
      const report = '項目1: NG\n項目2: NG\n項目3: OK'
      const judgment = result.current.getSimpleJudgment(report)
      expect(judgment.status).toBe('ng')
      expect(judgment.ngCount).toBe(2)
      expect(judgment.okCount).toBe(1)
    })

    it('❌絵文字もNGとしてカウント', () => {
      const { result } = renderHook(() => useReviewExecution())
      const report = '項目1: ❌\n項目2: ❌\n項目3: ✅'
      const judgment = result.current.getSimpleJudgment(report)
      expect(judgment.status).toBe('ng')
      expect(judgment.ngCount).toBe(2)
      expect(judgment.okCount).toBe(1)
    })

    it('要確認キーワードがあればwarningステータス', () => {
      const { result } = renderHook(() => useReviewExecution())
      const report = '項目1: 要確認\n項目2: OK'
      const judgment = result.current.getSimpleJudgment(report)
      expect(judgment.status).toBe('warning')
      expect(judgment.warningCount).toBe(1)
      expect(judgment.okCount).toBe(1)
    })

    it('⚠️絵文字も警告としてカウント', () => {
      const { result } = renderHook(() => useReviewExecution())
      const report = '項目1: ⚠️\n項目2: ✅'
      const judgment = result.current.getSimpleJudgment(report)
      expect(judgment.status).toBe('warning')
      expect(judgment.warningCount).toBe(1)
      expect(judgment.okCount).toBe(1)
    })

    it('NGも警告もなければokステータス', () => {
      const { result } = renderHook(() => useReviewExecution())
      const report = '項目1: OK\n項目2: OK\n項目3: ✅'
      const judgment = result.current.getSimpleJudgment(report)
      expect(judgment.status).toBe('ok')
      expect(judgment.ngCount).toBe(0)
      expect(judgment.warningCount).toBe(0)
      expect(judgment.okCount).toBe(3)
    })

    it('NGが警告より優先される', () => {
      const { result } = renderHook(() => useReviewExecution())
      const report = '項目1: NG\n項目2: 要確認\n項目3: OK'
      const judgment = result.current.getSimpleJudgment(report)
      expect(judgment.status).toBe('ng')
      expect(judgment.ngCount).toBe(1)
      expect(judgment.warningCount).toBe(1)
      expect(judgment.okCount).toBe(1)
    })
  })

  describe('parseMappingResult', () => {
    it('空文字列はnullを返す', () => {
      const { result } = renderHook(() => useReviewExecution())
      expect(result.current.parseMappingResult('')).toBeNull()
    })

    it('無効なJSONはnullを返す', () => {
      const { result } = renderHook(() => useReviewExecution())
      expect(result.current.parseMappingResult('これはJSONではない')).toBeNull()
    })

    it('filesプロパティがないJSONはnullを返す', () => {
      const { result } = renderHook(() => useReviewExecution())
      expect(result.current.parseMappingResult('{"data": []}')).toBeNull()
    })

    it('正しいJSON応答をパースできる', () => {
      const { result } = renderHook(() => useReviewExecution())
      const json = JSON.stringify({
        files: [
          {
            designFile: 'spec.xlsx',
            items: [
              { designItem: '1.1 ログイン', implementationElement: 'login()', implementationLocation: 'auth.ts:10-20', confidence: '高', note: '' },
              { designItem: '1.2 セッション', implementationElement: '-', implementationLocation: '-', confidence: '-', note: '未実装' },
            ],
          },
        ],
      })
      const parsed = result.current.parseMappingResult(json)
      expect(parsed).not.toBeNull()
      expect(parsed!.files).toHaveLength(1)
      expect(parsed!.files[0].items).toHaveLength(2)
    })

    it('```json ブロックからJSONを抽出できる', () => {
      const { result } = renderHook(() => useReviewExecution())
      const rawOutput = '```json\n{"files": [{"designFile": "spec.xlsx", "items": []}]}\n```'
      const parsed = result.current.parseMappingResult(rawOutput)
      expect(parsed).not.toBeNull()
      expect(parsed!.files).toHaveLength(1)
    })
  })

  describe('calculateMappingSummary', () => {
    it('全項目マッピング済みでカバレッジ100%', () => {
      const { result } = renderHook(() => useReviewExecution())
      const mappingResult = {
        files: [{
          designFile: 'spec.xlsx',
          items: [
            { designItem: '1.1', implementationElement: 'func()', implementationLocation: 'file.ts:1', confidence: '高' as const, note: '' },
            { designItem: '1.2', implementationElement: 'func2()', implementationLocation: 'file.ts:10', confidence: '中' as const, note: '' },
          ],
        }],
      }
      const summary = result.current.calculateMappingSummary(mappingResult)
      expect(summary.designItemCount).toBe(2)
      expect(summary.mappedCount).toBe(2)
      expect(summary.unmappedCount).toBe(0)
      expect(summary.coveragePercent).toBe(100)
    })

    it('未マッピング項目はconfidence="-"で判定', () => {
      const { result } = renderHook(() => useReviewExecution())
      const mappingResult = {
        files: [{
          designFile: 'spec.xlsx',
          items: [
            { designItem: '1.1', implementationElement: 'func()', implementationLocation: 'file.ts:1', confidence: '高' as const, note: '' },
            { designItem: '1.2', implementationElement: '-', implementationLocation: '-', confidence: '-' as const, note: '未実装' },
          ],
        }],
      }
      const summary = result.current.calculateMappingSummary(mappingResult)
      expect(summary.designItemCount).toBe(2)
      expect(summary.mappedCount).toBe(1)
      expect(summary.unmappedCount).toBe(1)
      expect(summary.coveragePercent).toBe(50)
    })

    it('複数ファイルの項目を合算', () => {
      const { result } = renderHook(() => useReviewExecution())
      const mappingResult = {
        files: [
          {
            designFile: 'spec1.xlsx',
            items: [
              { designItem: '1.1', implementationElement: 'func()', implementationLocation: 'file.ts:1', confidence: '高' as const, note: '' },
            ],
          },
          {
            designFile: 'spec2.xlsx',
            items: [
              { designItem: '2.1', implementationElement: '-', implementationLocation: '-', confidence: '-' as const, note: '未実装' },
              { designItem: '2.2', implementationElement: '-', implementationLocation: '-', confidence: '-' as const, note: '未実装' },
            ],
          },
        ],
      }
      const summary = result.current.calculateMappingSummary(mappingResult)
      expect(summary.designItemCount).toBe(3)
      expect(summary.mappedCount).toBe(1)
      expect(summary.unmappedCount).toBe(2)
      expect(summary.coveragePercent).toBe(33) // Math.round(33.33...)
    })

    it('項目数0でカバレッジ0%', () => {
      const { result } = renderHook(() => useReviewExecution())
      const mappingResult = { files: [] }
      const summary = result.current.calculateMappingSummary(mappingResult)
      expect(summary.designItemCount).toBe(0)
      expect(summary.coveragePercent).toBe(0)
    })
  })

  describe('executeReview with mode parameter', () => {
    const mockReviewParams = {
      specFiles: [{ filename: 'spec.xlsx', file: new File([''], 'spec.xlsx'), isMain: true, type: '設計書', tool: 'markitdown' }],
      codeFiles: [{ filename: 'Main.java', file: new File([''], 'Main.java') }],
      specMarkdown: '# 設計書',
      codeWithLineNumbers: '1: public class Main {}',
      systemPrompt: { role: '', purpose: '', format: '', notes: '' },
    }

    it('デフォルトモードはreview', async () => {
      const mockExecuteReview = api.executeReview as ReturnType<typeof vi.fn>
      mockExecuteReview.mockResolvedValue({
        success: true,
        report: 'レビュー結果',
        reviewMeta: {
          version: '0.9.0',
          modelId: 'test-model',
          executedAt: '2026-02-10',
          inputTokens: 100,
          outputTokens: 50,
          designs: [],
          programs: [],
        },
      })

      const { result } = renderHook(() => useReviewExecution())

      await act(async () => {
        await result.current.executeReview(mockReviewParams)
      })

      // 最初の呼び出しでmodeがreviewであることを確認
      expect(mockExecuteReview).toHaveBeenCalledWith(
        expect.objectContaining({
          mode: 'review',
          useStructureMap: false,
        })
      )
    })

    it('マッピングモードでのレビュー実行', async () => {
      const mockExecuteReview = api.executeReview as ReturnType<typeof vi.fn>
      mockExecuteReview.mockResolvedValue({
        success: true,
        report: 'マッピング結果',
        reviewMeta: {
          version: '0.9.0',
          modelId: 'test-model',
          executedAt: '2026-02-10',
          inputTokens: 100,
          outputTokens: 50,
          designs: [],
          programs: [],
        },
      })

      const { result } = renderHook(() => useReviewExecution())

      await act(async () => {
        await result.current.executeReview({
          ...mockReviewParams,
          mode: 'mapping',
          useStructureMap: true,
          structureMap: {
            documentMap: [{ id: 'MD1', section: '概要', level: 1, path: '概要', original_file: 'spec.md', original_start_line: 1, original_end_line: 10, word_count: 100, part_file: 'part1.md', checksum: 'abc123' }],
            codeMaps: [{ filename: 'Main.java', entries: [{ id: 'CD1', symbol: 'Main', type: 'class', original_file: 'Main.java', original_start_line: 1, original_end_line: 20, part_file: 'part1.java', checksum: 'def456' }] }],
          },
        })
      })

      expect(mockExecuteReview).toHaveBeenCalledWith(
        expect.objectContaining({
          mode: 'mapping',
          useStructureMap: true,
          structureMap: expect.objectContaining({
            documentMap: expect.any(Array),
            codeMaps: expect.any(Array),
          }),
        })
      )
    })

    it('useStructureMap=falseの場合、structureMapは渡されない', async () => {
      const mockExecuteReview = api.executeReview as ReturnType<typeof vi.fn>
      mockExecuteReview.mockResolvedValue({
        success: true,
        report: 'レビュー結果',
        reviewMeta: {
          version: '0.9.0',
          modelId: 'test-model',
          executedAt: '2026-02-10',
          inputTokens: 100,
          outputTokens: 50,
          designs: [],
          programs: [],
        },
      })

      const { result } = renderHook(() => useReviewExecution())

      await act(async () => {
        await result.current.executeReview({
          ...mockReviewParams,
          mode: 'review',
          useStructureMap: false,
          structureMap: {
            documentMap: [],
            codeMaps: [],
          },
        })
      })

      expect(mockExecuteReview).toHaveBeenCalledWith(
        expect.objectContaining({
          mode: 'review',
          useStructureMap: false,
          structureMap: undefined, // useStructureMap=falseならundefined
        })
      )
    })
  })

  describe('setCurrentTab', () => {
    it('タブを変更できる', () => {
      const { result } = renderHook(() => useReviewExecution())

      act(() => {
        result.current.setCurrentTab(2)
      })

      expect(result.current.currentTab).toBe(2)
    })
  })

  describe('clearResults', () => {
    it('結果をクリアできる', async () => {
      const mockExecuteReview = api.executeReview as ReturnType<typeof vi.fn>
      mockExecuteReview.mockResolvedValue({
        success: true,
        report: 'レビュー結果',
        reviewMeta: {
          version: '0.9.0',
          modelId: 'test-model',
          executedAt: '2026-02-10',
          inputTokens: 100,
          outputTokens: 50,
          designs: [],
          programs: [],
        },
      })

      const { result } = renderHook(() => useReviewExecution())

      // まずレビューを実行
      await act(async () => {
        await result.current.executeReview({
          specFiles: [],
          codeFiles: [],
          specMarkdown: '# test',
          codeWithLineNumbers: '1: test',
          systemPrompt: { role: '', purpose: '', format: '', notes: '' },
        })
      })

      // 結果をクリア
      act(() => {
        result.current.clearResults()
      })

      expect(result.current.reviewResults).toEqual([null, null])
      expect(result.current.currentTab).toBe(1)
      expect(result.current.reviewError).toBeNull()
    })
  })
})
