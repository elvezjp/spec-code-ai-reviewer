import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MarkdownOrganizer } from '@features/reviewer/components/MarkdownOrganizer'
import type { DesignFile, LlmConfig } from '@features/reviewer/types'

// APIモジュールのモック
const mockOrganizeMarkdown = vi.fn()
vi.mock('@features/reviewer/services/api', () => ({
  organizeMarkdown: (request: any) => mockOrganizeMarkdown(request),
}))

// TokenEstimationのモック
vi.mock('@core/index', () => ({
  estimateTokenCount: vi.fn((text: string) => Math.ceil(text.length / 4)),
}))

describe('MarkdownOrganizer', () => {
  const mockSpecFiles: DesignFile[] = [
    {
      file: new File([''], 'spec1.xlsx'),
      filename: 'spec1.xlsx',
      isMain: true,
      type: '設計書',
      tool: 'markitdown',
      markdown: '# 設計書1\n内容1',
    },
    {
      file: new File([''], 'spec2.xlsx'),
      filename: 'spec2.xlsx',
      isMain: false,
      type: '要件定義書',
      tool: 'excel2md',
      markdown: '# 設計書2\n内容2',
    },
  ]

  const mockGetTypeNote = vi.fn((type: string) => `注意: ${type}`)
  const mockOnAdopt = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    mockGetTypeNote.mockImplementation((type: string) => `注意: ${type}`)
  })

  describe('初期表示', () => {
    it('specMarkdownがnullの場合はボタンが無効', () => {
      render(
        <MarkdownOrganizer
          specMarkdown={null}
          specFiles={mockSpecFiles}
          getTypeNote={mockGetTypeNote}
          onAdopt={mockOnAdopt}
        />
      )

      const button = screen.getByText('AIでMarkdownを整理する')
      expect(button).toBeDisabled()
    })

    it('specMarkdownがある場合はボタンが有効', () => {
      render(
        <MarkdownOrganizer
          specMarkdown="# 結合済みMarkdown\n内容"
          specFiles={mockSpecFiles}
          getTypeNote={mockGetTypeNote}
          onAdopt={mockOnAdopt}
        />
      )

      const button = screen.getByText('AIでMarkdownを整理する')
      expect(button).not.toBeDisabled()
    })

    it('specMarkdownがnullから値に変わると自動で開く', () => {
      const { rerender } = render(
        <MarkdownOrganizer
          specMarkdown={null}
          specFiles={mockSpecFiles}
          getTypeNote={mockGetTypeNote}
          onAdopt={mockOnAdopt}
        />
      )

      expect(screen.queryByText('整理方針')).not.toBeInTheDocument()

      rerender(
        <MarkdownOrganizer
          specMarkdown="# 結合済みMarkdown"
          specFiles={mockSpecFiles}
          getTypeNote={mockGetTypeNote}
          onAdopt={mockOnAdopt}
        />
      )

      expect(screen.getByText('整理方針')).toBeInTheDocument()
    })
  })

  describe('整理実行', () => {
    it('正常系: 単一ファイルの整理', async () => {
      const user = userEvent.setup()
      mockOrganizeMarkdown.mockResolvedValueOnce({
        success: true,
        organizedMarkdown: '# 整理済み1\n[ref:S1-P1] 内容1',
        warnings: [],
      })

      render(
        <MarkdownOrganizer
          specMarkdown="# 結合済みMarkdown"
          specFiles={[mockSpecFiles[0]]}
          getTypeNote={mockGetTypeNote}
          onAdopt={mockOnAdopt}
        />
      )

      // まず開く
      const toggleButton = screen.getByText('AIでMarkdownを整理する')
      await user.click(toggleButton)

      const button = screen.getByText('整理を実行')
      await user.click(button)

      await waitFor(() => {
        expect(mockOrganizeMarkdown).toHaveBeenCalledTimes(1)
      })

      expect(mockOrganizeMarkdown).toHaveBeenCalledWith({
        markdown: '# 設計書1\n内容1',
        policy: expect.stringContaining('要約や推測は禁止'),
        source: {
          filename: 'spec1.xlsx',
          tool: 'markitdown',
        },
        llmConfig: undefined,
      })
    })

    it('正常系: 複数ファイルの整理', async () => {
      const user = userEvent.setup()
      mockOrganizeMarkdown
        .mockResolvedValueOnce({
          success: true,
          organizedMarkdown: '# 整理済み1',
          warnings: [],
        })
        .mockResolvedValueOnce({
          success: true,
          organizedMarkdown: '# 整理済み2',
          warnings: [],
        })

      render(
        <MarkdownOrganizer
          specMarkdown="# 結合済みMarkdown"
          specFiles={mockSpecFiles}
          getTypeNote={mockGetTypeNote}
          onAdopt={mockOnAdopt}
        />
      )

      // まず開く
      const toggleButton = screen.getByText('AIでMarkdownを整理する')
      await user.click(toggleButton)

      const button = screen.getByText('整理を実行')
      await user.click(button)

      await waitFor(() => {
        expect(mockOrganizeMarkdown).toHaveBeenCalledTimes(2)
      })
    })

    it('エラー: APIエラー時', async () => {
      const user = userEvent.setup()
      mockOrganizeMarkdown.mockResolvedValueOnce({
        success: false,
        error: 'APIエラーが発生しました',
        errorCode: 'api_error',
      })

      render(
        <MarkdownOrganizer
          specMarkdown="# 結合済みMarkdown"
          specFiles={[mockSpecFiles[0]]}
          getTypeNote={mockGetTypeNote}
          onAdopt={mockOnAdopt}
        />
      )

      // まず開く
      const toggleButton = screen.getByText('AIでMarkdownを整理する')
      await user.click(toggleButton)

      const button = screen.getByText('整理を実行')
      await user.click(button)

      await waitFor(() => {
        expect(screen.getByText(/APIエラーが発生しました/)).toBeInTheDocument()
      })
    })

    it('警告: 警告が返る場合', async () => {
      const user = userEvent.setup()
      mockOrganizeMarkdown.mockResolvedValueOnce({
        success: true,
        organizedMarkdown: '# 整理済み1',
        warnings: [
          { code: 'ref_missing', message: '参照IDが欠落しています' },
        ],
      })

      render(
        <MarkdownOrganizer
          specMarkdown="# 結合済みMarkdown"
          specFiles={[mockSpecFiles[0]]}
          getTypeNote={mockGetTypeNote}
          onAdopt={mockOnAdopt}
        />
      )

      // まず開く
      const toggleButton = screen.getByText('AIでMarkdownを整理する')
      await user.click(toggleButton)

      const button = screen.getByText('整理を実行')
      await user.click(button)

      await waitFor(() => {
        expect(screen.getByText(/参照IDが欠落しています/)).toBeInTheDocument()
      })
    })
  })

  describe('採用・破棄', () => {
    it('採用ボタンでonAdoptが呼ばれる', async () => {
      const user = userEvent.setup()
      mockOrganizeMarkdown.mockResolvedValueOnce({
        success: true,
        organizedMarkdown: '# 整理済み1',
        warnings: [],
      })

      render(
        <MarkdownOrganizer
          specMarkdown="# 結合済みMarkdown"
          specFiles={[mockSpecFiles[0]]}
          getTypeNote={mockGetTypeNote}
          onAdopt={mockOnAdopt}
        />
      )

      // まず開く
      const toggleButton = screen.getByText('AIでMarkdownを整理する')
      await user.click(toggleButton)

      const organizeButton = screen.getByText('整理を実行')
      await user.click(organizeButton)

      await waitFor(() => {
        expect(screen.getByText('採用してMarkdownに反映')).toBeInTheDocument()
      })

      const adoptButton = screen.getByText('採用してMarkdownに反映')
      await user.click(adoptButton)

      expect(mockOnAdopt).toHaveBeenCalledTimes(1)
      const adoptedFiles = mockOnAdopt.mock.calls[0][0]
      expect(adoptedFiles).toBeInstanceOf(Map)
      expect(adoptedFiles.get('spec1.xlsx')).toBe('# 整理済み1')
    })

    it('破棄ボタンで整理結果がクリアされる', async () => {
      const user = userEvent.setup()
      mockOrganizeMarkdown.mockResolvedValueOnce({
        success: true,
        organizedMarkdown: '# 整理済み1',
        warnings: [],
      })

      render(
        <MarkdownOrganizer
          specMarkdown="# 結合済みMarkdown"
          specFiles={[mockSpecFiles[0]]}
          getTypeNote={mockGetTypeNote}
          onAdopt={mockOnAdopt}
        />
      )

      // まず開く
      const toggleButton = screen.getByText('AIでMarkdownを整理する')
      await user.click(toggleButton)

      const organizeButton = screen.getByText('整理を実行')
      await user.click(organizeButton)

      await waitFor(() => {
        expect(screen.getByText('破棄')).toBeInTheDocument()
      })

      const discardButton = screen.getByText('破棄')
      await user.click(discardButton)

      expect(screen.queryByText('採用してMarkdownに反映')).not.toBeInTheDocument()
      expect(mockOnAdopt).not.toHaveBeenCalled()
    })
  })

  describe('表示モード切り替え', () => {
    it('セクション表示と行表示を切り替えられる', async () => {
      const user = userEvent.setup()
      mockOrganizeMarkdown.mockResolvedValueOnce({
        success: true,
        organizedMarkdown: '# 整理済み1',
        warnings: [],
      })

      render(
        <MarkdownOrganizer
          specMarkdown="# 結合済みMarkdown"
          specFiles={[mockSpecFiles[0]]}
          getTypeNote={mockGetTypeNote}
          onAdopt={mockOnAdopt}
        />
      )

      // まず開く
      const toggleButton = screen.getByText('AIでMarkdownを整理する')
      await user.click(toggleButton)

      const organizeButton = screen.getByText('整理を実行')
      await user.click(organizeButton)

      await waitFor(() => {
        expect(screen.getByText('セクション')).toBeInTheDocument()
      })

      const lineButton = screen.getByText('行')
      await user.click(lineButton)

      // 行表示モードに切り替わったことを確認
      expect(screen.getByText('行').closest('button')).toHaveClass('bg-blue-50')
    })
  })

  describe('LLM設定の適用', () => {
    it('LLM設定が渡される', async () => {
      const user = userEvent.setup()
      const llmConfig: LlmConfig = {
        provider: 'anthropic',
        model: 'claude-sonnet-4-20250514',
        maxTokens: 16384,
        apiKey: 'test-key',
      }

      mockOrganizeMarkdown.mockResolvedValueOnce({
        success: true,
        organizedMarkdown: '# 整理済み1',
        warnings: [],
      })

      render(
        <MarkdownOrganizer
          specMarkdown="# 結合済みMarkdown"
          specFiles={[mockSpecFiles[0]]}
          llmConfig={llmConfig}
          getTypeNote={mockGetTypeNote}
          onAdopt={mockOnAdopt}
        />
      )

      // まず開く
      const toggleButton = screen.getByText('AIでMarkdownを整理する')
      await user.click(toggleButton)

      const button = screen.getByText('整理を実行')
      await user.click(button)

      await waitFor(() => {
        expect(mockOrganizeMarkdown).toHaveBeenCalledWith(
          expect.objectContaining({
            llmConfig,
          })
        )
      })
    })
  })
})
