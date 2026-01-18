import { useState } from 'react'
import type { SystemPromptPreset } from '@core/types'
import { Card } from '@core/index'
import { CONFIG_SCHEMA } from '../schema/configSchema'

interface SystemPromptsSectionProps {
  systemPrompts: SystemPromptPreset[]
  onSystemPromptChange: (index: number, field: keyof SystemPromptPreset, value: string) => void
  onSystemPromptAdd: () => void
  onSystemPromptRemove: (index: number) => void
}

export function SystemPromptsSection({
  systemPrompts,
  onSystemPromptChange,
  onSystemPromptAdd,
  onSystemPromptRemove,
}: SystemPromptsSectionProps) {
  const [collapsedItems, setCollapsedItems] = useState<Set<number>>(new Set())

  const section = CONFIG_SCHEMA.sections.find((s) => s.id === 'systemPrompts')

  if (!section || section.outputFormat !== 'sections') {
    return null
  }

  const fields = 'fields' in section ? section.fields : []
  const otherFields = fields.filter((f) => f.id !== 'name')

  const toggleCollapse = (index: number) => {
    setCollapsedItems((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(index)) {
        newSet.delete(index)
      } else {
        newSet.add(index)
      }
      return newSet
    })
  }

  return (
    <Card>
      <h2 className="text-lg font-bold text-gray-800 mb-1">■ {section.title}</h2>
      <p className="text-sm text-gray-500 mb-4">{section.description}</p>

      <div className="space-y-4">
        {systemPrompts.map((item, index) => {
          const isCollapsed = collapsedItems.has(index)

          return (
            <div key={index} className="border border-gray-200 rounded-lg overflow-hidden">
              {/* ヘッダー（プリセット名と削除ボタン） */}
              <div className="bg-gray-50 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1">
                  <button
                    type="button"
                    onClick={() => toggleCollapse(index)}
                    className="text-gray-500 hover:text-gray-700 transition"
                  >
                    {isCollapsed ? '▶' : '▼'}
                  </button>
                  <input
                    type="text"
                    value={item.name || ''}
                    placeholder="プリセット名を入力"
                    onChange={(e) => onSystemPromptChange(index, 'name', e.target.value)}
                    className="flex-1 px-3 py-1 border border-gray-300 rounded-md text-sm font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => onSystemPromptRemove(index)}
                  className="text-red-500 hover:text-red-700 px-2 py-1 text-lg ml-2"
                  title="削除"
                >
                  ×
                </button>
              </div>

              {/* コンテンツ（各フィールド） */}
              {!isCollapsed && (
                <div className="p-4 space-y-4">
                  {otherFields.map((field) => (
                    <div key={field.id}>
                      <label className="block text-sm font-medium text-gray-700 mb-1">{field.label}</label>
                      <textarea
                        rows={field.rows || 3}
                        value={item[field.id as keyof SystemPromptPreset] || ''}
                        onChange={(e) =>
                          onSystemPromptChange(index, field.id as keyof SystemPromptPreset, e.target.value)
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-y"
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      <button
        type="button"
        onClick={onSystemPromptAdd}
        className="mt-4 text-blue-500 hover:text-blue-700 text-sm flex items-center gap-1"
      >
        <span>+</span> プリセットを追加
      </button>
    </Card>
  )
}
