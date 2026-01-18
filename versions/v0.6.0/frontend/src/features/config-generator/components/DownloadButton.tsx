import { Download } from 'lucide-react'
import { Button, Card } from '@core/index'
import { CONFIG_SCHEMA } from '../schema/configSchema'

interface DownloadButtonProps {
  onDownload: () => void
}

export function DownloadButton({ onDownload }: DownloadButtonProps) {
  return (
    <Card>
      <Button variant="primary" onClick={onDownload} className="w-full py-4 text-lg font-bold flex items-center justify-center gap-3">
        <Download className="w-6 h-6" />
        <span>{CONFIG_SCHEMA.meta.outputFileName} をダウンロード</span>
      </Button>
    </Card>
  )
}
