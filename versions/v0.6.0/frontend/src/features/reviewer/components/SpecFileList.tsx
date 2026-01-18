import { useState } from 'react'
import type { DesignFile, ConversionTool } from '../types'

interface SpecFileListProps {
  files: DesignFile[]
  availableTools: ConversionTool[]
  specTypesList: string[]
  specMarkdown: string | null
  specStatus: string
  isConverting: boolean
  onMainChange: (filename: string) => void
  onTypeChange: (filename: string, type: string) => void
  onToolChange: (filename: string, tool: string) => void
  onApplyToolToAll: (tool: string) => void
  onConvert: () => void
  onDownload: () => void
}

export function SpecFileList({
  files,
  availableTools,
  specTypesList,
  specMarkdown,
  specStatus,
  isConverting,
  onMainChange,
  onTypeChange,
  onToolChange,
  onApplyToolToAll,
  onConvert,
  onDownload,
}: SpecFileListProps) {
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)

  if (files.length === 0) return null

  return (
    <div className="mb-2">
      {/* Detail settings header */}
      <div className="flex justify-between items-center mb-1">
        <p className="text-xs text-gray-500">詳細設定</p>
        {/* Bulk settings */}
        {availableTools.length >= 1 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">一括設定:</span>
            <div className="flex gap-1">
              {availableTools.map((tool) => (
                <button
                  key={tool.name}
                  onClick={() => onApplyToolToAll(tool.name)}
                  className="px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50"
                >
                  {tool.display_name}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* File list */}
      <div className="space-y-2">
        {files.map((file) => (
          <div
            key={file.filename}
            className="flex flex-col gap-1 text-sm bg-gray-50 border border-gray-200 rounded px-3 py-2"
          >
            <span className="text-gray-700 break-words">{file.filename}</span>
            <div className="flex flex-wrap items-center gap-2">
              <label className="flex items-center gap-1 cursor-pointer">
                <input
                  type="radio"
                  name="main-spec"
                  checked={file.isMain}
                  onChange={() => onMainChange(file.filename)}
                  className="w-4 h-4 text-blue-600 cursor-pointer"
                />
                <span className="text-xs text-gray-500 font-bold">メイン</span>
              </label>
              <span className="text-xs text-gray-500 ml-2">種別</span>
              <select
                value={file.type}
                onChange={(e) => onTypeChange(file.filename, e.target.value)}
                className="border border-gray-300 rounded px-2 py-1 text-sm"
              >
                {specTypesList.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
              <span className="text-xs text-gray-500">ツール</span>
              <select
                value={file.tool}
                onChange={(e) => onToolChange(file.filename, e.target.value)}
                className="border border-gray-300 rounded px-2 py-1 text-sm"
              >
                {availableTools.map((t) => (
                  <option key={t.name} value={t.name}>
                    {t.display_name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        ))}
      </div>

      <p className="text-xs text-gray-400 mt-2">
        ※
        メイン設計書を対象に突合し、それ以外は必要に応じて参照されます。種別ごとの注意事項が変換後マークダウンに付与されます。特別な処理を指示したい場合はシステムプロンプトを編集してください。
      </p>

      {/* Action buttons */}
      <div className="flex items-center gap-2 flex-wrap mt-3">
        <button
          onClick={onConvert}
          disabled={isConverting || files.length === 0}
          className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm transition disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          マークダウンに変換
        </button>
        <button
          onClick={onDownload}
          disabled={!specMarkdown}
          className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm transition disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          📥 ダウンロード
        </button>
        <span className="text-sm text-gray-500">{specStatus}</span>
      </div>

      <ul className="text-xs text-gray-400 mt-2 list-disc list-inside space-y-0.5">
        <li>
          MarkItDown:{' '}
          <a
            href="https://github.com/microsoft/markitdown"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-500 hover:underline"
          >
            Microsoft MarkItDown
          </a>
          の仕様に準拠した変換を行います
        </li>
        <li>excel2md: シート全体をCSVブロックとして変換します</li>
      </ul>

      {/* Preview */}
      {specMarkdown && (
        <div className="mt-3">
          <button
            onClick={() => setIsPreviewOpen(!isPreviewOpen)}
            className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-800"
          >
            <span className={`transition-transform ${isPreviewOpen ? '' : ''}`}>
              {isPreviewOpen ? '▼' : '▶'}
            </span>
            <span>変換結果をプレビュー</span>
          </button>
          {isPreviewOpen && (
            <div className="mt-2">
              <div className="bg-gray-50 border border-gray-200 rounded-md p-3 max-h-64 overflow-auto">
                <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
                  {specMarkdown}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
