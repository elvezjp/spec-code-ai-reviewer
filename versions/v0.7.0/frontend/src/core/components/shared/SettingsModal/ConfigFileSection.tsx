import { FileDropzone } from '../../ui/FileDropzone'
import { Button } from '../../ui/Button'

interface ConfigFileSectionProps {
  onFileLoad: (content: string, filename: string) => void
  onSaveToBrowser: () => void
  onClearSaved: () => void
  loadedFilename?: string
  loadStatus?: {
    llm?: string
    specTypes?: string
    prompts?: string
  }
  generatorUrl?: string
  isSavedToBrowser?: boolean
  isModified?: boolean
}

export function ConfigFileSection({
  onFileLoad,
  onSaveToBrowser,
  onClearSaved,
  loadedFilename,
  loadStatus,
  generatorUrl = '/config-file-generator',
  isSavedToBrowser = false,
  isModified = false,
}: ConfigFileSectionProps) {
  // loadedFilenameがあれば読み込み済みとみなす
  const isLoaded = !!loadedFilename

  const handleFilesSelect = async (files: File[]) => {
    if (files.length === 0) return

    const file = files[0]
    const content = await file.text()
    onFileLoad(content, file.name)
  }

  const handleClearSaved = () => {
    if (window.confirm('ブラウザに保存された設定をクリアしますか？')) {
      onClearSaved()
    }
  }

  // 保存ステータスメッセージを生成
  const getSaveStatusMessage = (): { text: string; className: string } | null => {
    if (!isSavedToBrowser) {
      return null
    }
    if (isModified) {
      return {
        text: '設定が変更されています（保存していません）',
        className: 'text-sm text-orange-600',
      }
    }
    return {
      text: 'ブラウザに設定が保存されています（次回自動読込）',
      className: 'text-sm text-green-600',
    }
  }

  const saveStatus = getSaveStatusMessage()

  return (
    <div className="mb-6 border-t border-gray-200 pt-6">
      <h3 className="text-sm font-medium text-gray-700 mb-2">■ 設定ファイル</h3>

      {/* 設定ファイルジェネレーターへのリンク */}
      <div className="mb-4">
        <p className="text-sm text-gray-600 mb-2">
          マークダウンで設定を一括管理します。
        </p>
        <a
          href={generatorUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full px-4 py-2 text-sm text-center bg-blue-500 hover:bg-blue-600 text-white rounded transition"
        >
          設定ファイルジェネレーターで作成
        </a>
      </div>

      {/* ファイルアップロード領域 */}
      <FileDropzone
        onFilesSelect={handleFilesSelect}
        accept=".md"
        className="mb-3"
      >
        {isLoaded && loadedFilename ? (
          <div className="text-left">
            <p className="text-gray-700 font-medium mb-1">{loadedFilename}</p>
            {loadStatus?.llm && (
              <p className={`text-sm ${loadStatus.llm.includes('更新しました') || loadStatus.llm.includes('読み込みました') ? 'text-green-600' : 'text-gray-500'}`}>
                {loadStatus.llm}
              </p>
            )}
            {loadStatus?.specTypes && (
              <p className={`text-sm ${loadStatus.specTypes.includes('更新しました') || loadStatus.specTypes.includes('読み込みました') ? 'text-green-600' : 'text-gray-500'}`}>
                {loadStatus.specTypes}
              </p>
            )}
            {loadStatus?.prompts && (
              <p className={`text-sm ${loadStatus.prompts.includes('更新しました') || loadStatus.prompts.includes('読み込みました') ? 'text-green-600' : 'text-gray-500'}`}>
                {loadStatus.prompts}
              </p>
            )}
          </div>
        ) : (
          <>
            <p className="text-gray-600 mb-1">設定ファイルを選択</p>
            <p className="text-gray-400 text-sm">
              または ここにドラッグ&ドロップ
            </p>
          </>
        )}
      </FileDropzone>

      {/* 保存ステータス表示 */}
      {saveStatus && (
        <div className="mb-3">
          <p className={saveStatus.className}>{saveStatus.text}</p>
        </div>
      )}

      {/* ブラウザ保存ボタン */}
      <div className="flex gap-2 mb-2">
        <Button
          variant="secondary"
          size="sm"
          onClick={onSaveToBrowser}
          className="flex-1"
        >
          設定をブラウザに保存
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={handleClearSaved}
          className="flex-1"
        >
          保存した設定をクリア
        </Button>
      </div>
      <p className="text-xs text-gray-500 mb-1">
        ※ 保存しなくてもアップロードした設定で利用可能です。
      </p>
      <p className="text-xs text-gray-500">
        ※
        保存された設定はブラウザ拡張機能で読み込まれる場合があります。共有PCの場合は利用後に設定をクリアしてください。
      </p>
    </div>
  )
}
