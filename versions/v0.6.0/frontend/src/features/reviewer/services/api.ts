// API service for reviewer feature

import type {
  ConversionTool,
  ReviewRequest,
  ReviewResult,
} from '../types'

const getBackendUrl = (): string => {
  return ''
}

export async function fetchAvailableTools(): Promise<ConversionTool[]> {
  try {
    const response = await fetch(`${getBackendUrl()}/api/convert/available-tools`)
    const result = await response.json()
    return result.tools || []
  } catch {
    // Fallback to default tools
    return [
      { name: 'markitdown', display_name: 'MarkItDown' },
      { name: 'excel2md', display_name: 'excel2md' },
    ]
  }
}

export async function convertExcelToMarkdown(
  file: File,
  tool: string
): Promise<{ success: boolean; markdown?: string; error?: string }> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('tool', tool)

  const response = await fetch(`${getBackendUrl()}/api/convert/excel-to-markdown`, {
    method: 'POST',
    body: formData,
  })

  return await response.json()
}

export async function addLineNumbers(
  file: File
): Promise<{ success: boolean; content?: string; error?: string }> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${getBackendUrl()}/api/convert/add-line-numbers`, {
    method: 'POST',
    body: formData,
  })

  return await response.json()
}

export async function executeReview(
  request: ReviewRequest
): Promise<{ success: boolean; report?: string; reviewMeta?: ReviewResult['reviewMeta']; error?: string }> {
  const response = await fetch(`${getBackendUrl()}/api/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  return await response.json()
}

export async function testLlmConnection(
  llmConfig: ReviewRequest['llmConfig']
): Promise<{ success: boolean; error?: string }> {
  const response = await fetch(`${getBackendUrl()}/api/llm/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ llmConfig }),
  })

  return await response.json()
}
