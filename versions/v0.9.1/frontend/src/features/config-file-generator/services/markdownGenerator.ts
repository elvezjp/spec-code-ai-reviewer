import type { ConfigFormState, LlmSectionDefinition, InfoSectionDefinition, TableSectionDefinition, SectionsSectionDefinition } from '../types'
import { CONFIG_SCHEMA } from '../schema/configSchema'

// ISO 8601形式のタイムスタンプを生成
function generateTimestamp(): string {
  const now = new Date()
  const offset = -now.getTimezoneOffset()
  const offsetHours = Math.floor(Math.abs(offset) / 60)
    .toString()
    .padStart(2, '0')
  const offsetMinutes = (Math.abs(offset) % 60).toString().padStart(2, '0')
  const offsetSign = offset >= 0 ? '+' : '-'
  const tzString = `${offsetSign}${offsetHours}:${offsetMinutes}`

  const year = now.getFullYear()
  const month = (now.getMonth() + 1).toString().padStart(2, '0')
  const day = now.getDate().toString().padStart(2, '0')
  const hours = now.getHours().toString().padStart(2, '0')
  const minutes = now.getMinutes().toString().padStart(2, '0')
  const seconds = now.getSeconds().toString().padStart(2, '0')

  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}${tzString}`
}

// テーブルセル用のエスケープ
function escapeForTableCell(text: string): string {
  if (!text) return ''
  return text.replace(/\|/g, '\\|').replace(/\n/g, '<br>')
}

// infoセクションのマークダウン生成
function generateInfoSection(): string {
  const section = CONFIG_SCHEMA.sections.find((s) => s.id === 'info') as InfoSectionDefinition | undefined
  if (!section) return ''

  let md = '## info\n\n'

  section.fields.forEach((field) => {
    let value: string
    if (field.type === 'fixed') {
      value = field.value
    } else if (field.type === 'auto' && field.generator === 'timestamp_iso8601') {
      value = generateTimestamp()
    } else {
      value = ''
    }
    md += `- ${field.id}: ${value}\n`
  })

  return md + '\n'
}

// llmセクションのマークダウン生成
function generateLlmSection(formState: ConfigFormState): string {
  const section = CONFIG_SCHEMA.sections.find((s) => s.id === 'llm') as LlmSectionDefinition | undefined
  if (!section || !('conditional' in section)) return ''

  const currentCase = section.conditional.cases[formState.provider]
  let md = '## llm\n\n'

  currentCase.fields.forEach((field) => {
    const value = formState.llmFields[field.id as keyof typeof formState.llmFields]

    if (field.type === 'array') {
      md += `- ${field.id}:\n`
      if (Array.isArray(value)) {
        value.forEach((item) => {
          if (item && item.trim()) {
            md += `  - ${item}\n`
          }
        })
      }
    } else {
      md += `- ${field.id}: ${value ?? ''}\n`
    }
  })

  return md + '\n'
}

// specTypesセクションのマークダウン生成
function generateSpecTypesSection(formState: ConfigFormState): string {
  const section = CONFIG_SCHEMA.sections.find((s) => s.id === 'specTypes') as TableSectionDefinition | undefined
  if (!section || section.outputFormat !== 'table') return ''

  const columns = section.columns
  const headers = columns.map((col) => col.id)

  let md = '## specTypes\n\n'
  md += `| ${headers.join(' | ')} |\n`
  md += `|${headers.map(() => '------').join('|')}|\n`

  formState.specTypes.forEach((row) => {
    const values = headers.map((h) => escapeForTableCell(row[h as keyof typeof row] || ''))
    md += `| ${values.join(' | ')} |\n`
  })

  return md + '\n'
}

// systemPromptsセクションのマークダウン生成
function generateSystemPromptsSection(formState: ConfigFormState): string {
  const section = CONFIG_SCHEMA.sections.find((s) => s.id === 'systemPrompts') as SectionsSectionDefinition | undefined
  if (!section || section.outputFormat !== 'sections') return ''

  const itemKey = section.itemKey
  const fields = section.fields

  let md = '## systemPrompts\n\n'

  formState.systemPrompts.forEach((item) => {
    const itemName = item[itemKey as keyof typeof item] || '名称未設定'
    md += `### ${itemName}\n\n`

    fields.forEach((field) => {
      if (field.id === itemKey) return // itemKeyは見出しに使用済み
      const value = item[field.id as keyof typeof item] || ''
      md += `#### ${field.id}\n\n`
      md += `${value}\n\n`
    })
  })

  return md
}

// マークダウン全体を生成
export function generateMarkdown(formState: ConfigFormState): string {
  let md = `# ${CONFIG_SCHEMA.meta.outputTitle}\n\n`

  md += generateInfoSection()
  md += generateLlmSection(formState)
  md += generateSpecTypesSection(formState)
  md += generateSystemPromptsSection(formState)

  return md.trim() + '\n'
}

// ファイルをダウンロード
export function downloadMarkdown(content: string): void {
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)

  const a = document.createElement('a')
  a.href = url
  a.download = CONFIG_SCHEMA.meta.outputFileName
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
