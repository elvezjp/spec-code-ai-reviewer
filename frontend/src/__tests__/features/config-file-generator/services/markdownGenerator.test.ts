import { describe, it, expect } from 'vitest'
import { generateMarkdown } from '@features/config-file-generator/services/markdownGenerator'
import type { ConfigFormState } from '@features/config-file-generator/types'

function buildOpenAiFormState(overrides: Partial<ConfigFormState['llmFields']> = {}): ConfigFormState {
  return {
    provider: 'openai',
    llmFields: {
      provider: 'openai',
      apiKey: 'sk-test',
      maxTokens: 16384,
      models: ['gpt-5.2'],
      ...overrides,
    },
    specTypes: [],
    systemPrompts: [],
  }
}

describe('generateMarkdown - reasoningEffort', () => {
  it('reasoningEffort入力時に設定ファイルへ出力される', () => {
    const md = generateMarkdown(
      buildOpenAiFormState({ reasoningEffort: 'low' })
    )

    expect(md).toContain('- reasoningEffort: low')
  })

  it('reasoningEffort未入力時は出力されない', () => {
    const md = generateMarkdown(buildOpenAiFormState())

    expect(md).not.toContain('reasoningEffort')
  })

  it('baseUrlとreasoningEffortを同時に出力できる', () => {
    const md = generateMarkdown(
      buildOpenAiFormState({
        baseUrl: 'https://api.moonshot.ai/v1',
        reasoningEffort: 'low',
      })
    )

    expect(md).toContain('- baseUrl: https://api.moonshot.ai/v1')
    expect(md).toContain('- reasoningEffort: low')
  })
})
