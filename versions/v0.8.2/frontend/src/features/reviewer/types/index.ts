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
  lineCount?: number
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
// Split Types
// =============================================================================

export type SplitMode = 'batch' | 'split'

export interface SplitSettings {
  reviewMode: SplitMode
  documentMaxDepth: number // 1-6
}

export interface DocumentPart {
  id: string
  section: string
  level: number
  path: string
  startLine: number
  endLine: number
  content: string
  estimatedTokens: number
}

export interface CodePart {
  id: string
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

// =============================================================================
// Structure Matching Types
// =============================================================================

export interface DocumentStructure {
  indexMd: string
  mapJson: Record<string, unknown>
}

export interface CodeFileStructure {
  filename: string
  indexMd: string
  mapJson: Record<string, unknown>
}

export interface StructureMatchingRequest {
  document: DocumentStructure
  codeFiles: CodeFileStructure[]
  systemPrompt?: SystemPromptValues // ユーザー指定のシステムプロンプト
  llmConfig?: LlmConfig
}

export interface MatchedDocSection {
  id: string
  title: string
  path: string
}

export interface MatchedCodeSymbol {
  id: string
  filename: string
  symbol: string
}

export interface MatchedGroup {
  groupId: string
  groupName: string
  docSections: MatchedDocSection[]
  codeSymbols: MatchedCodeSymbol[]
  reason: string
  estimatedTokens: number
}

export interface StructureMatchingResponse {
  success: boolean
  groups: MatchedGroup[]
  totalGroups: number
  tokensUsed?: { input: number; output: number }
  error?: string
}

// =============================================================================
// Group Review Types
// =============================================================================

export interface GroupReviewRequest {
  groupId: string
  groupName: string
  documentContent: string // フロントエンドで結合済みの設計書内容
  codeContent: string // フロントエンドで結合済みのコード内容
  reviewOptions?: Record<string, unknown>
  systemPrompt?: SystemPromptValues // ユーザー指定のシステムプロンプト
  llmConfig?: LlmConfig
}

export interface ReviewFinding {
  id: string
  findingType: string // inconsistency, missing_in_code, missing_in_doc, suggestion
  severity: string // error, warning, info
  docLocation?: { section: string; line: number }
  codeLocation?: { filename: string; symbol: string; line: number }
  description: string
  recommendation: string
}

export interface GroupReviewResult {
  report: string // AIが生成したMarkdown形式のレビューレポート
}

export interface GroupReviewResponse {
  success: boolean
  groupId: string
  reviewResult?: GroupReviewResult
  tokensUsed?: { input: number; output: number }
  error?: string
}

// =============================================================================
// Integrate Types
// =============================================================================

export interface GroupReviewSummary {
  groupId: string
  groupName: string
  report: string // グループレビューのMarkdownレポート
}

export interface IntegrateRequest {
  structureMatching: StructureMatchingResponse
  groupReviews: GroupReviewSummary[]
  integrationOptions?: Record<string, unknown>
  systemPrompt?: SystemPromptValues // ユーザー指定のシステムプロンプト
  llmConfig?: LlmConfig
}

export interface KeyIssue {
  priority: number
  title: string
  affectedGroups: string[]
  description: string
  relatedFindings: string[]
}

export interface CrossGroupIssue {
  title: string
  groups: string[]
  description: string
}

export interface IntegratedReport {
  overallSummary: string
  consistencyScore: number
  keyIssues: KeyIssue[]
  crossGroupIssues: CrossGroupIssue[]
  statistics: Record<string, unknown>
  deduplicatedFindings: string[]
}

export interface IntegrateResponse {
  success: boolean
  report?: string // AIが生成した統合レビューレポート（Markdown形式）
  integratedReport?: IntegratedReport
  reviewMeta?: ReviewMeta // 一括レビューと同様のメタ情報
  tokensUsed?: { input: number; output: number }
  error?: string
}

// =============================================================================
// Split Review Execution State (Frontend)
// =============================================================================

export type SplitReviewPhase = 'idle' | 'structure-matching' | 'group-review' | 'integrate' | 'completed' | 'paused' | 'error'

export type GroupReviewStatus = 'pending' | 'in_progress' | 'completed' | 'error' | 'skipped'

export interface GroupReviewState {
  groupId: string
  groupName: string
  status: GroupReviewStatus
  result?: GroupReviewResult
  tokensUsed?: { input: number; output: number }
  error?: string
}

export interface SplitReviewState {
  phase: SplitReviewPhase
  structureMatchingResult?: StructureMatchingResponse
  groupReviews: GroupReviewState[]
  integrateResult?: IntegrateResponse
  currentGroupIndex: number
  error?: string
}
