import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '@core/index'
import type { HeadingInfo } from '../types'

interface PreImportantPanelProps {
  headings: HeadingInfo[]
  selectedStartLines: number[]
  onToggle: (startLine: number) => void
  isLoading: boolean
}

export function PreImportantPanel({
  headings,
  selectedStartLines,
  onToggle,
  isLoading,
}: PreImportantPanelProps) {
  if (isLoading) {
    return (
      <div className="p-3 bg-gray-50 border border-gray-200 rounded">
        <p className="text-sm font-semibold text-gray-700 mb-2">事前重要指定</p>
        <p className="text-sm text-gray-500">見出し一覧を取得中...</p>
      </div>
    )
  }

  if (headings.length === 0) {
    return null
  }

  return (
    <div className="p-3 bg-gray-50 border border-gray-200 rounded">
      <p className="text-sm font-semibold text-gray-700 mb-2">事前重要指定</p>
      <p className="text-xs text-gray-400 mb-2">
        設計書の見出し（H2）単位でセクションを表示しています。事前重要指定するセクションにチェックを入れてください。
      </p>
      <div className="overflow-x-auto">
        <Table className="min-w-full text-sm">
          <TableHead>
            <TableRow>
              <TableHeaderCell className="w-20">事前重要指定</TableHeaderCell>
              <TableHeaderCell className="w-12">#</TableHeaderCell>
              <TableHeaderCell>セクション名</TableHeaderCell>
              <TableHeaderCell className="w-24">行範囲</TableHeaderCell>
              <TableHeaderCell className="w-24">推定文字数</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {headings.map((heading, index) => (
              <TableRow key={`heading-${heading.startLine}`}>
                <TableCell className="text-center">
                  <input
                    type="checkbox"
                    checked={selectedStartLines.includes(heading.startLine)}
                    onChange={() => onToggle(heading.startLine)}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                </TableCell>
                <TableCell>{index + 1}</TableCell>
                <TableCell>{heading.title}</TableCell>
                <TableCell className="text-gray-600">
                  L{heading.startLine}-L{heading.endLine}
                </TableCell>
                <TableCell className="text-gray-600">
                  ~{heading.estimatedChars.toLocaleString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
