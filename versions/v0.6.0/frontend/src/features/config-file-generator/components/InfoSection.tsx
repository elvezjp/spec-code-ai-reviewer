import { Card } from '@core/index'
import { CONFIG_SCHEMA } from '../schema/configSchema'

export function InfoSection() {
  const section = CONFIG_SCHEMA.sections.find((s) => s.id === 'info')

  if (!section || section.outputFormat !== 'list' || !('fields' in section)) {
    return null
  }

  return (
    <Card>
      <h2 className="text-lg font-bold text-gray-800 mb-1">■ {section.title}</h2>
      <p className="text-sm text-gray-500 mb-4">{section.description}</p>

      <div className="space-y-3">
        {section.fields.map((field) => (
          <div key={field.id} className="flex items-center">
            <label className="w-32 text-sm font-medium text-gray-700">{field.label}:</label>
            {field.type === 'fixed' ? (
              <span className="text-gray-600">{field.value}（固定）</span>
            ) : field.type === 'auto' ? (
              <span className="text-gray-500 italic">ダウンロード時に自動生成</span>
            ) : null}
          </div>
        ))}
      </div>
    </Card>
  )
}
