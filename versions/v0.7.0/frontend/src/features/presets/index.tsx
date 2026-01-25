import { useMemo, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { ChevronDown, ChevronRight } from 'lucide-react'
import {
  Layout,
  Header,
  Card,
  Button,
  usePresetCatalog,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
} from '@core/index'
import { useReviewerSettings } from '@/features/reviewer/hooks'
import type { Preset } from '@core/types'

export function Presets() {
  const navigate = useNavigate()
  const { applyPreset } = useReviewerSettings()
  const {
    filteredPresets,
    tags,
    selectedTag,
    setSelectedTag,
    query,
    setQuery,
    resetFilters,
  } = usePresetCatalog()
  const [expandedPresets, setExpandedPresets] = useState<Set<string>>(new Set())
  const [expandedSpecTypes, setExpandedSpecTypes] = useState<Set<string>>(new Set())

  const handleApply = (preset: Preset) => {
    applyPreset(preset)
    sessionStorage.setItem('preset-toast', `プリセット「${preset.name}」を適用しました`)
    navigate('/')
  }

  const togglePreset = (presetId: string) => {
    setExpandedPresets((prev) => {
      const next = new Set(prev)
      if (next.has(presetId)) {
        next.delete(presetId)
      } else {
        next.add(presetId)
      }
      return next
    })
  }

  const toggleSpecTypes = (presetId: string) => {
    setExpandedSpecTypes((prev) => {
      const next = new Set(prev)
      if (next.has(presetId)) {
        next.delete(presetId)
      } else {
        next.add(presetId)
      }
      return next
    })
  }

  const tagButtons = useMemo(() => {
    return tags.map((tag) => {
      const isActive = tag === selectedTag
      const displayName = tag === 'all' ? 'すべて' : tag
      return (
        <button
          key={tag}
          onClick={() => setSelectedTag(tag)}
          aria-pressed={isActive}
          aria-label={`${displayName}でフィルタ`}
          className={`rounded-full px-3 py-1 text-sm border transition focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            isActive
              ? 'bg-blue-600 text-white border-blue-600'
              : 'bg-white text-gray-700 border-gray-200 hover:border-gray-300'
          }`}
        >
          {displayName}
        </button>
      )
    })
  }, [tags, selectedTag, setSelectedTag])

  return (
    <Layout>
      <Header
        title="プリセットライブラリ"
        subtitle="用途に合わせたプリセットをワンクリックで適用できます。"
        rightContent={
          <Link to="/" className="text-blue-600 hover:text-blue-800 text-sm">
            ← レビュー画面に戻る
          </Link>
        }
      />

      <Card className="mb-6">
        <div className="flex flex-col gap-4">
          <div className="flex flex-col md:flex-row md:items-center gap-3">
            <label htmlFor="preset-search" className="sr-only">
              プリセットをキーワードで検索
            </label>
            <input
              id="preset-search"
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="キーワードで検索"
              aria-label="プリセットをキーワードで検索"
              className="w-full md:flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
            <Button variant="secondary" onClick={resetFilters}>
              フィルタをリセット
            </Button>
          </div>
          <div className="flex flex-wrap gap-2" role="group" aria-label="タグフィルタ">
            {tagButtons}
          </div>
        </div>
      </Card>

      {filteredPresets.length === 0 ? (
        <Card>
          <p className="text-gray-600 text-sm">該当するプリセットがありません。</p>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          {filteredPresets.map((preset) => (
            <Card key={preset.id} className="flex flex-col gap-4">
              <div>
                <h2 className="text-lg font-semibold text-gray-800">{preset.name}</h2>
                <p className="text-sm text-gray-600 mt-1">{preset.description}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {preset.tags.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full bg-gray-100 text-gray-600 px-2 py-1 text-xs"
                  >
                    {tag}
                  </span>
                ))}
              </div>
              <div className="text-sm text-gray-700 space-y-2">
                <div>
                  <button
                    onClick={() => togglePreset(preset.id)}
                    aria-expanded={expandedPresets.has(preset.id)}
                    aria-controls={`preset-details-${preset.id}`}
                    aria-label={`${preset.name}のシステムプロンプト詳細を${expandedPresets.has(preset.id) ? '閉じる' : '表示'}`}
                    className="flex items-center gap-2 w-full text-left font-medium text-gray-800 hover:text-gray-900 transition focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
                  >
                    {expandedPresets.has(preset.id) ? (
                      <ChevronDown className="w-4 h-4" aria-hidden="true" />
                    ) : (
                      <ChevronRight className="w-4 h-4" aria-hidden="true" />
                    )}
                    <span>システムプロンプトを見る</span>
                  </button>
                  {expandedPresets.has(preset.id) && (
                    <div
                      id={`preset-details-${preset.id}`}
                      role="region"
                      aria-label={`${preset.name}のシステムプロンプト詳細`}
                      className="mt-2"
                    >
                      <div className="bg-gray-50 border border-gray-200 rounded-md p-3 max-h-64 overflow-auto">
                        <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
{`## 役割
${preset.systemPrompt.role}

## 目的
${preset.systemPrompt.purpose}

## フォーマット
${preset.systemPrompt.format}

## 注意事項
${preset.systemPrompt.notes}`}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
                <div>
                  <button
                    onClick={() => toggleSpecTypes(preset.id)}
                    aria-expanded={expandedSpecTypes.has(preset.id)}
                    aria-controls={`preset-spectypes-${preset.id}`}
                    aria-label={`${preset.name}の設計書種別を${expandedSpecTypes.has(preset.id) ? '閉じる' : '表示'}`}
                    className="flex items-center gap-2 w-full text-left font-medium text-gray-800 hover:text-gray-900 transition focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
                  >
                    {expandedSpecTypes.has(preset.id) ? (
                      <ChevronDown className="w-4 h-4" aria-hidden="true" />
                    ) : (
                      <ChevronRight className="w-4 h-4" aria-hidden="true" />
                    )}
                    <span>設計書種別と注意事項を見る</span>
                  </button>
                  {expandedSpecTypes.has(preset.id) && (
                    <div
                      id={`preset-spectypes-${preset.id}`}
                      role="region"
                      aria-label={`${preset.name}の設計書種別`}
                      className="mt-2 overflow-x-auto"
                    >
                      <Table className="min-w-full text-sm">
                        <TableHead>
                          <TableRow>
                            <TableHeaderCell className="w-1/4">種別</TableHeaderCell>
                            <TableHeaderCell>注意事項</TableHeaderCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {preset.specTypes.map((specType, index) => (
                            <TableRow key={index}>
                              <TableCell>{specType.type}</TableCell>
                              <TableCell className="text-gray-600 text-xs">{specType.note}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </div>
              </div>
              <div className="flex justify-end">
                <Button onClick={() => handleApply(preset)}>このプリセットを使う</Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </Layout>
  )
}

export default Presets
