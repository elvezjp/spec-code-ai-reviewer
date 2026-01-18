import { useState } from 'react'
import type { CodeFile } from '../types'

interface CodeFileListProps {
  files: CodeFile[]
  codeWithLineNumbers: string | null
  codeStatus: string
  isConverting: boolean
  onConvert: () => void
  onDownload: () => void
}

export function CodeFileList({
  files,
  codeWithLineNumbers,
  codeStatus,
  isConverting,
  onConvert,
  onDownload,
}: CodeFileListProps) {
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)

  return (
    <div>
      {/* Action buttons */}
      <div className="flex items-center gap-2 flex-wrap">
        <button
          onClick={onConvert}
          disabled={isConverting || files.length === 0}
          className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm transition disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          add-line-numbersで変換
        </button>
        <button
          onClick={onDownload}
          disabled={!codeWithLineNumbers}
          className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm transition disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          📥 ダウンロード
        </button>
        <span className="text-sm text-gray-500">{codeStatus}</span>
      </div>

      <p className="text-xs text-gray-400 mt-2">
        ※{' '}
        <a
          href="https://github.com/elvezjp/add-line-numbers"
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-500 hover:underline"
        >
          add-line-numbers
        </a>{' '}
        の仕様に準拠した変換を行います
      </p>

      {/* Preview */}
      {codeWithLineNumbers && (
        <div className="mt-3">
          <button
            onClick={() => setIsPreviewOpen(!isPreviewOpen)}
            className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-800"
          >
            <span>{isPreviewOpen ? '▼' : '▶'}</span>
            <span>変換結果をプレビュー</span>
          </button>
          {isPreviewOpen && (
            <div className="mt-2">
              <div className="bg-gray-50 border border-gray-200 rounded-md p-3 max-h-64 overflow-auto">
                <pre className="text-xs text-gray-700 whitespace-pre font-mono">
                  {codeWithLineNumbers}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
