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

  describe('getSimpleMappingJudgment', () => {
    it('空のレポートはngステータスとゼロカウント', () => {
      const { result } = renderHook(() => useReviewExecution())
      const judgment = result.current.getSimpleMappingJudgment('')
      expect(judgment.status).toBe('ng')
      expect(judgment.designItemCount).toBe(0)
      expect(judgment.mappedCount).toBe(0)
      expect(judgment.unmappedCount).toBe(0)
      expect(judgment.coveragePercent).toBe(0)
    })

    it('マッピングテーブルの行数をカウント', () => {
      const { result } = renderHook(() => useReviewExecution())
      const report = `# マッピング結果

## マッピング一覧
| 設計書項目 | 設計内容 | 実装ファイル:行 | 実装要素 | 確信度 | 備考 |
|-----------|---------|----------------|---------|-------|------|
| 1.1 | ログイン機能 | auth.ts:10-20 | login() | 高 | - |
| 1.2 | ログアウト機能 | auth.ts:30-40 | logout() | 高 | - |
| 1.3 | セッション管理 | session.ts:5-15 | manage() | 中 | 要確認 |

## 未マッピング項目
なし
`
      const judgment = result.current.getSimpleMappingJudgment(report)
      expect(judgment.mappedCount).toBe(3)
      expect(judgment.designItemCount).toBe(3)
      expect(judgment.coveragePercent).toBe(100)
      expect(judgment.status).toBe('ok')
    })

    it('未マッピング項目のリストをカウント', () => {
      const { result } = renderHook(() => useReviewExecution())
      const report = `# マッピング結果

## マッピング一覧
| 設計書項目 | 設計内容 | 実装ファイル:行 | 実装要素 | 確信度 | 備考 |
|-----------|---------|----------------|---------|-------|------|
| 1.1 | ログイン機能 | auth.ts:10-20 | login() | 高 | - |
| 1.2 | ログアウト機能 | auth.ts:30-40 | logout() | 高 | - |

## 未マッピング項目
- 1.3 セッション管理
- 1.4 権限チェック
`
      const judgment = result.current.getSimpleMappingJudgment(report)
      expect(judgment.mappedCount).toBe(2)
      expect(judgment.unmappedCount).toBe(2)
      expect(judgment.designItemCount).toBe(4)
      expect(judgment.coveragePercent).toBe(50)
      expect(judgment.status).toBe('warning')
    })

    it('「特定できなかった」キーワードからもカウント', () => {
      const { result } = renderHook(() => useReviewExecution())
      const report = `# マッピング結果

## マッピング一覧
| 設計書項目 | 設計内容 | 実装ファイル:行 | 実装要素 | 確信度 | 備考 |
|-----------|---------|----------------|---------|-------|------|
| 1.1 | ログイン機能 | auth.ts:10-20 | login() | 高 | - |

以下の項目は実装箇所を特定できなかった:
- 項目A: 特定できなかった
- 項目B: 特定できなかった
- 項目C: 特定できなかった
`
      const judgment = result.current.getSimpleMappingJudgment(report)
      expect(judgment.mappedCount).toBe(1)
      // 「特定できなかった」が3回出現
      expect(judgment.unmappedCount).toBeGreaterThanOrEqual(3)
    })

    it('カバレッジ100%でokステータス', () => {
      const { result } = renderHook(() => useReviewExecution())
      const report = `## マッピング一覧
| 設計書項目 | 設計内容 | 実装ファイル:行 | 実装要素 | 確信度 | 備考 |
|-----------|---------|----------------|---------|-------|------|
| 1.1 | 機能A | file.ts:1-10 | funcA() | 高 | - |
`
      const judgment = result.current.getSimpleMappingJudgment(report)
      expect(judgment.coveragePercent).toBe(100)
      expect(judgment.status).toBe('ok')
    })

    it('カバレッジ0%以上100%未満でwarningステータス', () => {
      const { result } = renderHook(() => useReviewExecution())
      const report = `## マッピング一覧
| 設計書項目 | 設計内容 | 実装ファイル:行 | 実装要素 | 確信度 | 備考 |
|-----------|---------|----------------|---------|-------|------|
| 1.1 | 機能A | file.ts:1-10 | funcA() | 高 | - |

## 未マッピング項目
- 1.2 機能B
`
      const judgment = result.current.getSimpleMappingJudgment(report)
      expect(judgment.coveragePercent).toBe(50)
      expect(judgment.status).toBe('warning')
    })

    it('カバレッジ0%でngステータス', () => {
      const { result } = renderHook(() => useReviewExecution())
      const report = `## マッピング一覧
| 設計書項目 | 設計内容 | 実装ファイル:行 | 実装要素 | 確信度 | 備考 |
|-----------|---------|----------------|---------|-------|------|

## 未マッピング項目
- すべての項目が特定できなかった
`
      const judgment = result.current.getSimpleMappingJudgment(report)
      expect(judgment.mappedCount).toBe(0)
      // テーブルデータ行がないので coveragePercent は 0
      expect(judgment.status).toBe('ng')
    })

    it('設計項目数0でもngステータス', () => {
      const { result } = renderHook(() => useReviewExecution())
      const report = '# 空のレポート\n\n何も見つかりませんでした。'
      const judgment = result.current.getSimpleMappingJudgment(report)
      expect(judgment.designItemCount).toBe(0)
      expect(judgment.coveragePercent).toBe(0)
      expect(judgment.status).toBe('ng')
    })

    it('カバレッジ率は整数に丸められる', () => {
      const { result } = renderHook(() => useReviewExecution())
      // 3項目中1つマッピング = 33.333...%
      const report = `## マッピング一覧
| 設計書項目 | 設計内容 | 実装ファイル:行 | 実装要素 | 確信度 | 備考 |
|-----------|---------|----------------|---------|-------|------|
| 1.1 | 機能A | file.ts:1-10 | funcA() | 高 | - |

## 未マッピング項目
- 1.2 機能B
- 1.3 機能C
`
      const judgment = result.current.getSimpleMappingJudgment(report)
      expect(judgment.mappedCount).toBe(1)
      expect(judgment.unmappedCount).toBe(2)
      expect(judgment.designItemCount).toBe(3)
      expect(judgment.coveragePercent).toBe(33) // Math.round(33.33...)
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
