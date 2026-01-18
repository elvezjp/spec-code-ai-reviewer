import { useMemo } from 'react'

interface TokenEstimationResult {
  totalTokens: number
  specTokens: number
  codeTokens: number
  promptTokens: number
  isWarning: boolean
  formattedTotal: string
}

// トークン数推定関数
// 日本語: 約1.5文字/トークン、英数字: 約4文字/トークン
function estimateTokenCount(text: string): number {
  if (!text) return 0

  // 日本語文字（ひらがな、カタカナ、漢字）をカウント
  const japaneseChars = (text.match(/[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]/g) || []).length
  // 英数字とその他の文字をカウント
  const otherChars = text.length - japaneseChars

  // 日本語は約1.5文字/トークン、英数字は約4文字/トークン
  const japaneseTokens = japaneseChars / 1.5
  const otherTokens = otherChars / 4

  return Math.round(japaneseTokens + otherTokens)
}

const WARNING_THRESHOLD = 100000

export function useTokenEstimation(
  specMarkdown: string,
  codeWithLineNumbers: string,
  systemPromptText: string
): TokenEstimationResult {
  return useMemo(() => {
    const specTokens = estimateTokenCount(specMarkdown)
    const codeTokens = estimateTokenCount(codeWithLineNumbers)
    const promptTokens = estimateTokenCount(systemPromptText)
    const totalTokens = specTokens + codeTokens + promptTokens

    return {
      totalTokens,
      specTokens,
      codeTokens,
      promptTokens,
      isWarning: totalTokens >= WARNING_THRESHOLD,
      formattedTotal: totalTokens.toLocaleString() + ' トークン',
    }
  }, [specMarkdown, codeWithLineNumbers, systemPromptText])
}

export { estimateTokenCount }
