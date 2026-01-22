import { useEffect, useMemo, useState } from 'react'
import { Sparkles, ChevronDown, ChevronRight } from 'lucide-react'
import ReactDiffViewer from 'react-diff-viewer-continued'
import type { LlmConfig, OrganizeMarkdownWarning } from '../types'
import { organizeMarkdown } from '../services/api'
import { OrganizerAlerts } from './OrganizerAlerts'

interface MarkdownOrganizerProps {
  specMarkdown: string | null
  llmConfig?: LlmConfig
  onAdopt: (markdown: string) => void
}

const DEFAULT_POLICY = `以下のルールでMarkdownを構造化してください。
- 要約や推測は禁止。原文の意味を変えない。
- 内容を「要件」「条件」「例外」「境界値」「前提」に再分類する。
- 見出しは原文の章立てを維持し、各項目に原文参照IDを付与する。
- 表は「入力/条件/出力/備考」の構造に変換する。`

const normalizeForSectionDiff = (markdown: string): string => {
  const lines = markdown.split('\n')
  const sections: string[] = []
  let current: string[] = []

  const flush = () => {
    if (current.length > 0) {
      sections.push(current.join('\n'))
      current = []
    }
  }

  for (const line of lines) {
    if (/^#{1,3}\s+/.test(line)) {
      flush()
      current.push(line)
      continue
    }

    if (current.length === 0) {
      current.push('## (見出しなし)')
    }
    current.push(line)
  }

  flush()
  return sections.join('\n\n---\n\n')
}

export function MarkdownOrganizer({ specMarkdown, llmConfig, onAdopt }: MarkdownOrganizerProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [policy, setPolicy] = useState(DEFAULT_POLICY)
  const [organizedMarkdown, setOrganizedMarkdown] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [status, setStatus] = useState('')
  const [warnings, setWarnings] = useState<OrganizeMarkdownWarning[]>([])
  const [error, setError] = useState<{ code?: string; message: string } | null>(null)
  const [viewMode, setViewMode] = useState<'section' | 'line'>('section')
  const [splitView, setSplitView] = useState(true)
  const [sourceMarkdown, setSourceMarkdown] = useState<string | null>(specMarkdown)

  useEffect(() => {
    setOrganizedMarkdown(null)
    setStatus('')
    setWarnings([])
    setError(null)
    setSourceMarkdown(specMarkdown)
  }, [specMarkdown])

  const oldValue = useMemo(() => {
    if (!sourceMarkdown) return ''
    return viewMode === 'section' ? normalizeForSectionDiff(sourceMarkdown) : sourceMarkdown
  }, [sourceMarkdown, viewMode])

  const newValue = useMemo(() => {
    if (!organizedMarkdown) return ''
    return viewMode === 'section'
      ? normalizeForSectionDiff(organizedMarkdown)
      : organizedMarkdown
  }, [organizedMarkdown, viewMode])

  const handleOrganize = async () => {
    if (!specMarkdown || !policy.trim()) return

    setIsProcessing(true)
    setStatus('整理中...')
    setWarnings([])
    setError(null)
    setSourceMarkdown(specMarkdown)

    try {
      const result = await organizeMarkdown({
        markdown: specMarkdown,
        policy,
        llmConfig,
      })

      if (!result.success) {
        setError({
          code: result.errorCode,
          message: result.error || '整理に失敗しました',
        })
        setStatus('❌ 整理に失敗しました')
        return
      }

      setOrganizedMarkdown(result.organizedMarkdown || '')
      setWarnings(result.warnings || [])
      setStatus('✅ 整理済み')
    } catch (error) {
      const message = error instanceof Error ? error.message : '整理に失敗しました'
      setError({ message })
      setStatus(`❌ ${message}`)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleAdopt = () => {
    if (!organizedMarkdown) return
    onAdopt(organizedMarkdown)
    setStatus('✅ 整理結果を採用しました')
  }

  const handleDiscard = () => {
    setOrganizedMarkdown(null)
    setWarnings([])
    setError(null)
    setStatus('整理結果を破棄しました')
  }

  return (
    <div className="mt-4 border-t border-gray-200 pt-3">
      <div className="flex items-center justify-between gap-2">
        <button
          onClick={() => setIsOpen((prev) => !prev)}
          disabled={!specMarkdown}
          className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900 disabled:text-gray-400 disabled:cursor-not-allowed"
        >
          <Sparkles className="w-4 h-4" />
          AIでMarkdownを整理する
          {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </button>
        {!specMarkdown && (
          <span className="text-xs text-gray-400">※ 変換済みMarkdownが必要です</span>
        )}
      </div>

      {isOpen && (
        <div className="mt-3 space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              整理方針
            </label>
            <textarea
              value={policy}
              onChange={(e) => setPolicy(e.target.value)}
              rows={6}
              className="w-full text-xs border border-gray-300 rounded-md p-2 font-mono"
              placeholder="整理方針を入力してください"
            />
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={handleOrganize}
              disabled={!specMarkdown || !policy.trim() || isProcessing}
              className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm transition disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              整理を実行
            </button>
            <span className="text-sm text-gray-500">{status}</span>
          </div>

          <OrganizerAlerts error={error} warnings={warnings} />

          {organizedMarkdown && (
            <div>
              <div className="flex items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">表示:</span>
                  <button
                    onClick={() => setViewMode('section')}
                    className={`px-2 py-1 text-xs rounded border ${
                      viewMode === 'section'
                        ? 'bg-blue-50 text-blue-700 border-blue-200'
                        : 'bg-white text-gray-600 border-gray-200'
                    }`}
                  >
                    セクション
                  </button>
                  <button
                    onClick={() => setViewMode('line')}
                    className={`px-2 py-1 text-xs rounded border ${
                      viewMode === 'line'
                        ? 'bg-blue-50 text-blue-700 border-blue-200'
                        : 'bg-white text-gray-600 border-gray-200'
                    }`}
                  >
                    行
                  </button>
                </div>
                <label className="text-xs text-gray-500 flex items-center gap-1">
                  <input
                    type="checkbox"
                    checked={splitView}
                    onChange={(e) => setSplitView(e.target.checked)}
                  />
                  左右表示
                </label>
              </div>
              <div className="border border-gray-200 rounded-md overflow-auto max-h-[420px]">
                <ReactDiffViewer
                  oldValue={oldValue}
                  newValue={newValue}
                  splitView={splitView}
                  showDiffOnly={false}
                  leftTitle="整理前Markdown"
                  rightTitle="整理後Markdown"
                />
              </div>
              <div className="flex items-center gap-2 mt-3">
                <button
                  onClick={handleAdopt}
                  className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm transition"
                >
                  採用
                </button>
                <button
                  onClick={handleDiscard}
                  className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-3 py-1 rounded text-sm transition"
                >
                  破棄
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
