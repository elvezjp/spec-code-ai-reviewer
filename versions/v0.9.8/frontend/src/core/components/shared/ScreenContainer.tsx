import type { ReactNode } from 'react'
import type { ScreenState } from '../../types'

interface ScreenContainerProps {
  currentScreen: ScreenState
  mainScreen: ReactNode
  executingScreen?: ReactNode
  resultScreen?: ReactNode
}

export function ScreenContainer({
  currentScreen,
  mainScreen,
  executingScreen,
  resultScreen,
}: ScreenContainerProps) {
  return (
    <>
      <div className={currentScreen === 'main' ? '' : 'hidden'}>{mainScreen}</div>
      {executingScreen && (
        <div className={currentScreen === 'executing' ? '' : 'hidden'}>
          {executingScreen}
        </div>
      )}
      {resultScreen && (
        <div className={currentScreen === 'result' ? '' : 'hidden'}>
          {resultScreen}
        </div>
      )}
    </>
  )
}
