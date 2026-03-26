import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PreImportantPanel } from '@features/reviewer/components/PreImportantPanel'
import type { HeadingInfo } from '@features/reviewer/types'

describe('PreImportantPanel', () => {
  const mockHeadings: HeadingInfo[] = [
    { title: 'セクション1', level: 2, startLine: 1, endLine: 20, estimatedChars: 500 },
    { title: 'セクション2', level: 2, startLine: 21, endLine: 50, estimatedChars: 1200 },
    { title: 'セクション3', level: 2, startLine: 51, endLine: 80, estimatedChars: 800 },
  ]

  const defaultProps = {
    headings: mockHeadings,
    selectedStartLines: [] as number[],
    onToggle: vi.fn(),
    excludedStartLines: [] as number[],
    onToggleExcluded: vi.fn(),
    isLoading: false,
    error: null as string | null | undefined,
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('事前除外チェックボックスの表示', () => {
    it('テーブルに重要と除外の2つのチェックボックス列が表示される', () => {
      render(<PreImportantPanel {...defaultProps} />)

      // ヘッダーに2つのチェックボックス列がある
      expect(screen.getByText('事前重要指定')).toBeInTheDocument()
      expect(screen.getByText('事前除外指定')).toBeInTheDocument()
    })

    it('各セクション行に重要・除外の2つのチェックボックスが表示される', () => {
      render(<PreImportantPanel {...defaultProps} />)

      // 3セクション × 2チェックボックス = 6つのチェックボックス
      const checkboxes = screen.getAllByRole('checkbox')
      expect(checkboxes).toHaveLength(6)
    })

    it('selectedStartLinesに含まれるセクションの重要チェックボックスがONになる', () => {
      render(<PreImportantPanel {...defaultProps} selectedStartLines={[1]} />)

      const checkboxes = screen.getAllByRole('checkbox')
      // 1行目: 重要=ON, 除外=OFF
      expect(checkboxes[0]).toBeChecked()
      expect(checkboxes[1]).not.toBeChecked()
      // 2行目: 重要=OFF, 除外=OFF
      expect(checkboxes[2]).not.toBeChecked()
      expect(checkboxes[3]).not.toBeChecked()
    })

    it('excludedStartLinesに含まれるセクションの除外チェックボックスがONになる', () => {
      render(<PreImportantPanel {...defaultProps} excludedStartLines={[21]} />)

      const checkboxes = screen.getAllByRole('checkbox')
      // 1行目: 重要=OFF, 除外=OFF
      expect(checkboxes[0]).not.toBeChecked()
      expect(checkboxes[1]).not.toBeChecked()
      // 2行目: 重要=OFF, 除外=ON
      expect(checkboxes[2]).not.toBeChecked()
      expect(checkboxes[3]).toBeChecked()
    })
  })

  describe('排他制御（コールバック呼び出し）', () => {
    it('重要チェックボックスをクリックするとonToggleが正しいstartLineで呼ばれる', async () => {
      const user = userEvent.setup()
      const onToggle = vi.fn()
      render(<PreImportantPanel {...defaultProps} onToggle={onToggle} />)

      const checkboxes = screen.getAllByRole('checkbox')
      // 1行目の重要チェックボックス（index 0）をクリック
      await user.click(checkboxes[0])

      expect(onToggle).toHaveBeenCalledWith(1)
      expect(onToggle).toHaveBeenCalledTimes(1)
    })

    it('除外チェックボックスをクリックするとonToggleExcludedが正しいstartLineで呼ばれる', async () => {
      const user = userEvent.setup()
      const onToggleExcluded = vi.fn()
      render(<PreImportantPanel {...defaultProps} onToggleExcluded={onToggleExcluded} />)

      const checkboxes = screen.getAllByRole('checkbox')
      // 2行目の除外チェックボックス（index 3）をクリック
      await user.click(checkboxes[3])

      expect(onToggleExcluded).toHaveBeenCalledWith(21)
      expect(onToggleExcluded).toHaveBeenCalledTimes(1)
    })

    it('重要チェックボックスクリックでonToggleExcludedは呼ばれない', async () => {
      const user = userEvent.setup()
      const onToggle = vi.fn()
      const onToggleExcluded = vi.fn()
      render(<PreImportantPanel {...defaultProps} onToggle={onToggle} onToggleExcluded={onToggleExcluded} />)

      const checkboxes = screen.getAllByRole('checkbox')
      await user.click(checkboxes[0]) // 重要チェックボックス

      expect(onToggle).toHaveBeenCalledTimes(1)
      expect(onToggleExcluded).not.toHaveBeenCalled()
    })

    it('除外チェックボックスクリックでonToggleは呼ばれない', async () => {
      const user = userEvent.setup()
      const onToggle = vi.fn()
      const onToggleExcluded = vi.fn()
      render(<PreImportantPanel {...defaultProps} onToggle={onToggle} onToggleExcluded={onToggleExcluded} />)

      const checkboxes = screen.getAllByRole('checkbox')
      await user.click(checkboxes[1]) // 除外チェックボックス

      expect(onToggleExcluded).toHaveBeenCalledTimes(1)
      expect(onToggle).not.toHaveBeenCalled()
    })
  })

  describe('パネルタイトルと説明文', () => {
    it('パネルタイトルが「事前指定」と表示される', () => {
      render(<PreImportantPanel {...defaultProps} />)

      expect(screen.getByText('事前指定')).toBeInTheDocument()
    })

    it('説明文に「事前重要指定」と「事前除外指定」が含まれる', () => {
      render(<PreImportantPanel {...defaultProps} />)

      // ヘッダーセルと説明文の両方に表示されるため、getAllByTextで複数存在を確認
      const importantTexts = screen.getAllByText(/事前重要指定/)
      expect(importantTexts.length).toBeGreaterThanOrEqual(2) // ヘッダー + 説明文
      const excludedTexts = screen.getAllByText(/事前除外指定/)
      expect(excludedTexts.length).toBeGreaterThanOrEqual(2) // ヘッダー + 説明文
    })
  })

  describe('ローディング状態', () => {
    it('isLoading=trueの場合はローディングメッセージが表示される', () => {
      render(<PreImportantPanel {...defaultProps} isLoading={true} />)

      expect(screen.getByText('見出し一覧を取得中...')).toBeInTheDocument()
      expect(screen.queryAllByRole('checkbox')).toHaveLength(0)
    })
  })

  describe('エラー状態', () => {
    it('errorがある場合はエラーメッセージが表示される', () => {
      render(<PreImportantPanel {...defaultProps} error="接続エラー" />)

      expect(screen.getByText(/接続エラー/)).toBeInTheDocument()
      expect(screen.queryAllByRole('checkbox')).toHaveLength(0)
    })
  })

  describe('見出しが空の場合', () => {
    it('headingsが空配列の場合は何も表示されない', () => {
      const { container } = render(<PreImportantPanel {...defaultProps} headings={[]} />)

      expect(container.innerHTML).toBe('')
    })
  })

  describe('セクション情報の表示', () => {
    it('各セクションの名前・行範囲・推定文字数が表示される', () => {
      render(<PreImportantPanel {...defaultProps} />)

      expect(screen.getByText('セクション1')).toBeInTheDocument()
      expect(screen.getByText('セクション2')).toBeInTheDocument()
      expect(screen.getByText('セクション3')).toBeInTheDocument()
      expect(screen.getByText('L1-L20')).toBeInTheDocument()
      expect(screen.getByText('L21-L50')).toBeInTheDocument()
      expect(screen.getByText('~500')).toBeInTheDocument()
      expect(screen.getByText('~1,200')).toBeInTheDocument()
    })
  })
})
