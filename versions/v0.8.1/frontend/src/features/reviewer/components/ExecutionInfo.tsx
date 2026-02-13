import type { ReactNode } from 'react'
import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '@core/index'

interface DesignFileInfo {
  filename: string
  role?: string
  type?: string
  tool?: string
}

interface ProgramFileInfo {
  filename: string
}

interface ExecutionInfoProps {
  version?: string
  modelId?: string
  executedAt?: string
  inputTokens?: number
  outputTokens?: number
  designs?: DesignFileInfo[]
  programs?: ProgramFileInfo[]
  children?: ReactNode
}

export function ExecutionInfo({
  version,
  modelId,
  executedAt,
  inputTokens,
  outputTokens,
  designs,
  programs,
  children,
}: ExecutionInfoProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div className="text-gray-600">バージョン:</div>
        <div className="text-gray-800">{version || '-'}</div>
        <div className="text-gray-600">モデルID:</div>
        <div className="text-gray-800">{modelId || '-'}</div>
        <div className="text-gray-600">実行日時:</div>
        <div className="text-gray-800">{executedAt || '-'}</div>
        {(inputTokens !== undefined || outputTokens !== undefined) && (
          <>
            <div className="text-gray-600">トークン数:</div>
            <div className="text-gray-800">
              入力 {(inputTokens || 0).toLocaleString()} / 出力 {(outputTokens || 0).toLocaleString()}
            </div>
          </>
        )}
      </div>

      {designs && designs.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2">設計書:</h3>
          <div className="overflow-x-auto">
            <Table className="min-w-full text-sm">
              <TableHead>
                <TableRow>
                  <TableHeaderCell>ファイル名</TableHeaderCell>
                  <TableHeaderCell>役割</TableHeaderCell>
                  <TableHeaderCell>種別</TableHeaderCell>
                  <TableHeaderCell>ツール</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {designs.map((d) => (
                  <TableRow key={d.filename}>
                    <TableCell>{d.filename}</TableCell>
                    <TableCell>{d.role || '-'}</TableCell>
                    <TableCell>{d.type || '-'}</TableCell>
                    <TableCell>{d.tool || '-'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      )}

      {programs && programs.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2">プログラム:</h3>
          <div className="overflow-x-auto">
            <Table className="min-w-full text-sm">
              <TableHead>
                <TableRow>
                  <TableHeaderCell>ファイル名</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {programs.map((p) => (
                  <TableRow key={p.filename}>
                    <TableCell>{p.filename}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      )}

      {children && <div className="mt-4">{children}</div>}
    </div>
  )
}
