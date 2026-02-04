import { useState, useCallback } from 'react'
import { ChevronDown, ChevronRight, Loader2 } from 'lucide-react'
import { Button, Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '@core/index'
import type { SplitSettings, SplitMode, DocumentPart, CodePart, SplitPreviewResult } from '../types'

interface SplitSettingsSectionProps {
  settings: SplitSettings
  onSettingsChange: (settings: SplitSettings) => void
  previewResult: SplitPreviewResult | null
  onExecutePreview: () => Promise<void>
  isExecuting: boolean
  hasDesignDoc: boolean
  hasCodeFiles: boolean
  codeFilenames: string[]
}

export function SplitSettingsSection({
  settings,
  onSettingsChange,
  previewResult,
  onExecutePreview,
  isExecuting,
  hasDesignDoc,
  hasCodeFiles,
  codeFilenames,
}: SplitSettingsSectionProps) {
  const [isDocOptionsExpanded, setIsDocOptionsExpanded] = useState(false)
  const [isCodeOptionsExpanded, setIsCodeOptionsExpanded] = useState(false)

  const handleDocModeChange = useCallback((mode: SplitMode) => {
    onSettingsChange({ ...settings, documentMode: mode })
    if (mode === 'split') {
      setIsDocOptionsExpanded(true)
    }
  }, [settings, onSettingsChange])

  const handleCodeModeChange = useCallback((mode: SplitMode) => {
    onSettingsChange({ ...settings, codeMode: mode })
    if (mode === 'split') {
      setIsCodeOptionsExpanded(true)
    }
  }, [settings, onSettingsChange])

  const handleDepthChange = useCallback((depth: number) => {
    onSettingsChange({ ...settings, documentMaxDepth: depth })
  }, [settings, onSettingsChange])

  const isSplitEnabled = settings.documentMode === 'split' || settings.codeMode === 'split'
  const canExecutePreview = isSplitEnabled && (
    (settings.documentMode === 'split' && hasDesignDoc) ||
    (settings.codeMode === 'split' && hasCodeFiles)
  )

  // 対応言語を判定
  const supportedCodeFiles = codeFilenames.filter(name => {
    const ext = name.toLowerCase().split('.').pop()
    return ext === 'py' || ext === 'java'
  })
  const unsupportedCodeFiles = codeFilenames.filter(name => {
    const ext = name.toLowerCase().split('.').pop()
    return ext !== 'py' && ext !== 'java'
  })

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-medium text-gray-900 mb-4">6. 分割設定</h2>

      {/* 分割モード選択 */}
      <div className="space-y-4 mb-6">
        {/* 設計書 */}
        <div className="flex items-center gap-6">
          <span className="text-sm font-medium text-gray-700 w-24">設計書:</span>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="docMode"
              checked={settings.documentMode === 'batch'}
              onChange={() => handleDocModeChange('batch')}
              className="w-4 h-4 text-blue-600"
              disabled={!hasDesignDoc}
            />
            <span className="text-sm text-gray-700">一括</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="docMode"
              checked={settings.documentMode === 'split'}
              onChange={() => handleDocModeChange('split')}
              className="w-4 h-4 text-blue-600"
              disabled={!hasDesignDoc}
            />
            <span className="text-sm text-gray-700">分割</span>
          </label>
        </div>

        {/* プログラム */}
        <div className="flex items-center gap-6">
          <span className="text-sm font-medium text-gray-700 w-24">プログラム:</span>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="codeMode"
              checked={settings.codeMode === 'batch'}
              onChange={() => handleCodeModeChange('batch')}
              className="w-4 h-4 text-blue-600"
              disabled={!hasCodeFiles}
            />
            <span className="text-sm text-gray-700">一括</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="codeMode"
              checked={settings.codeMode === 'split'}
              onChange={() => handleCodeModeChange('split')}
              className="w-4 h-4 text-blue-600"
              disabled={!hasCodeFiles}
            />
            <span className="text-sm text-gray-700">分割</span>
          </label>
        </div>
      </div>

      {/* 設計書分割オプション */}
      {settings.documentMode === 'split' && (
        <div className="mb-4">
          <button
            type="button"
            onClick={() => setIsDocOptionsExpanded(!isDocOptionsExpanded)}
            className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900"
          >
            {isDocOptionsExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            設計書分割オプション
          </button>
          {isDocOptionsExpanded && (
            <div className="mt-2 ml-5 p-3 bg-gray-50 rounded border border-gray-200">
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600">分割深度:</span>
                <label className="flex items-center gap-1 cursor-pointer">
                  <input
                    type="radio"
                    name="docDepth"
                    checked={settings.documentMaxDepth === 2}
                    onChange={() => handleDepthChange(2)}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="text-sm text-gray-700">H2まで（推奨）</span>
                </label>
                <label className="flex items-center gap-1 cursor-pointer">
                  <input
                    type="radio"
                    name="docDepth"
                    checked={settings.documentMaxDepth === 3}
                    onChange={() => handleDepthChange(3)}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="text-sm text-gray-700">H3まで</span>
                </label>
                <label className="flex items-center gap-1 cursor-pointer">
                  <input
                    type="radio"
                    name="docDepth"
                    checked={settings.documentMaxDepth === 4}
                    onChange={() => handleDepthChange(4)}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="text-sm text-gray-700">H4まで</span>
                </label>
              </div>
            </div>
          )}
        </div>
      )}

      {/* プログラム分割オプション */}
      {settings.codeMode === 'split' && (
        <div className="mb-4">
          <button
            type="button"
            onClick={() => setIsCodeOptionsExpanded(!isCodeOptionsExpanded)}
            className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900"
          >
            {isCodeOptionsExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            プログラム分割オプション
          </button>
          {isCodeOptionsExpanded && (
            <div className="mt-2 ml-5 p-3 bg-gray-50 rounded border border-gray-200">
              <div className="text-sm text-gray-600">
                <p>対応言語: Python (.py) / Java (.java)</p>
                {supportedCodeFiles.length > 0 && (
                  <p className="mt-1 text-green-600">
                    対応ファイル: {supportedCodeFiles.join(', ')}
                  </p>
                )}
                {unsupportedCodeFiles.length > 0 && (
                  <p className="mt-1 text-amber-600">
                    未対応ファイル: {unsupportedCodeFiles.join(', ')}（一括処理されます）
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 分割プレビュー実行ボタン */}
      {isSplitEnabled && (
        <div className="flex justify-center mb-4">
          <Button
            onClick={onExecutePreview}
            disabled={!canExecutePreview || isExecuting}
            variant="primary"
          >
            {isExecuting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                プレビュー実行中...
              </>
            ) : previewResult ? (
              '分割プレビュー実行 ✓ 実行済み'
            ) : (
              '分割プレビュー実行'
            )}
          </Button>
        </div>
      )}

      {/* プレビュー結果 */}
      {previewResult && (
        <div className="border-t border-gray-200 pt-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">プレビュー結果</h3>

          {/* 設計書パーツ */}
          {previewResult.documentParts && previewResult.documentParts.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-600 mb-2">
                ■ 設計書: {previewResult.documentParts.length} パート
              </h4>
              <DocumentPartsTable parts={previewResult.documentParts} />
            </div>
          )}

          {/* コードパーツ */}
          {previewResult.codeParts && previewResult.codeParts.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-2">
                ■ プログラム: {previewResult.codeParts.length} パート
                {previewResult.codeLanguage && (
                  <span className="ml-2 text-xs text-gray-500">
                    ({previewResult.codeLanguage})
                  </span>
                )}
              </h4>
              <CodePartsTable parts={previewResult.codeParts} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function DocumentPartsTable({ parts }: { parts: DocumentPart[] }) {
  return (
    <div className="overflow-x-auto">
      <Table className="min-w-full text-sm">
        <TableHead>
          <TableRow>
            <TableHeaderCell className="w-12">#</TableHeaderCell>
            <TableHeaderCell>セクション名</TableHeaderCell>
            <TableHeaderCell className="w-24">行範囲</TableHeaderCell>
            <TableHeaderCell className="w-28">推定トークン</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {parts.map((part, index) => (
            <TableRow key={`${part.section}-${part.startLine}`}>
              <TableCell>{index + 1}</TableCell>
              <TableCell>{part.section}</TableCell>
              <TableCell className="text-gray-600">L{part.startLine}-L{part.endLine}</TableCell>
              <TableCell className="text-gray-600">~{part.estimatedTokens.toLocaleString()}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

function CodePartsTable({ parts }: { parts: CodePart[] }) {
  return (
    <div className="overflow-x-auto">
      <Table className="min-w-full text-sm">
        <TableHead>
          <TableRow>
            <TableHeaderCell className="w-12">#</TableHeaderCell>
            <TableHeaderCell>シンボル名</TableHeaderCell>
            <TableHeaderCell className="w-20">種別</TableHeaderCell>
            <TableHeaderCell className="w-24">行範囲</TableHeaderCell>
            <TableHeaderCell className="w-28">推定トークン</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {parts.map((part, index) => (
            <TableRow key={`${part.symbol}-${part.startLine}`}>
              <TableCell>{index + 1}</TableCell>
              <TableCell>
                {part.parentSymbol ? `${part.parentSymbol}#${part.symbol}` : part.symbol}
              </TableCell>
              <TableCell className="text-gray-600">{part.symbolType}</TableCell>
              <TableCell className="text-gray-600">L{part.startLine}-L{part.endLine}</TableCell>
              <TableCell className="text-gray-600">~{part.estimatedTokens.toLocaleString()}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
