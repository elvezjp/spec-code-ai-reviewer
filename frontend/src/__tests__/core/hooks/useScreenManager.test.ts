import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useScreenManager } from '@core/hooks/useScreenManager'

describe('useScreenManager', () => {
  it('初期状態はmain', () => {
    const { result } = renderHook(() => useScreenManager())
    expect(result.current.currentScreen).toBe('main')
  })

  it('初期状態を指定できる', () => {
    const { result } = renderHook(() => useScreenManager('executing'))
    expect(result.current.currentScreen).toBe('executing')
  })

  it('showMainでmain画面に切り替わる', () => {
    const { result } = renderHook(() => useScreenManager('result'))

    act(() => {
      result.current.showMain()
    })

    expect(result.current.currentScreen).toBe('main')
  })

  it('showExecutingでexecuting画面に切り替わる', () => {
    const { result } = renderHook(() => useScreenManager())

    act(() => {
      result.current.showExecuting()
    })

    expect(result.current.currentScreen).toBe('executing')
  })

  it('showResultでresult画面に切り替わる', () => {
    const { result } = renderHook(() => useScreenManager())

    act(() => {
      result.current.showResult()
    })

    expect(result.current.currentScreen).toBe('result')
  })

  it('setScreenで任意の画面に切り替えられる', () => {
    const { result } = renderHook(() => useScreenManager())

    act(() => {
      result.current.setScreen('result')
    })
    expect(result.current.currentScreen).toBe('result')

    act(() => {
      result.current.setScreen('executing')
    })
    expect(result.current.currentScreen).toBe('executing')
  })
})
