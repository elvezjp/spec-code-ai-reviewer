import { useState, useCallback } from 'react'
import type { ScreenState } from '../types'

interface UseScreenManagerReturn {
  currentScreen: ScreenState
  showMain: () => void
  showExecuting: () => void
  showResult: () => void
  setScreen: (screen: ScreenState) => void
}

export function useScreenManager(initialScreen: ScreenState = 'main'): UseScreenManagerReturn {
  const [currentScreen, setCurrentScreen] = useState<ScreenState>(initialScreen)

  const showMain = useCallback(() => setCurrentScreen('main'), [])
  const showExecuting = useCallback(() => setCurrentScreen('executing'), [])
  const showResult = useCallback(() => setCurrentScreen('result'), [])
  const setScreen = useCallback((screen: ScreenState) => setCurrentScreen(screen), [])

  return {
    currentScreen,
    showMain,
    showExecuting,
    showResult,
    setScreen,
  }
}
