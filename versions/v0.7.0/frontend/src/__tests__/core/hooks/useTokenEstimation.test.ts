import { describe, it, expect } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useTokenEstimation, estimateTokenCount } from '@core/hooks/useTokenEstimation'

describe('estimateTokenCount', () => {
  it('空文字列は0トークン', () => {
    expect(estimateTokenCount('')).toBe(0)
  })

  it('英数字のみのテキスト（約4文字/トークン）', () => {
    const text = 'Hello World' // 11文字（スペース含む）
    const result = estimateTokenCount(text)
    // 11 / 4 = 2.75 → 3
    expect(result).toBe(3)
  })

  it('日本語のみのテキスト（約1.5文字/トークン）', () => {
    const text = 'こんにちは' // 5文字
    const result = estimateTokenCount(text)
    // 5 / 1.5 = 3.33 → 3
    expect(result).toBe(3)
  })

  it('日本語と英数字の混在テキスト', () => {
    const text = 'Hello こんにちは World' // Hello(5) + space(1) + こんにちは(5) + space(1) + World(5)
    const result = estimateTokenCount(text)
    // 日本語: 5 / 1.5 = 3.33
    // 英数字+スペース: 12 / 4 = 3
    // 合計: 6.33 → 6
    expect(result).toBe(6)
  })

  it('漢字を正しくカウント', () => {
    const text = '設計書' // 3文字
    const result = estimateTokenCount(text)
    // 3 / 1.5 = 2
    expect(result).toBe(2)
  })

  it('カタカナを正しくカウント', () => {
    const text = 'プログラム' // 5文字
    const result = estimateTokenCount(text)
    // 5 / 1.5 = 3.33 → 3
    expect(result).toBe(3)
  })
})

describe('useTokenEstimation', () => {
  it('全て空文字列の場合は0トークン', () => {
    const { result } = renderHook(() => useTokenEstimation('', '', ''))

    expect(result.current.totalTokens).toBe(0)
    expect(result.current.specTokens).toBe(0)
    expect(result.current.codeTokens).toBe(0)
    expect(result.current.promptTokens).toBe(0)
    expect(result.current.isWarning).toBe(false)
  })

  it('各テキストのトークン数を個別に計算', () => {
    const { result } = renderHook(() =>
      useTokenEstimation('設計書', 'function test() {}', 'システムプロンプト')
    )

    expect(result.current.specTokens).toBe(2) // 設計書: 3 / 1.5 = 2
    expect(result.current.codeTokens).toBe(5) // function test() {}: 18 / 4 = 4.5 → 5
    expect(result.current.promptTokens).toBe(6) // システムプロンプト: 9 / 1.5 = 6
    expect(result.current.totalTokens).toBe(13)
  })

  it('100,000トークン以上で警告フラグがtrue', () => {
    // 100,000トークン = 約150,000日本語文字
    const longText = 'あ'.repeat(150000)
    const { result } = renderHook(() => useTokenEstimation(longText, '', ''))

    expect(result.current.isWarning).toBe(true)
  })

  it('100,000トークン未満で警告フラグはfalse', () => {
    const text = 'あ'.repeat(1000)
    const { result } = renderHook(() => useTokenEstimation(text, '', ''))

    expect(result.current.isWarning).toBe(false)
  })

  it('formattedTotalがカンマ区切りで表示される', () => {
    const text = 'あ'.repeat(15000) // 15000 / 1.5 = 10000トークン
    const { result } = renderHook(() => useTokenEstimation(text, '', ''))

    expect(result.current.formattedTotal).toBe('10,000 トークン')
  })
})
