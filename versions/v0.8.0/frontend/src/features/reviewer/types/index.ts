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

// =============================================================================
// Split Types (v0.8.0)
// =============================================================================

export type SplitMode = 'batch' | 'split'

export interface SplitSettings {
  documentMode: SplitMode
  documentMaxDepth: number // 1-6
  codeMode: SplitMode
}

export interface DocumentPart {
  section: string
  level: number
  path: string
  startLine: number
  endLine: number
  content: string
  estimatedTokens: number
}

export interface CodePart {
  symbol: string
  symbolType: string // class, method, function
  parentSymbol: string | null
  startLine: number
  endLine: number
  content: string
  estimatedTokens: number
}

export interface SplitMarkdownRequest {
  content: string
  filename: string
  maxDepth: number
}

export interface SplitMarkdownResponse {
  success: boolean
  parts: DocumentPart[]
  indexContent?: string
  error?: string
}

export interface SplitCodeRequest {
  content: string
  filename: string
}

export interface SplitCodeResponse {
  success: boolean
  parts: CodePart[]
  indexContent?: string
  language?: string
  error?: string
}

export interface SplitPreviewResult {
  documentParts: DocumentPart[] | null
  codeParts: CodePart[] | null
  documentIndex: string | null
  codeIndex: string | null
  codeLanguage: string | null
}

export interface PartsReviewRequest {
  documentParts?: DocumentPart[]
  codeParts?: CodePart[]
  systemPrompt: SystemPromptValues
  llmConfig?: LlmConfig
  executedAt?: string
}

export interface PartsReviewProgress {
  sessionId: string
  status: 'running' | 'completed' | 'error'
  totalPhases: number
  currentPhase: number
  phaseName: string
  totalPairs: number
  completedPairs: number
  partialResults: string[]
  error?: string
}

export interface PartsReviewResponse {
  success: boolean
  sessionId?: string
  report?: string
  reviewMeta?: ReviewMeta
  error?: string
}
