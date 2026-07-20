import { Download } from 'lucide-react'
import { Button, Card } from '@core/index'
import { CONFIG_SCHEMA } from '../schema/configSchema'

interface DownloadButtonProps {
  onDownload: () => void
}

export function DownloadButton({ onDownload }: DownloadButtonProps) {
  return (
    <Card>
      <Button variant="primary" size="lg" onClick={onDownload} className="flex items-center justify-center gap-3">
        <Download className="w-6 h-6" />
        <span>{CONFIG_SCHEMA.meta.outputFileName} をダウンロード</span>
      </Button>
    </Card>
  )
}
