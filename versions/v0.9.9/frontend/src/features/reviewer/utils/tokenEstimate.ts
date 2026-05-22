/**
 * 簡易トークン数推定（バックエンドの _estimate_tokens と同じロジック）
 */
export function estimateTokens(text: string): number {
  let japaneseChars = 0
  for (const char of text) {
    const codePoint = char.codePointAt(0)
    if (codePoint !== undefined && codePoint > 0x3000) {
      japaneseChars++
    }
  }
  const otherChars = text.length - japaneseChars
  return Math.floor(japaneseChars * 1.5 + otherChars * 0.25)
}
