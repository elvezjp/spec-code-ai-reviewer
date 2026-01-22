import { AlertTriangle } from 'lucide-react'
import type { OrganizeMarkdownWarning } from '../types'

interface OrganizerAlertsProps {
  error?: { code?: string; message: string } | null
  warnings?: OrganizeMarkdownWarning[]
}

const formatErrorTitle = (code?: string) => {
  switch (code) {
    case 'token_limit':
      return 'トークン超過'
    case 'api_error':
      return 'APIエラー'
    case 'format_invalid':
      return '形式不正'
    case 'timeout':
      return 'タイムアウト'
    case 'input_empty':
      return '入力不足'
    case 'policy_empty':
      return '方針未入力'
    default:
      return 'エラー'
  }
}

export function OrganizerAlerts({ error, warnings = [] }: OrganizerAlertsProps) {
  if (!error && warnings.length === 0) return null

  return (
    <div className="space-y-2">
      {error && (
        <div className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          <AlertTriangle className="w-4 h-4 mt-0.5" />
          <div>
            <div className="font-semibold">{formatErrorTitle(error.code)}</div>
            <div>{error.message}</div>
          </div>
        </div>
      )}
      {warnings.length > 0 && (
        <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700">
          <div className="flex items-center gap-2 font-semibold mb-1">
            <AlertTriangle className="w-4 h-4" />
            警告
          </div>
          <ul className="list-disc list-inside space-y-1">
            {warnings.map((warning, index) => (
              <li key={`${warning.code}-${index}`}>{warning.message}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
