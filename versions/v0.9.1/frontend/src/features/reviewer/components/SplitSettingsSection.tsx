import { useState, useCallback, useEffect, useRef } from 'react'
import { ChevronDown, ChevronRight, Loader2 } from 'lucide-react'
import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '@core/index'
import type { SplitSettings, SplitMode, DocumentSplitMode, DocumentPart, CodePart, SplitPreviewResult } from '../types'

interface SplitSettingsSectionProps {
  settings: SplitSettings
  onSettingsChange: (settings: SplitSettings) => void
  onShowToast: (message: string) => void
  previewResult: SplitPreviewResult | null
  onExecutePreview: () => Promise<void>
  onClearPreview: () => void
  isExecuting: boolean
  hasDesignDoc: boolean
  hasCodeFiles: boolean
  codeFilenames: string[]
  pinnedDocPartIds: string[]
  onTogglePinnedDocPart: (partId: string) => void
  isSummarizing: boolean
  summarizingPartIds: Set<string>
  hasPendingSummarize: boolean
  summarizeError: string | null
  onToggleSummarizeMode: (partId: string) => void
  onExecuteSummarize: () => void
  previewError?: string | null
}

export function SplitSettingsSection({
  settings,
  onSettingsChange,
  onShowToast,
  previewResult,
  onExecutePreview,
  onClearPreview,
  isExecuting,
  hasDesignDoc,
  hasCodeFiles,
  codeFilenames,
  pinnedDocPartIds,
  onTogglePinnedDocPart,
  isSummarizing,
  summarizingPartIds,
  hasPendingSummarize,
  summarizeError,
  onToggleSummarizeMode,
  onExecuteSummarize,
  previewError,
}: SplitSettingsSectionProps) {
  const [isOptionsExpanded, setIsOptionsExpanded] = useState(true)
  const prevHasDesignDocRef = useRef(hasDesignDoc)
  const prevHasCodeFilesRef = useRef(hasCodeFiles)

  // 設計書またはプログラムがdisabledになったらプレビューをクリア
  useEffect(() => {
    const prevHasDesignDoc = prevHasDesignDocRef.current
    const prevHasCodeFiles = prevHasCodeFilesRef.current

    // 設計書がenabled→disabledになった場合、または
    // プログラムがenabled→disabledになった場合にクリア
    if ((prevHasDesignDoc && !hasDesignDoc) || (prevHasCodeFiles && !hasCodeFiles)) {
      if (previewResult) {
        onClearPreview()
      }
    }

    prevHasDesignDocRef.current = hasDesignDoc
    prevHasCodeFilesRef.current = hasCodeFiles
  }, [hasDesignDoc, hasCodeFiles, previewResult, onClearPreview])

  // 対応言語を判定
  const supportedCodeFiles = codeFilenames.filter(name => {
    const ext = name.toLowerCase().split('.').pop()
    return ext === 'py' || ext === 'java'
  })
  const unsupportedCodeFiles = codeFilenames.filter(name => {
    const ext = name.toLowerCase().split('.').pop()
    return ext !== 'py' && ext !== 'java'
  })

  const handleReviewModeChange = useCallback((mode: SplitMode) => {
    if (mode === 'split' && unsupportedCodeFiles.length > 0) {
      onShowToast('非対応言語のプログラムが含まれています。分割レビュー方式は選択できません。')
      onSettingsChange({ ...settings, reviewMode: 'batch' })
      return
    }
    onSettingsChange({ ...settings, reviewMode: mode })
    if (mode === 'split') {
      setIsOptionsExpanded(true)
    }
  }, [settings, onSettingsChange, onShowToast, unsupportedCodeFiles.length])

  const handleDepthChange = useCallback((depth: number) => {
    onSettingsChange({ ...settings, documentMaxDepth: depth })
  }, [settings, onSettingsChange])

  const handleSplitModeChange = useCallback((mode: DocumentSplitMode) => {
    onSettingsChange({ ...settings, documentSplitMode: mode })
  }, [settings, onSettingsChange])

  const isSplitEnabled = settings.reviewMode === 'split'
  const canExecutePreview = isSplitEnabled && hasDesignDoc && hasCodeFiles

  useEffect(() => {
    if (settings.reviewMode === 'split' && unsupportedCodeFiles.length > 0) {
      onShowToast('非対応言語のプログラムが含まれています。分割レビュー方式は選択できません。')
      onSettingsChange({ ...settings, reviewMode: 'batch' })
    }
  }, [settings, unsupportedCodeFiles.length, onSettingsChange, onShowToast])

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-800">分割設定</h2>
      <p className="text-xs text-gray-400 mt-2 mb-4">
        設計書やプログラムが大きくAIのトークン上限を超える場合、分割してレビューできます。
      </p>

      {/* 分割モード選択 */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-gray-700 w-24">レビュー方式:</span>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="reviewMode"
              checked={settings.reviewMode === 'batch'}
              onChange={() => handleReviewModeChange('batch')}
              className="w-4 h-4 text-blue-600"
            />
            <span className="text-sm text-gray-700">一括</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="reviewMode"
              checked={settings.reviewMode === 'split'}
              onChange={() => handleReviewModeChange('split')}
              className="w-4 h-4 text-blue-600"
              disabled={!hasDesignDoc || !hasCodeFiles || unsupportedCodeFiles.length > 0}
            />
            <span className="text-sm text-gray-700">分割</span>
          </label>
          <span className="text-xs text-gray-400 ml-2">
            ※{' '}
            <a href="https://github.com/elvezjp/md2map" target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
              md2map
            </a>
            {' '}と{' '}
            <a href="https://github.com/elvezjp/code2map" target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
              code2map
            </a>
            {' '}の仕様に準拠し、解析と分割を行います。
          </span>
        </div>
        {unsupportedCodeFiles.length > 0 && (
          <div className="text-xs text-amber-600">
            ※ 非対応言語のプログラムが含まれているため、分割は選択できません。
          </div>
        )}
      </div>

      {/* 分割オプション */}
      {isSplitEnabled && (
        <div className="mb-4">
          <button
            type="button"
            onClick={() => setIsOptionsExpanded(!isOptionsExpanded)}
            className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900"
          >
            {isOptionsExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            分割オプション
          </button>
          {isOptionsExpanded && (
            <div className="mt-2 p-3 bg-gray-50 rounded border border-gray-200 space-y-3">
              {/* 設計書オプション */}
              {settings.reviewMode === 'split' && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">設計書</p>
                  {/* 分割モード選択 */}
                  <div className="mb-3">
                    <span className="text-sm text-gray-600">分割モード:</span>
                    <div className="mt-1 ml-2 space-y-1">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="splitMode"
                          checked={settings.documentSplitMode === 'heading'}
                          onChange={() => handleSplitModeChange('heading')}
                          className="w-4 h-4 text-blue-600"
                        />
                        <span className="text-sm text-gray-700 w-20">見出し</span>
                        <span className="text-xs text-gray-400">見出し（H2/H3等）の区切りで機械的に分割します</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="splitMode"
                          checked={settings.documentSplitMode === 'nlp'}
                          onChange={() => handleSplitModeChange('nlp')}
                          className="w-4 h-4 text-blue-600"
                        />
                        <span className="text-sm text-gray-700 w-20">NLP</span>
                        <span className="text-xs text-gray-400">見出しに加えて自然言語処理で意味的な区切りを検出して分割します</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="splitMode"
                          checked={settings.documentSplitMode === 'ai'}
                          onChange={() => handleSplitModeChange('ai')}
                          className="w-4 h-4 text-blue-600"
                        />
                        <span className="text-sm text-gray-700 w-20">AI（推奨）</span>
                        <span className="text-xs text-gray-400">見出しに加えてAIが文脈を考慮して適切に分割を行います</span>
                      </label>
                    </div>
                  </div>
                  {/* 見出しレベル選択 */}
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-600">見出しレベル:</span>
                    <label className="flex items-center gap-1 cursor-pointer">
                      <input
                        type="radio"
                        name="docDepth"
                        checked={settings.documentMaxDepth === 2}
                        onChange={() => handleDepthChange(2)}
                        className="w-4 h-4 text-blue-600"
                      />
                      <span className="text-sm text-gray-700">H2(##)まで（推奨）</span>
                    </label>
                    <label className="flex items-center gap-1 cursor-pointer">
                      <input
                        type="radio"
                        name="docDepth"
                        checked={settings.documentMaxDepth === 3}
                        onChange={() => handleDepthChange(3)}
                        className="w-4 h-4 text-blue-600"
                      />
                      <span className="text-sm text-gray-700">H3(###)まで</span>
                    </label>
                    <label className="flex items-center gap-1 cursor-pointer">
                      <input
                        type="radio"
                        name="docDepth"
                        checked={settings.documentMaxDepth === 4}
                        onChange={() => handleDepthChange(4)}
                        className="w-4 h-4 text-blue-600"
                      />
                      <span className="text-sm text-gray-700">H4(####)まで</span>
                    </label>
                  </div>
                </div>
              )}

              {/* プログラムオプション */}
              {settings.reviewMode === 'split' && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">プログラム</p>
                  <div className="text-sm text-gray-600">
                    <p>対応言語: Python (.py) / Java (.java)</p>
                    {supportedCodeFiles.length > 0 && (
                      <p className="mt-1 text-green-600">
                        対応ファイル: {supportedCodeFiles.join(', ')}
                      </p>
                    )}
                    {unsupportedCodeFiles.length > 0 && (
                      <p className="mt-1 text-amber-600">
                        未対応ファイル: {unsupportedCodeFiles.join(', ')}（分割できません）
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 分割プレビュー実行ボタン */}
      {isSplitEnabled && (
        <div className="mb-4 space-y-2">
          <div className="flex items-center gap-3">
            <button
              onClick={onExecutePreview}
              disabled={!canExecutePreview || isExecuting || !!previewResult}
              className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm transition disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {isExecuting ? (
                <>
                  <Loader2 className="w-4 h-4 inline mr-1 animate-spin" />
                  プレビュー実行中...
                </>
              ) : previewResult ? (
                'プレビュー実行済み'
              ) : (
                '分割プレビュー'
              )}
            </button>
            {settings.documentSplitMode === 'ai' && (
              <span className="text-xs text-muted text-gray-400">
                ※ 設計書が大きい場合は、処理に時間が掛かったり、タイムアウトや制限等でエラーになる可能性があります。
              </span>
            )}
          </div>
          {/* プレビューエラー */}
          {previewError && (
            <p className="text-sm text-red-600">{previewError}</p>
          )}
          {/* 要約実行ボタン */}
          {previewResult && previewResult.documentParts && (
            <SummarizeExecuteRow
              parts={previewResult.documentParts}
              isSummarizing={isSummarizing}
              hasPendingSummarize={hasPendingSummarize}
              summarizeError={summarizeError}
              onExecuteSummarize={onExecuteSummarize}
            />
          )}
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
              <ul className="text-xs text-gray-500 mb-2 list-disc list-inside space-y-0.5">
                <li><strong>重要</strong>: 分割レビュー時に全てのグループで参照されます。</li>
                <li><strong>要約</strong>: レビュー時に要約テキストで代替されます。分割後もトークン数が多い場合に使用してください。</li>
              </ul>
              <DocumentPartsTable
                parts={previewResult.documentParts}
                pinnedDocPartIds={pinnedDocPartIds}
                onTogglePinnedDocPart={onTogglePinnedDocPart}
                onToggleSummarizeMode={onToggleSummarizeMode}
                summarizingPartIds={summarizingPartIds}
              />
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

function DocumentPartsTable({
  parts,
  pinnedDocPartIds,
  onTogglePinnedDocPart,
  onToggleSummarizeMode,
  summarizingPartIds,
}: {
  parts: DocumentPart[]
  pinnedDocPartIds: string[]
  onTogglePinnedDocPart: (partId: string) => void
  onToggleSummarizeMode: (partId: string) => void
  summarizingPartIds: Set<string>
}) {
  return (
    <div className="overflow-x-auto">
      <Table className="min-w-full text-sm">
        <TableHead>
          <TableRow>
            <TableHeaderCell className="w-14">重要</TableHeaderCell>
            <TableHeaderCell className="w-14">要約</TableHeaderCell>
            <TableHeaderCell className="w-12">#</TableHeaderCell>
            <TableHeaderCell>セクション名</TableHeaderCell>
            <TableHeaderCell className="w-24">行範囲</TableHeaderCell>
            <TableHeaderCell className="w-28">推定トークン</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {parts.map((part, index) => {
            const isSummarizingThis = summarizingPartIds.has(part.id)
            return (
              <TableRow key={`${part.id}-${part.startLine}`}>
                {/* 重要チェックボックス */}
                <TableCell className="text-center">
                  <input
                    type="checkbox"
                    checked={pinnedDocPartIds.includes(part.id)}
                    onChange={() => onTogglePinnedDocPart(part.id)}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                </TableCell>
                {/* 要約チェックボックス */}
                <TableCell className="text-center">
                  <input
                    type="checkbox"
                    checked={part.summarizeMode === 'summarize'}
                    onChange={() => onToggleSummarizeMode(part.id)}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                </TableCell>
                <TableCell>{index + 1}</TableCell>
                <TableCell>
                  {part.displayName}
                  {/* 要約完了時のプレビューアコーディオン */}
                  {part.summarizedContent && part.summarizeMode === 'summarize' && (
                    <SummarizedTextPreview text={part.summarizedContent} />
                  )}
                </TableCell>
                <TableCell className="text-gray-600">
                  L{part.startLine}-L{part.endLine}
                </TableCell>
                {/* 推定トークン: 選択モードに応じた表示 */}
                <TableCell className="text-gray-600">
                  {isSummarizingThis ? (
                    <span className="text-blue-600">⟳ 要約中</span>
                  ) : part.summarizeMode === 'summarize' ? (
                    part.summarizedContent && part.summarizedTokens ? (
                      <span>~{part.summarizedTokens.toLocaleString()}</span>
                    ) : (
                      <span className="text-amber-600">未実行</span>
                    )
                  ) : (
                    <span>~{part.estimatedTokens.toLocaleString()}</span>
                  )}
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}

function SummarizeExecuteRow({
  parts,
  isSummarizing,
  hasPendingSummarize,
  summarizeError,
  onExecuteSummarize,
}: {
  parts: DocumentPart[]
  isSummarizing: boolean
  hasPendingSummarize: boolean
  summarizeError: string | null
  onExecuteSummarize: () => void
}) {
  const totalSelected = parts.filter((p) => p.summarizeMode === 'summarize').length
  const completedCount = parts.filter((p) => p.summarizeMode === 'summarize' && p.summarizedContent).length

  if (totalSelected === 0) return null

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-3">
        <button
          onClick={onExecuteSummarize}
          disabled={!hasPendingSummarize || isSummarizing}
          className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm transition disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {isSummarizing ? (
            <>
              <Loader2 className="w-4 h-4 inline mr-1 animate-spin" />
              要約実行中...
            </>
          ) : (
            '選択した要約を実行'
          )}
        </button>
        <span className="text-xs text-gray-600">
          {completedCount}/{totalSelected}件
        </span>
        {summarizeError ? (
          <span className="text-xs text-red-600">{summarizeError}</span>
        ) : (
          <span className="text-xs text-gray-400">
            「要約」を選択したセクションを事前に要約します。
          </span>
        )}
      </div>
      <p className="text-xs text-amber-600">
        ※ 要約によって微妙なニュアンスや制約が失われることがあるため、品質検証が必要です。
      </p>
    </div>
  )
}

function SummarizedTextPreview({ text }: { text: string }) {
  const [isExpanded, setIsExpanded] = useState(false)
  return (
    <div className="mt-1">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
      >
        {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        要約結果を表示
      </button>
      {isExpanded && (
        <div className="mt-1 p-2 bg-gray-50 border border-gray-200 rounded text-xs text-gray-700 whitespace-pre-wrap max-h-40 overflow-y-auto">
          {text}
        </div>
      )}
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
