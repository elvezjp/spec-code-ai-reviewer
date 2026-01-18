import { Button, Card } from '@core/index'
import { CONFIG_SCHEMA } from '../schema/configSchema'

interface DownloadButtonProps {
  onDownload: () => void
}

export function DownloadButton({ onDownload }: DownloadButtonProps) {
  return (
    <Card>
      <Button variant="primary" onClick={onDownload} className="w-full py-4 text-lg font-bold flex items-center justify-center gap-3">
        <span className="text-2xl">📥</span>
        <span>{CONFIG_SCHEMA.meta.outputFileName} をダウンロード</span>
      </Button>
    </Card>
  )
}
