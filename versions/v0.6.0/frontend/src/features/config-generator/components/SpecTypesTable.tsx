import { X, Plus } from 'lucide-react'
import type { SpecType } from '@core/types'
import {
  Card,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
} from '@core/index'
import { CONFIG_SCHEMA } from '../schema/configSchema'

interface SpecTypesTableProps {
  specTypes: SpecType[]
  onSpecTypeChange: (index: number, field: keyof SpecType, value: string) => void
  onSpecTypeAdd: () => void
  onSpecTypeRemove: (index: number) => void
}

export function SpecTypesTable({
  specTypes,
  onSpecTypeChange,
  onSpecTypeAdd,
  onSpecTypeRemove,
}: SpecTypesTableProps) {
  const section = CONFIG_SCHEMA.sections.find((s) => s.id === 'specTypes')

  if (!section || section.outputFormat !== 'table') {
    return null
  }

  const columns = 'columns' in section ? section.columns : []

  return (
    <Card>
      <h2 className="text-lg font-bold text-gray-800 mb-1">■ {section.title}</h2>
      <p className="text-sm text-gray-500 mb-4">{section.description}</p>

      <div className="overflow-x-auto">
        <Table bordered>
          <TableHead>
            <TableRow>
              {columns.map((col) => (
                <TableHeaderCell
                  key={col.id}
                  bordered
                  style={col.width ? { width: col.width } : undefined}
                >
                  {col.label}
                </TableHeaderCell>
              ))}
              <TableHeaderCell bordered className="w-10" />
            </TableRow>
          </TableHead>
          <TableBody>
            {specTypes.map((row, index) => (
              <TableRow key={index} className="align-top">
                {columns.map((col) => (
                  <TableCell key={col.id} bordered className="p-0">
                    <input
                      type="text"
                      value={row[col.id as keyof SpecType] || ''}
                      onChange={(e) =>
                        onSpecTypeChange(index, col.id as keyof SpecType, e.target.value)
                      }
                      className="w-full px-4 py-2 border-0 focus:ring-2 focus:ring-blue-500"
                    />
                  </TableCell>
                ))}
                <TableCell bordered className="text-center">
                  <button
                    type="button"
                    onClick={() => onSpecTypeRemove(index)}
                    className="text-red-500 hover:text-red-700 px-2 py-1"
                    title="削除"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <button
        type="button"
        onClick={onSpecTypeAdd}
        className="mt-3 text-blue-500 hover:text-blue-700 text-sm flex items-center gap-1"
      >
        <Plus className="w-4 h-4" /> 行を追加
      </button>
    </Card>
  )
}
