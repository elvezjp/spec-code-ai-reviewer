import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useSplitSettings } from '@features/reviewer/hooks/useSplitSettings'

// APIモジュールのモック
vi.mock('@features/reviewer/services/api', () => ({
  splitMarkdown: vi.fn(),
  splitCode: vi.fn(),
  executeSummarize: vi.fn(),
  fetchHeadings: vi.fn().mockResolvedValue({ success: true, headings: [] }),
}))

describe('useSplitSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('preExcludedSections state management', () => {
    it('初期状態でpreExcludedSectionsは空配列', () => {
      const { result } = renderHook(() => useSplitSettings())
      expect(result.current.preExcludedSections).toEqual([])
    })

    it('togglePreExcludedSectionで除外セクションを追加できる', () => {
      const { result } = renderHook(() => useSplitSettings())

      act(() => {
        result.current.togglePreExcludedSection(10)
      })

      expect(result.current.preExcludedSections).toContain(10)
    })

    it('togglePreExcludedSectionで既に含まれるセクションを除去できる', () => {
      const { result } = renderHook(() => useSplitSettings())

      act(() => {
        result.current.togglePreExcludedSection(10)
      })
      expect(result.current.preExcludedSections).toContain(10)

      act(() => {
        result.current.togglePreExcludedSection(10)
      })
      expect(result.current.preExcludedSections).not.toContain(10)
    })

    it('複数の除外セクションを追加できる', () => {
      const { result } = renderHook(() => useSplitSettings())

      act(() => {
        result.current.togglePreExcludedSection(10)
      })
      act(() => {
        result.current.togglePreExcludedSection(30)
      })

      expect(result.current.preExcludedSections).toEqual([10, 30])
    })
  })

  describe('排他制御: togglePreExcludedSection', () => {
    it('除外をONにすると同じセクションが事前重要から除外される', () => {
      const { result } = renderHook(() => useSplitSettings())

      // まず事前重要に追加
      act(() => {
        result.current.togglePreImportantSection(10)
      })
      expect(result.current.preImportantSections).toContain(10)

      // 同じセクションを事前除外に追加 → 事前重要から除外される
      act(() => {
        result.current.togglePreExcludedSection(10)
      })
      expect(result.current.preExcludedSections).toContain(10)
      expect(result.current.preImportantSections).not.toContain(10)
    })

    it('他のセクションの事前重要はそのまま維持される', () => {
      const { result } = renderHook(() => useSplitSettings())

      // 2つのセクションを事前重要に追加
      act(() => {
        result.current.togglePreImportantSection(10)
      })
      act(() => {
        result.current.togglePreImportantSection(20)
      })
      expect(result.current.preImportantSections).toEqual([10, 20])

      // セクション10のみ事前除外に追加
      act(() => {
        result.current.togglePreExcludedSection(10)
      })

      // セクション10は事前重要から除外、セクション20は維持
      expect(result.current.preImportantSections).toEqual([20])
      expect(result.current.preExcludedSections).toContain(10)
    })
  })

  describe('排他制御: togglePreImportantSection', () => {
    it('重要をONにすると同じセクションが事前除外から除外される', () => {
      const { result } = renderHook(() => useSplitSettings())

      // まず事前除外に追加
      act(() => {
        result.current.togglePreExcludedSection(10)
      })
      expect(result.current.preExcludedSections).toContain(10)

      // 同じセクションを事前重要に追加 → 事前除外から除外される
      act(() => {
        result.current.togglePreImportantSection(10)
      })
      expect(result.current.preImportantSections).toContain(10)
      expect(result.current.preExcludedSections).not.toContain(10)
    })

    it('他のセクションの事前除外はそのまま維持される', () => {
      const { result } = renderHook(() => useSplitSettings())

      // 2つのセクションを事前除外に追加
      act(() => {
        result.current.togglePreExcludedSection(10)
      })
      act(() => {
        result.current.togglePreExcludedSection(20)
      })
      expect(result.current.preExcludedSections).toEqual([10, 20])

      // セクション10のみ事前重要に追加
      act(() => {
        result.current.togglePreImportantSection(10)
      })

      // セクション10は事前除外から除外、セクション20は維持
      expect(result.current.preExcludedSections).toEqual([20])
      expect(result.current.preImportantSections).toContain(10)
    })
  })

  describe('DEFAULT_PRE_IMPORTANT_SPLIT_SETTINGS defaults', () => {
    it('preImportantSplitSettingsの初期値にsummaryMode: "ai"が含まれる', () => {
      const { result } = renderHook(() => useSplitSettings())
      expect(result.current.preImportantSplitSettings.summaryMode).toBe('ai')
    })

    it('preImportantSplitSettingsの初期値にsummaryMaxChars: 300が含まれる', () => {
      const { result } = renderHook(() => useSplitSettings())
      expect(result.current.preImportantSplitSettings.summaryMaxChars).toBe(300)
    })

    it('preImportantSplitSettingsの初期値にmaxSubsections: 5が含まれる', () => {
      const { result } = renderHook(() => useSplitSettings())
      expect(result.current.preImportantSplitSettings.maxSubsections).toBe(5)
    })

    it('normalSplitSettingsも同じデフォルト値を持つ', () => {
      const { result } = renderHook(() => useSplitSettings())
      expect(result.current.normalSplitSettings.summaryMode).toBe('ai')
      expect(result.current.normalSplitSettings.summaryMaxChars).toBe(100)
      expect(result.current.normalSplitSettings.maxSubsections).toBe(5)
    })
  })

  describe('clearHeadingsCache', () => {
    it('clearHeadingsCacheでpreExcludedSectionsもクリアされる', () => {
      const { result } = renderHook(() => useSplitSettings())

      act(() => {
        result.current.togglePreExcludedSection(10)
      })
      act(() => {
        result.current.togglePreImportantSection(20)
      })
      expect(result.current.preExcludedSections).toEqual([10])
      expect(result.current.preImportantSections).toEqual([20])

      act(() => {
        result.current.clearHeadingsCache()
      })

      expect(result.current.preExcludedSections).toEqual([])
      expect(result.current.preImportantSections).toEqual([])
    })
  })
})
