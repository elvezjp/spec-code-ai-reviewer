import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SplitSettingsSection } from '@features/reviewer/components/SplitSettingsSection'
import type { PreImportantSplitSettings, SplitSettings } from '@features/reviewer/types'

// lucide-react のモック（アイコンコンポーネント）
vi.mock('lucide-react', () => ({
  ChevronDown: () => <span data-testid="chevron-down" />,
  ChevronRight: () => <span data-testid="chevron-right" />,
  Loader2: () => <span data-testid="loader" />,
}))

describe('SplitSettingsSection - DocumentSplitSettingsBlock', () => {
  const baseSplitSettings: PreImportantSplitSettings = {
    splitMode: 'ai',
    headingLevel: 2,
    splitInstructions: '',
    maxSubsections: 5,
    summaryMode: 'ai',
    summaryMaxChars: 100,
  }

  const baseSettings: SplitSettings = {
    reviewMode: 'split',
    documentMaxDepth: 2,
    documentSplitMode: 'ai',
    aiPromptExtraNotes: '',
  }

  const defaultProps = {
    settings: baseSettings,
    onSettingsChange: vi.fn(),
    onShowToast: vi.fn(),
    previewResult: null,
    onExecutePreview: vi.fn().mockResolvedValue(undefined),
    onClearPreview: vi.fn(),
    isExecuting: false,
    hasDesignDoc: true,
    hasCodeFiles: true,
    codeFilenames: ['main.py'],
    pinnedDocPartIds: [] as string[],
    onTogglePinnedDocPart: vi.fn(),
    isSummarizing: false,
    summarizingPartIds: new Set<string>(),
    hasPendingSummarize: false,
    summarizeError: null as string | null,
    onToggleSummarizeMode: vi.fn(),
    onToggleExcludedDocPart: vi.fn(),
    onExecuteSummarize: vi.fn(),
    previewError: null as string | null,
    headings: [],
    isLoadingHeadings: false,
    headingsError: null as string | null,
    preImportantSections: [] as number[],
    onTogglePreImportantSection: vi.fn(),
    preExcludedSections: [] as number[],
    onTogglePreExcludedSection: vi.fn(),
    preImportantSplitSettings: { ...baseSplitSettings },
    normalSplitSettings: { ...baseSplitSettings },
    onPreImportantSplitSettingsChange: vi.fn(),
    onNormalSplitSettingsChange: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('サマリーモードのラジオボタン表示', () => {
    it('通常セクションブロックにサマリーモードのラジオボタンが表示される', () => {
      render(<SplitSettingsSection {...defaultProps} />)

      // summaryMode radio buttons: ルールベース and AI（推奨）
      expect(screen.getByText('サマリーモード:')).toBeInTheDocument()
      expect(screen.getByText('ルールベース')).toBeInTheDocument()
      // AI（推奨） is the summary mode label
      const aiLabels = screen.getAllByText('AI（推奨）')
      expect(aiLabels.length).toBeGreaterThanOrEqual(1)
    })
  })

  describe('最大分割数の表示条件', () => {
    it('splitMode="nlp"のとき最大分割数の入力が表示される', () => {
      const nlpSettings = { ...baseSplitSettings, splitMode: 'nlp' as const }
      render(
        <SplitSettingsSection
          {...defaultProps}
          normalSplitSettings={nlpSettings}
        />
      )

      expect(screen.getByText('1セクションあたりの最大分割数:')).toBeInTheDocument()
    })

    it('splitMode="ai"のとき最大分割数の入力が表示される', () => {
      const aiSettings = { ...baseSplitSettings, splitMode: 'ai' as const }
      render(
        <SplitSettingsSection
          {...defaultProps}
          normalSplitSettings={aiSettings}
        />
      )

      expect(screen.getByText('1セクションあたりの最大分割数:')).toBeInTheDocument()
    })

    it('splitMode="heading"のとき最大分割数の入力が表示されない', () => {
      const headingSettings = { ...baseSplitSettings, splitMode: 'heading' as const }
      render(
        <SplitSettingsSection
          {...defaultProps}
          normalSplitSettings={headingSettings}
        />
      )

      expect(screen.queryByText('1セクションあたりの最大分割数:')).not.toBeInTheDocument()
    })
  })

  describe('サマリー最大文字数の表示', () => {
    it('summaryMode="text"のときサマリー最大文字数の入力が表示される', () => {
      const textSettings = { ...baseSplitSettings, summaryMode: 'text' as const }
      render(
        <SplitSettingsSection
          {...defaultProps}
          normalSplitSettings={textSettings}
        />
      )

      expect(screen.getByText('サマリー最大文字数:')).toBeInTheDocument()
    })

    it('summaryMode="ai"のときもサマリー最大文字数の入力が表示される', () => {
      const aiSettings = { ...baseSplitSettings, summaryMode: 'ai' as const }
      render(
        <SplitSettingsSection
          {...defaultProps}
          normalSplitSettings={aiSettings}
        />
      )

      expect(screen.getByText('サマリー最大文字数:')).toBeInTheDocument()
    })
  })
})
