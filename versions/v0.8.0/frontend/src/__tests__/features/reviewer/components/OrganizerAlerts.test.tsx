import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { OrganizerAlerts } from '@features/reviewer/components/OrganizerAlerts'
import type { OrganizeMarkdownWarning } from '@features/reviewer/types'

describe('OrganizerAlerts', () => {
  it('エラーも警告もない場合は何も表示しない', () => {
    const { container } = render(<OrganizerAlerts />)
    expect(container.firstChild).toBeNull()
  })

  it('エラーのみ表示', () => {
    render(
      <OrganizerAlerts
        error={{ code: 'api_error', message: 'APIエラーが発生しました' }}
      />
    )

    expect(screen.getByText('APIエラー')).toBeInTheDocument()
    expect(screen.getByText('APIエラーが発生しました')).toBeInTheDocument()
  })

  it('警告のみ表示', () => {
    const warnings: OrganizeMarkdownWarning[] = [
      { code: 'ref_missing', message: '参照IDが欠落しています' },
      { code: 'content_modified', message: '内容が改変されています' },
    ]

    render(<OrganizerAlerts warnings={warnings} />)

    expect(screen.getByText('警告')).toBeInTheDocument()
    expect(screen.getByText('参照IDが欠落しています')).toBeInTheDocument()
    expect(screen.getByText('内容が改変されています')).toBeInTheDocument()
  })

  it('エラーと警告の両方を表示', () => {
    const warnings: OrganizeMarkdownWarning[] = [
      { code: 'ref_missing', message: '参照IDが欠落しています' },
    ]

    render(
      <OrganizerAlerts
        error={{ code: 'timeout', message: 'タイムアウトしました' }}
        warnings={warnings}
      />
    )

    expect(screen.getByText('タイムアウト')).toBeInTheDocument()
    expect(screen.getByText('タイムアウトしました')).toBeInTheDocument()
    expect(screen.getByText('警告')).toBeInTheDocument()
    expect(screen.getByText('参照IDが欠落しています')).toBeInTheDocument()
  })

  describe('エラーコードのタイトル表示', () => {
    it('token_limit → トークン超過', () => {
      render(
        <OrganizerAlerts
          error={{ code: 'token_limit', message: '入力が長すぎます' }}
        />
      )
      expect(screen.getByText('トークン超過')).toBeInTheDocument()
    })

    it('api_error → APIエラー', () => {
      render(
        <OrganizerAlerts
          error={{ code: 'api_error', message: 'APIエラーメッセージ' }}
        />
      )
      expect(screen.getByText('APIエラー')).toBeInTheDocument()
      expect(screen.getByText('APIエラーメッセージ')).toBeInTheDocument()
    })

    it('format_invalid → 形式不正', () => {
      render(
        <OrganizerAlerts
          error={{ code: 'format_invalid', message: '形式が不正です' }}
        />
      )
      expect(screen.getByText('形式不正')).toBeInTheDocument()
    })

    it('timeout → タイムアウト', () => {
      render(
        <OrganizerAlerts
          error={{ code: 'timeout', message: 'タイムアウトしました' }}
        />
      )
      expect(screen.getByText('タイムアウト')).toBeInTheDocument()
    })

    it('input_empty → 入力不足', () => {
      render(
        <OrganizerAlerts
          error={{ code: 'input_empty', message: '入力が空です' }}
        />
      )
      expect(screen.getByText('入力不足')).toBeInTheDocument()
    })

    it('policy_empty → 方針未入力', () => {
      render(
        <OrganizerAlerts
          error={{ code: 'policy_empty', message: '方針が空です' }}
        />
      )
      expect(screen.getByText('方針未入力')).toBeInTheDocument()
    })

    it('未知のエラーコード → エラー', () => {
      render(
        <OrganizerAlerts
          error={{ code: 'unknown_error', message: '不明なエラー' }}
        />
      )
      expect(screen.getByText('エラー')).toBeInTheDocument()
    })

    it('エラーコード未指定 → エラー', () => {
      render(<OrganizerAlerts error={{ message: 'エラーメッセージ' }} />)
      expect(screen.getByText('エラー')).toBeInTheDocument()
    })
  })

  it('複数の警告をリスト表示', () => {
    const warnings: OrganizeMarkdownWarning[] = [
      { code: 'ref_missing', message: '警告1' },
      { code: 'content_modified', message: '警告2' },
      { code: 'other', message: '警告3' },
    ]

    render(<OrganizerAlerts warnings={warnings} />)

    const listItems = screen.getAllByRole('listitem')
    expect(listItems).toHaveLength(3)
    expect(listItems[0]).toHaveTextContent('警告1')
    expect(listItems[1]).toHaveTextContent('警告2')
    expect(listItems[2]).toHaveTextContent('警告3')
  })
})
