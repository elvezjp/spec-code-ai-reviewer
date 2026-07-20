import type { AppInfo } from '../../../types'

interface ProgramInfoSectionProps {
  appInfo: AppInfo
}

export function ProgramInfoSection({ appInfo }: ProgramInfoSectionProps) {
  return (
    <div className="mb-6">
      <h3 className="text-sm font-medium text-gray-700 mb-2">プログラム情報</h3>
      <div className="p-4 bg-gray-50 rounded-lg text-sm text-gray-600 space-y-1">
        <p>
          <span className="font-medium">プログラム名:</span> {appInfo.name}
        </p>
        <p>
          <span className="font-medium">バージョン:</span> {appInfo.version}
        </p>
        {appInfo.description && (
          <p>
            <span className="font-medium">説明:</span> {appInfo.description}
          </p>
        )}
        {appInfo.copyright && (
          <p className="text-xs text-gray-500 mt-2">
            {appInfo.copyright}
            {appInfo.url && (
              <>
                {' '}
                (
                <a
                  href={appInfo.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-500 hover:underline"
                >
                  {appInfo.url}
                </a>
                )
              </>
            )}
          </p>
        )}
      </div>
    </div>
  )
}
