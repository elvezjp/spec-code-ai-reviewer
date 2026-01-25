import type { LlmProvider, SpecType, SystemPromptPreset } from '@core/types'

// 設定ファイルジェネレーターのフォーム状態
export interface ConfigFormState {
  provider: LlmProvider
  llmFields: LlmFieldValues
  specTypes: SpecType[]
  systemPrompts: SystemPromptPreset[]
}

// LLMフィールドの値（プロバイダー共通）
export interface LlmFieldValues {
  provider: LlmProvider
  apiKey?: string
  accessKeyId?: string
  secretAccessKey?: string
  region?: string
  maxTokens: number
  models: string[]
}

// スキーマのメタ情報
export interface SchemaMeta {
  outputTitle: string
  outputFileName: string
  version: string
}

// フィールドタイプ
export type FieldType = 'fixed' | 'auto' | 'password' | 'text' | 'number' | 'array' | 'textarea'

// 基本フィールド定義
export interface BaseFieldDefinition {
  id: string
  label?: string
  type: FieldType
  required?: boolean
  placeholder?: string
  rows?: number
}

// 固定値フィールド
export interface FixedFieldDefinition extends BaseFieldDefinition {
  type: 'fixed'
  value: string
}

// 自動生成フィールド
export interface AutoFieldDefinition extends BaseFieldDefinition {
  type: 'auto'
  generator: 'timestamp_iso8601'
}

// テキスト/パスワードフィールド
export interface TextFieldDefinition extends BaseFieldDefinition {
  type: 'password' | 'text'
  default?: string
}

// 数値フィールド
export interface NumberFieldDefinition extends BaseFieldDefinition {
  type: 'number'
  default?: number
  min?: number
  max?: number
}

// 配列フィールド
export interface ArrayFieldDefinition extends BaseFieldDefinition {
  type: 'array'
  itemType: 'text'
  defaults: string[]
}

// フィールド定義のユニオン型
export type FieldDefinition =
  | FixedFieldDefinition
  | AutoFieldDefinition
  | TextFieldDefinition
  | NumberFieldDefinition
  | ArrayFieldDefinition

// プロバイダー固有の設定
export interface ProviderConfig {
  notes?: string[]
  fields: FieldDefinition[]
}

// 条件付きセクション（LLM用）
export interface ConditionalSection {
  switchField: string
  cases: Record<LlmProvider, ProviderConfig>
}

// テーブルカラム定義
export interface TableColumnDefinition {
  id: string
  label: string
  type: 'text' | 'textarea'
  width?: string
  rows?: number
}

// 出力フォーマット
export type OutputFormat = 'list' | 'table' | 'sections'

// セクション定義（基本）
export interface BaseSectionDefinition {
  id: string
  title: string
  description: string
  outputFormat: OutputFormat
}

// infoセクション
export interface InfoSectionDefinition extends BaseSectionDefinition {
  outputFormat: 'list'
  fields: (FixedFieldDefinition | AutoFieldDefinition)[]
}

// llmセクション（条件付き）
export interface LlmSectionDefinition extends BaseSectionDefinition {
  outputFormat: 'list'
  conditional: ConditionalSection
}

// テーブルセクション（specTypes用）
export interface TableSectionDefinition extends BaseSectionDefinition {
  outputFormat: 'table'
  columns: TableColumnDefinition[]
  defaults: SpecType[]
  editable: boolean
  minRows: number
}

// セクション形式（systemPrompts用）
export interface SectionsSectionDefinition extends BaseSectionDefinition {
  outputFormat: 'sections'
  itemKey: string
  fields: { id: string; label: string; rows?: number }[]
  defaults: SystemPromptPreset[]
  editable: boolean
  minRows: number
}

// セクション定義のユニオン型
export type SectionDefinition =
  | InfoSectionDefinition
  | LlmSectionDefinition
  | TableSectionDefinition
  | SectionsSectionDefinition

// スキーマ全体
export interface ConfigSchema {
  meta: SchemaMeta
  sections: SectionDefinition[]
}

// バリデーションエラー
export interface ValidationError {
  field: string
  message: string
}
