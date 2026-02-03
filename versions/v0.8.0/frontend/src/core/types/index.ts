// 画面状態
export type ScreenState = 'main' | 'executing' | 'result'

// アプリケーション情報
export interface AppInfo {
  name: string
  version: string
  description?: string
  copyright?: string
  url?: string
}

// LLMプロバイダー
export type LlmProvider = 'anthropic' | 'bedrock' | 'openai'

// LLM設定
export interface LlmSettings {
  provider: LlmProvider
  apiKey?: string
  accessKeyId?: string
  secretAccessKey?: string
  region?: string
  maxTokens: number
  models: string[]
  selectedModel?: string
}

// 設計書種別
export interface SpecType {
  type: string
  note: string
}

// プリセット専用プロンプト
export interface PresetPrompt {
  role: string
  purpose: string
  format: string
  notes: string
}

// システムプロンプトプリセット
export interface SystemPromptPreset {
  name: string
  role: string
  purpose: string
  format: string
  notes: string
}

// プリセット
export interface Preset {
  id: string
  name: string
  description: string
  tags: string[]
  systemPrompt: PresetPrompt
  specTypes: SpecType[]
}

// 設定ファイル（reviewer-config.md のパース結果）
export interface ReviewerConfig {
  info?: {
    version: string
    created_at: string
  }
  llm?: LlmSettings
  specTypes?: SpecType[]
  systemPrompts?: SystemPromptPreset[]
}

// 共通設定
export interface Settings {
  llm: LlmSettings
  specTypes: SpecType[]
  systemPrompts: SystemPromptPreset[]
}

// バージョン情報
export interface VersionInfo {
  value: string
  label: string
  isLatest: boolean
}

// ファイル情報（変換用）
export interface FileWithMetadata {
  file: File
  filename: string
  isMain?: boolean
  specType?: string
  tool?: string
}

// 変換済みファイル
export interface ConvertedFile {
  filename: string
  originalFilename: string
  content: string
  specType?: string
  isMain?: boolean
}

// レビュー結果
export interface ReviewResult {
  runNumber: 1 | 2
  report: string
  timestamp: string
  model: string
  inputTokens?: number
  outputTokens?: number
}

// レビュー実行データ
export interface ReviewData {
  specMarkdown: string
  codeWithLineNumbers: string
  systemPrompt: string
  results: ReviewResult[]
}
