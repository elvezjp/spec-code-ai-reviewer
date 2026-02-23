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
    reviewMode?: 'batch' | 'split'
    designs?: { filename: string; role: string; type: string; tool: string }[]
    programs?: { filename: string }[]
    groups?: {
      groupId: string
      groupName: string
      docSections: { id: string; title: string }[]
      codeSymbols: { symbol: string }[]
      estimatedTokens: number
    }[]
  },
  executionNumber: number,
  hasSplitData: boolean = false,
): string {
  const designsList =
    reviewMeta.designs
      ?.map((d) => `  - ${d.filename}（${d.role} / ${d.type} / ${d.tool}）`)
      .join('\n') || '  - なし'
  const programsList =
    reviewMeta.programs?.map((p) => `  - ${p.filename}`).join('\n') || '  - なし'

  const groupsSection =
    reviewMeta.reviewMode === 'split' && reviewMeta.groups && reviewMeta.groups.length > 0
      ? `### グループ分け結果

| グループID | グループ名 | 設計書セクション | コードシンボル | 推定トークン |
|-----------|-----------|----------------|--------------|------------|
${reviewMeta.groups
  .map(
    (g) =>
      `| ${g.groupId} | ${g.groupName} | ${g.docSections.map((d) => d.id).join(', ')} | ${g.codeSymbols.map((c) => c.symbol).join(', ')} | ${g.estimatedTokens.toLocaleString()} |`
  )
  .join('\n')}

`
      : ''

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
${reviewMeta.reviewMode !== undefined ? `| レビューモード | ${reviewMeta.reviewMode === 'batch' ? '一括' : '分割'} |` : ''}

### 設計書

${designsList}

### プログラム

${programsList}

${groupsSection}

## 同梱ファイル

| ファイル名 | 説明 |
|-----------|------|
| README.md | このファイル（レビュー情報とファイル説明） |
| system-prompt.md | システムプロンプト（役割・目的・出力形式・注意事項） |
| spec-markdown.md | 変換後の設計書（マークダウン形式） |
| code-numbered.txt | 行番号付きプログラム |
| review-result.md | AIレビュー結果 |
${hasSplitData ? `| split/spec-INDEX.md | 設計書の構造情報（md2map生成） |
| split/spec-MAP.json | 設計書のセクションマップ（md2map生成） |
| split/code-INDEX.md | プログラムの構造情報（code2map生成） |
| split/code-MAP.json | プログラムのシンボルマップ（code2map生成） |
` : ''}`
}
