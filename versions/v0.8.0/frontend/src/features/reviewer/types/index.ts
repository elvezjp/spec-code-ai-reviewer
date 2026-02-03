// Reviewer feature types

export interface DesignFile {
  file: File
  filename: string
  isMain: boolean
  type: string
  tool: string
  markdown?: string
  note?: string
}

export interface CodeFile {
  file: File
  filename: string
  contentWithLineNumbers?: string
}

export interface ConversionTool {
  name: string
  display_name: string
}

export interface ReviewResult {
  report: string
  reviewMeta: ReviewMeta
}

export interface ReviewMeta {
  version: string
  modelId: string
  executedAt: string
  inputTokens: number
  outputTokens: number
  designs: DesignFileMeta[]
  programs: ProgramFileMeta[]
}

export interface DesignFileMeta {
  filename: string
  role: string
  type: string
  tool: string
}

export interface ProgramFileMeta {
  filename: string
}

export interface ReviewExecutionData {
  systemPrompt: SystemPromptValues
  specMarkdown: string
  codeWithLineNumbers: string
  report: string
  reviewMeta: ReviewMeta
}

export interface SystemPromptValues {
  role: string
  purpose: string
  format: string
  notes: string
}

export interface SimpleJudgment {
  status: 'ok' | 'warning' | 'ng' | 'unknown'
  ngCount: number
  warningCount: number
  okCount: number
}

export interface LlmConfig {
  provider: 'anthropic' | 'openai' | 'bedrock'
  model: string
  maxTokens: number
  apiKey?: string
  accessKeyId?: string
  secretAccessKey?: string
  region?: string
}

export interface MarkdownSourceInfo {
  filename: string
  tool: string
}

export interface OrganizeMarkdownRequest {
  markdown: string
  policy: string
  source?: MarkdownSourceInfo
  llmConfig?: LlmConfig
}

export interface OrganizeMarkdownWarning {
  code: string
  message: string
}

export interface OrganizeMarkdownResponse {
  success: boolean
  organizedMarkdown?: string
  warnings?: OrganizeMarkdownWarning[]
  error?: string
  errorCode?: string
}

export interface ReviewerState {
  // Files
  specFiles: DesignFile[]
  codeFiles: CodeFile[]

  // Conversion results
  specMarkdown: string | null
  codeWithLineNumbers: string | null

  // Available tools
  availableTools: ConversionTool[]

  // Review results (2 executions)
  reviewResults: (ReviewExecutionData | null)[]

  // UI state
  isConverting: boolean
  isReviewing: boolean
  currentTab: number
}

export interface ReviewRequest {
  specMarkdown: string
  specFilename: string
  codeWithLineNumbers: string
  codeFilename: string
  designs: DesignFileForApi[]
  codes: CodeFileForApi[]
  systemPrompt: SystemPromptValues
  executedAt: string
  executionNumber: number
  llmConfig?: LlmConfig
}

export interface DesignFileForApi {
  filename: string
  content: string
  role: string
  isMain: boolean
  type: string
  tool: string
  note: string
}

export interface CodeFileForApi {
  filename: string
  contentWithLineNumbers: string
}

// ============================================================
// 段階的要約 API 型定義
// ============================================================

export interface Chunk {
  id: string // "chunk-0001" 形式
  title: string // 見出しテキスト or ファイル名+クラス/関数名
  text: string // チャンク本文
  tokenCount: number // 推定トークン数
}

export type ChunkStatus = 'pending' | 'processing' | 'completed' | 'error'

export interface ChunkWithStatus extends Chunk {
  status: ChunkStatus
  error?: string
}

export type ProgressiveSummaryStatus =
  | 'idle'
  | 'splitting'
  | 'ready'
  | 'summarizing'
  | 'stopped'
  | 'completed'
  | 'error'

export interface ProgressiveSummaryState {
  type: 'spec' | 'code'
  chunks: ChunkWithStatus[]
  currentIndex: number // -1 = not started
  currentSummary: string
  totalTokenCount: number
  status: ProgressiveSummaryStatus
  error: string | null
}

export interface SplitChunksRequest {
  type: 'spec' | 'code'
  markdown: string
  sourceFilenames: string[]
}

export interface SplitChunksResponse {
  success: boolean
  chunks: Chunk[]
  totalTokenCount: number
  error?: string
}

export interface ProgressiveSummaryRequest {
  type: 'spec' | 'code'
  chunk: { id: string; title: string; text: string }
  chunkOutline: string
  currentSummary: string
  policy: string
  llmConfig?: LlmConfig
}

export interface ProgressiveSummaryResponse {
  success: boolean
  chunkSummary?: string
  updatedSummary?: string
  error?: string
}
