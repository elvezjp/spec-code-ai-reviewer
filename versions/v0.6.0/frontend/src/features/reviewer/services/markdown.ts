// Markdown generation utilities for reviewer feature

import type { DesignFile, CodeFile, SystemPromptValues } from '../types'

export function generateSpecMarkdown(
  files: DesignFile[],
  getTypeNote: (type: string) => string
): string {
  return files
    .filter((f) => f.markdown)
    .map((f) => {
      const note = getTypeNote(f.type)
      const role = f.isMain ? 'メイン' : '参照'
      return `# 設計書: ${f.filename}\n- 役割: ${role}\n- 種別: ${f.type}\n- 注意事項: ${note}\n\n${f.markdown}`
    })
    .join('\n\n---\n\n')
}

export function generateCodeWithLineNumbers(files: CodeFile[]): string {
  return files
    .filter((f) => f.contentWithLineNumbers)
    .map((f) => `# プログラム: ${f.filename}\n\n${f.contentWithLineNumbers}`)
    .join('\n\n---\n\n')
}

export function generateSystemPromptMarkdown(prompt: SystemPromptValues): string {
  return `# システムプロンプト

## 役割

${prompt.role}

## 目的

${prompt.purpose}

## 出力形式

${prompt.format}

## 注意事項

${prompt.notes}
`
}

export function generateReadmeMarkdown(
  reviewMeta: {
    version: string
    modelId: string
    executedAt: string
    inputTokens: number
    outputTokens: number
    designs?: { filename: string; role: string; type: string; tool: string }[]
    programs?: { filename: string }[]
  },
  executionNumber: number
): string {
  const designsList =
    reviewMeta.designs
      ?.map((d) => `  - ${d.filename}（${d.role} / ${d.type} / ${d.tool}）`)
      .join('\n') || '  - なし'
  const programsList =
    reviewMeta.programs?.map((p) => `  - ${p.filename}`).join('\n') || '  - なし'

  return `# レビュー実行データ（${executionNumber}回目）

このZIPファイルには、AIレビュー実行時の入出力データが含まれています。

## レビュー情報

| 項目 | 内容 |
|------|------|
| バージョン | ${reviewMeta.version || '-'} |
| モデルID | ${reviewMeta.modelId || '-'} |
| レビュー実行日時 | ${reviewMeta.executedAt || '-'} |
| 実行回数 | ${executionNumber}回目 |
| 入力トークン数 | ${(reviewMeta.inputTokens || 0).toLocaleString()} |
| 出力トークン数 | ${(reviewMeta.outputTokens || 0).toLocaleString()} |

### 設計書

${designsList}

### プログラム

${programsList}

## 同梱ファイル

| ファイル名 | 説明 |
|-----------|------|
| README.md | このファイル（レビュー情報とファイル説明） |
| system-prompt.md | システムプロンプト（役割・目的・出力形式・注意事項） |
| spec-markdown.md | 変換後の設計書（マークダウン形式） |
| code-numbered.txt | 行番号付きプログラム |
| review-result.md | AIレビュー結果 |
`
}
