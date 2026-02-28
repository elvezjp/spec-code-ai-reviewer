import { describe, it, expect } from 'vitest'
import { generateReadmeMarkdown } from '@features/reviewer/services/markdown'

const baseReviewMeta = {
  version: 'v0.4.0',
  modelId: 'test-model',
  executedAt: '2024/01/01 12:00:00',
  inputTokens: 1000,
  outputTokens: 500,
}

const sampleGroups = [
  {
    groupId: 'G1',
    groupName: 'グループ1',
    docSections: [{ id: 'MD1', title: 'セクション1' }],
    codeSymbols: [{ symbol: 'MyClass' }],
    estimatedTokens: 5000,
  },
]

describe('generateReadmeMarkdown', () => {
  it('reviewMode=batchのとき「一括」が含まれる', () => {
    const result = generateReadmeMarkdown(
      { ...baseReviewMeta, reviewMode: 'batch' },
      1
    )
    expect(result).toContain('| レビューモード | 一括 |')
  })

  it('reviewMode=splitのとき「分割」が含まれる', () => {
    const result = generateReadmeMarkdown(
      { ...baseReviewMeta, reviewMode: 'split' },
      1
    )
    expect(result).toContain('| レビューモード | 分割 |')
  })

  it('reviewModeがundefinedのときレビューモード行が含まれない', () => {
    const result = generateReadmeMarkdown(
      { ...baseReviewMeta },
      1
    )
    expect(result).not.toContain('レビューモード')
  })

  it('reviewMode=splitかつgroupsがあるときグループ分け結果が含まれる', () => {
    const result = generateReadmeMarkdown(
      { ...baseReviewMeta, reviewMode: 'split', groups: sampleGroups },
      1
    )
    expect(result).toContain('### グループ分け結果')
    expect(result).toContain('| G1 | グループ1 | MD1 | MyClass | 5,000 |')
  })

  it('reviewMode=splitでgroupsが空のときグループ分け結果が含まれない', () => {
    const result = generateReadmeMarkdown(
      { ...baseReviewMeta, reviewMode: 'split', groups: [] },
      1
    )
    expect(result).not.toContain('グループ分け結果')
  })

  it('reviewMode=batchのときgroupsがあってもグループ分け結果が含まれない', () => {
    const result = generateReadmeMarkdown(
      { ...baseReviewMeta, reviewMode: 'batch', groups: sampleGroups },
      1
    )
    expect(result).not.toContain('グループ分け結果')
  })
})
