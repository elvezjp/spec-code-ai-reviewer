import type { SpecType } from '@core/types'
import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '@core/index'

interface SpecTypesSectionProps {
  specTypes: SpecType[]
}

export function SpecTypesSection({ specTypes }: SpecTypesSectionProps) {
  return (
    <div className="mb-6 border-t border-solid border-gray-200 pt-6">
      <h3 className="text-sm font-medium text-gray-700 mb-3">■ 設計書種別と注意事項</h3>

      <div className="overflow-x-auto">
        <Table className="min-w-full text-sm">
          <TableHead>
            <TableRow>
              <TableHeaderCell className="w-1/4">種別</TableHeaderCell>
              <TableHeaderCell>注意事項</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {specTypes.map((item) => (
              <TableRow key={item.type}>
                <TableCell>{item.type}</TableCell>
                <TableCell className="text-gray-600 text-xs">{item.note}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
