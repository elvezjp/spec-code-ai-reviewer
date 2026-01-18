import type { SpecType } from '@core/types'

interface SpecTypesSectionProps {
  specTypes: SpecType[]
}

export function SpecTypesSection({ specTypes }: SpecTypesSectionProps) {
  return (
    <div className="mb-6 border-t border-gray-200 pt-6">
      <h3 className="text-sm font-medium text-gray-700 mb-3">■ 設計書種別と注意事項</h3>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm border border-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left text-gray-600 border-b w-1/4">種別</th>
              <th className="px-3 py-2 text-left text-gray-600 border-b">注意事項</th>
            </tr>
          </thead>
          <tbody>
            {specTypes.map((item) => (
              <tr key={item.type}>
                <td className="px-3 py-2 border-b text-gray-800">{item.type}</td>
                <td className="px-3 py-2 border-b text-gray-600 text-xs">{item.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
