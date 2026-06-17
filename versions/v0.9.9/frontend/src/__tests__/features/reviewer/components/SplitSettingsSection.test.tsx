import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SplitSettingsSection } from '@features/reviewer/components/SplitSettingsSection'
import type { PreImportantSplitSettings, SplitSettings, SplitPreviewResult } from '@features/reviewer/types'

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
    hasAnyPendingSummarize: false,
    summarizeError: null as string | null,
    onToggleSummarizeMode: vi.fn(),
    onToggleExcludedDocPart: vi.fn(),
    onExecuteSummarize: vi.fn(),
    onExecuteAllSummarize: vi.fn(),
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
    pinnedCodePartIds: [] as string[],
    onTogglePinnedCodePart: vi.fn(),
    onToggleCodeSummarizeMode: vi.fn(),
    onToggleExcludedCodePart: vi.fn(),
    isCodeSummarizing: false,
    codeSummarizingPartIds: new Set<string>(),
    hasCodePendingSummarize: false,
    codeSummarizeError: null as string | null,
    onExecuteCodeSummarize: vi.fn(),
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

  describe('MAP.json / INDEX.md ダウンロードボタンの表示', () => {
    const makePreviewResult = (overrides: Partial<SplitPreviewResult> = {}): SplitPreviewResult => ({
      documentParts: [
        {
          id: 'MD1',
          section: '概要',
          displayName: '概要',
          level: 2,
          path: '概要',
          startLine: 1,
          endLine: 10,
          content: 'テスト内容',
          estimatedTokens: 100,
          summarizeMode: 'original',
          excluded: false,
          preImportant: false,
        },
      ],
      codeParts: [
        {
          id: 'CD1',
          symbol: 'TestClass',
          symbolType: 'class',
          parentSymbol: null,
          startLine: 1,
          endLine: 50,
          content: 'class TestClass:\n    pass',
          estimatedTokens: 500,
          excluded: false,
          summarizeMode: 'original' as const,
        },
      ],
      documentIndex: '# INDEX\n- MD1: 概要',
      documentMapJson: [{ id: 'MD1', section: '概要' }],
      codeIndex: '# INDEX\n- CD1: TestClass',
      codeMapJson: [{ id: 'CD1', symbol: 'TestClass' }],
      codeLanguage: 'Python',
      pinnedDocPartIds: [],
      documentWarnings: [],
      codeWarnings: [],
      ...overrides,
    })

    it('プレビュー結果がある場合、設計書のINDEX.md / MAP.jsonダウンロードボタンが表示される', () => {
      render(
        <SplitSettingsSection
          {...defaultProps}
          previewResult={makePreviewResult()}
        />
      )

      const indexButtons = screen.getAllByText('INDEX.md ↓')
      const mapButtons = screen.getAllByText('MAP.json ↓')
      // 設計書 + コードで2つずつ表示される
      expect(indexButtons).toHaveLength(2)
      expect(mapButtons).toHaveLength(2)
    })

    it('documentIndexがnullの場合、設計書のINDEX.mdボタンが表示されない', () => {
      render(
        <SplitSettingsSection
          {...defaultProps}
          previewResult={makePreviewResult({ documentIndex: null })}
        />
      )

      // コード側の1つのみ表示
      const indexButtons = screen.getAllByText('INDEX.md ↓')
      expect(indexButtons).toHaveLength(1)
    })

    it('documentMapJsonがnullの場合、設計書のMAP.jsonボタンが表示されない', () => {
      render(
        <SplitSettingsSection
          {...defaultProps}
          previewResult={makePreviewResult({ documentMapJson: null })}
        />
      )

      // コード側の1つのみ表示
      const mapButtons = screen.getAllByText('MAP.json ↓')
      expect(mapButtons).toHaveLength(1)
    })

    it('codeIndexがnullの場合、コードのINDEX.mdボタンが表示されない', () => {
      render(
        <SplitSettingsSection
          {...defaultProps}
          previewResult={makePreviewResult({ codeIndex: null })}
        />
      )

      // 設計書側の1つのみ表示
      const indexButtons = screen.getAllByText('INDEX.md ↓')
      expect(indexButtons).toHaveLength(1)
    })

    it('codeMapJsonがnullの場合、コードのMAP.jsonボタンが表示されない', () => {
      render(
        <SplitSettingsSection
          {...defaultProps}
          previewResult={makePreviewResult({ codeMapJson: null })}
        />
      )

      // 設計書側の1つのみ表示
      const mapButtons = screen.getAllByText('MAP.json ↓')
      expect(mapButtons).toHaveLength(1)
    })

    it('プレビュー結果がない場合、ダウンロードボタンが表示されない', () => {
      render(
        <SplitSettingsSection
          {...defaultProps}
          previewResult={null}
        />
      )

      expect(screen.queryByText('INDEX.md ↓')).not.toBeInTheDocument()
      expect(screen.queryByText('MAP.json ↓')).not.toBeInTheDocument()
    })

    it('ダウンロードボタンクリック時にBlobダウンロードが実行される', async () => {
      const user = userEvent.setup()
      const createObjectURLMock = vi.fn().mockReturnValue('blob:test-url')
      const revokeObjectURLMock = vi.fn()
      global.URL.createObjectURL = createObjectURLMock
      global.URL.revokeObjectURL = revokeObjectURLMock

      // createElement をスパイしてアンカー要素の click をモック
      const clickMock = vi.fn()
      const originalCreateElement = document.createElement.bind(document)
      const createElementSpy = vi.spyOn(document, 'createElement').mockImplementation((tagName: string, options?: ElementCreationOptions) => {
        const el = originalCreateElement(tagName, options)
        if (tagName === 'a') {
          el.click = clickMock
        }
        return el
      })

      render(
        <SplitSettingsSection
          {...defaultProps}
          previewResult={makePreviewResult()}
        />
      )

      const indexButtons = screen.getAllByText('INDEX.md ↓')
      await user.click(indexButtons[0])

      expect(createObjectURLMock).toHaveBeenCalled()
      expect(clickMock).toHaveBeenCalled()
      expect(revokeObjectURLMock).toHaveBeenCalled()

      createElementSpy.mockRestore()
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
