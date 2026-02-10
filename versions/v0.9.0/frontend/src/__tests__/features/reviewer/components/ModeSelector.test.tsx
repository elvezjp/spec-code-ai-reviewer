import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ModeSelector } from '@features/reviewer/components/ModeSelector'
import type { ReviewMode } from '@core/types'

describe('ModeSelector', () => {
  describe('初期状態', () => {
    it('突合モードが選択されている場合、突合モードボタンがアクティブ', () => {
      const onModeChange = vi.fn()
      render(<ModeSelector currentMode="review" onModeChange={onModeChange} />)

      const reviewButton = screen.getByRole('button', { name: /突合モード/ })
      const mappingButton = screen.getByRole('button', { name: /マッピングモード/ })

      // 突合モードがアクティブ状態（bg-blue-500）
      expect(reviewButton.className).toContain('bg-blue-500')
      expect(reviewButton.className).toContain('text-white')

      // マッピングモードが非アクティブ状態（bg-gray-100）
      expect(mappingButton.className).toContain('bg-gray-100')
      expect(mappingButton.className).toContain('text-gray-600')
    })

    it('マッピングモードが選択されている場合、マッピングモードボタンがアクティブ', () => {
      const onModeChange = vi.fn()
      render(<ModeSelector currentMode="mapping" onModeChange={onModeChange} />)

      const reviewButton = screen.getByRole('button', { name: /突合モード/ })
      const mappingButton = screen.getByRole('button', { name: /マッピングモード/ })

      // 突合モードが非アクティブ状態
      expect(reviewButton.className).toContain('bg-gray-100')
      expect(reviewButton.className).toContain('text-gray-600')

      // マッピングモードがアクティブ状態
      expect(mappingButton.className).toContain('bg-blue-500')
      expect(mappingButton.className).toContain('text-white')
    })
  })

  describe('モード表示', () => {
    it('突合モードのラベルと説明が表示される', () => {
      const onModeChange = vi.fn()
      render(<ModeSelector currentMode="review" onModeChange={onModeChange} />)

      expect(screen.getByText('突合モード')).toBeInTheDocument()
      expect(screen.getByText('設計書とコードの整合性を検証')).toBeInTheDocument()
    })

    it('マッピングモードのラベルと説明が表示される', () => {
      const onModeChange = vi.fn()
      render(<ModeSelector currentMode="review" onModeChange={onModeChange} />)

      expect(screen.getByText('マッピングモード')).toBeInTheDocument()
      expect(screen.getByText('設計項目と実装箇所を対応付け')).toBeInTheDocument()
    })
  })

  describe('モード切り替え', () => {
    it('マッピングモードボタンをクリックすると onModeChange が mapping で呼ばれる', () => {
      const onModeChange = vi.fn()
      render(<ModeSelector currentMode="review" onModeChange={onModeChange} />)

      const mappingButton = screen.getByRole('button', { name: /マッピングモード/ })
      fireEvent.click(mappingButton)

      expect(onModeChange).toHaveBeenCalledTimes(1)
      expect(onModeChange).toHaveBeenCalledWith('mapping')
    })

    it('突合モードボタンをクリックすると onModeChange が review で呼ばれる', () => {
      const onModeChange = vi.fn()
      render(<ModeSelector currentMode="mapping" onModeChange={onModeChange} />)

      const reviewButton = screen.getByRole('button', { name: /突合モード/ })
      fireEvent.click(reviewButton)

      expect(onModeChange).toHaveBeenCalledTimes(1)
      expect(onModeChange).toHaveBeenCalledWith('review')
    })

    it('同じモードのボタンをクリックしても onModeChange は呼ばれる', () => {
      const onModeChange = vi.fn()
      render(<ModeSelector currentMode="review" onModeChange={onModeChange} />)

      const reviewButton = screen.getByRole('button', { name: /突合モード/ })
      fireEvent.click(reviewButton)

      // 同じモードでもコールバックは呼ばれる（親コンポーネントで制御）
      expect(onModeChange).toHaveBeenCalledTimes(1)
      expect(onModeChange).toHaveBeenCalledWith('review')
    })
  })

  describe('アクセシビリティ', () => {
    it('両方のモードがボタンとしてレンダリングされる', () => {
      const onModeChange = vi.fn()
      render(<ModeSelector currentMode="review" onModeChange={onModeChange} />)

      const buttons = screen.getAllByRole('button')
      expect(buttons).toHaveLength(2)
    })
  })

  describe('スタイリング', () => {
    it('コンテナが正しいスタイルを持つ', () => {
      const onModeChange = vi.fn()
      const { container } = render(
        <ModeSelector currentMode="review" onModeChange={onModeChange} />
      )

      const wrapper = container.firstChild as HTMLElement
      expect(wrapper.className).toContain('bg-white')
      expect(wrapper.className).toContain('rounded-lg')
      expect(wrapper.className).toContain('shadow-md')
    })
  })
})
