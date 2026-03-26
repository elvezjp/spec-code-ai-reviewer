// API service for reviewer feature

import type {
  ConversionTool,
  ReviewRequest,
  ReviewResult,
  OrganizeMarkdownRequest,
  OrganizeMarkdownResponse,
  HeadingInfo,
  SplitMarkdownRequest,
  SplitMarkdownResponse,
  SplitCodeRequest,
  SplitCodeResponse,
  StructureMatchingRequest,
  StructureMatchingResponse,
  GroupReviewRequest,
  GroupReviewResponse,
  IntegrateRequest,
  IntegrateResponse,
  SummarizeRequest,
  SummarizeResponse,
} from '../types'

const getBackendUrl = (): string => {
  return ''
}

/**
 * レスポンスのステータスコードをチェックし、非 2xx の場合はエラーをスローする
 */
export async function assertResponseOk(response: Response, context: string): Promise<void> {
  if (!response.ok) {
    let detail = ''
    try {
      const body = await response.text()
      if (body) detail = `: ${body}`
    } catch {
      // ボディ読み取り失敗は無視
    }
    throw new Error(`${context} (HTTP ${response.status}${detail})`)
  }
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

  await assertResponseOk(response, 'Excel変換に失敗しました')
  return await response.json()
}

export async function addLineNumbers(
  file: File
): Promise<{ success: boolean; content?: string; line_count?: number; error?: string }> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${getBackendUrl()}/api/convert/add-line-numbers`, {
    method: 'POST',
    body: formData,
  })

  await assertResponseOk(response, '行番号付与に失敗しました')
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

  await assertResponseOk(response, 'レビュー実行に失敗しました')
  return await response.json()
}

export interface TestConnectionRequest {
  provider?: string
  model?: string
  apiKey?: string
  accessKeyId?: string
  secretAccessKey?: string
  region?: string
}

export interface TestConnectionResponse {
  status: 'connected' | 'error'
  provider?: string
  model?: string
  error?: string
}

export async function testLlmConnection(
  config?: TestConnectionRequest
): Promise<TestConnectionResponse> {
  const response = await fetch(`${getBackendUrl()}/api/test-connection`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config || {}),
  })

  await assertResponseOk(response, '接続テストに失敗しました')
  return await response.json()
}

export async function organizeMarkdown(
  request: OrganizeMarkdownRequest
): Promise<OrganizeMarkdownResponse> {
  const response = await fetch(`${getBackendUrl()}/api/organize-markdown`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  await assertResponseOk(response, 'マークダウン整形に失敗しました')
  return await response.json()
}

// =============================================================================
// Split API
// =============================================================================

export async function fetchHeadings(
  content: string
): Promise<{ success?: boolean; headings: HeadingInfo[]; error?: string }> {
  const response = await fetch(`${getBackendUrl()}/api/split/headings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  })

  if (!response.ok) {
    return { headings: [], error: `見出し一覧の取得に失敗しました (HTTP ${response.status})` }
  }

  return await response.json()
}

export async function splitMarkdown(
  request: SplitMarkdownRequest
): Promise<SplitMarkdownResponse> {
  const response = await fetch(`${getBackendUrl()}/api/split/markdown`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  await assertResponseOk(response, '分割処理に失敗しました')
  return await response.json()
}

export async function splitCode(
  request: SplitCodeRequest
): Promise<SplitCodeResponse> {
  const response = await fetch(`${getBackendUrl()}/api/split/code`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  await assertResponseOk(response, 'コード分割に失敗しました')
  return await response.json()
}

// =============================================================================
// Split Review APIs
// =============================================================================

export async function executeStructureMatching(
  request: StructureMatchingRequest
): Promise<StructureMatchingResponse> {
  const response = await fetch(`${getBackendUrl()}/api/review/structure-matching`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  await assertResponseOk(response, '構造マッチングに失敗しました')
  return await response.json()
}

export async function executeGroupReview(
  request: GroupReviewRequest
): Promise<GroupReviewResponse> {
  const response = await fetch(`${getBackendUrl()}/api/review/group`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  await assertResponseOk(response, 'グループレビューに失敗しました')
  return await response.json()
}

export async function executeIntegrate(
  request: IntegrateRequest
): Promise<IntegrateResponse> {
  const response = await fetch(`${getBackendUrl()}/api/review/integrate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  await assertResponseOk(response, '結果統合に失敗しました')
  return await response.json()
}

export async function executeSummarize(
  request: SummarizeRequest
): Promise<SummarizeResponse> {
  const response = await fetch(`${getBackendUrl()}/api/summarize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  await assertResponseOk(response, '要約処理に失敗しました')
  return await response.json()
}
