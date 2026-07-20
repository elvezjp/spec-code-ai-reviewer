import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useModal } from '@core/hooks/useModal'

describe('useModal', () => {
  it('初期状態はfalse', () => {
    const { result } = renderHook(() => useModal())
    expect(result.current.isOpen).toBe(false)
  })

  it('初期状態をtrueに設定できる', () => {
    const { result } = renderHook(() => useModal(true))
    expect(result.current.isOpen).toBe(true)
  })

  it('openでモーダルを開く', () => {
    const { result } = renderHook(() => useModal())

    act(() => {
      result.current.open()
    })

    expect(result.current.isOpen).toBe(true)
  })

  it('closeでモーダルを閉じる', () => {
    const { result } = renderHook(() => useModal(true))

    act(() => {
      result.current.close()
    })

    expect(result.current.isOpen).toBe(false)
  })

  it('toggleで状態を切り替える', () => {
    const { result } = renderHook(() => useModal())

    act(() => {
      result.current.toggle()
    })
    expect(result.current.isOpen).toBe(true)

    act(() => {
      result.current.toggle()
    })
    expect(result.current.isOpen).toBe(false)
  })
})
