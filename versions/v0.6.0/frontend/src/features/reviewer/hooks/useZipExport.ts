import { useCallback } from 'react'
import JSZip from 'jszip'
import type { ReviewExecutionData } from '../types'
import { generateSystemPromptMarkdown, generateReadmeMarkdown } from '../services/markdown'

interface UseZipExportReturn {
  downloadZip: (data: ReviewExecutionData, executionNumber: number) => Promise<void>
  downloadReport: (report: string, executionNumber: number) => void
  copyReport: (report: string) => Promise<void>
  downloadSpecMarkdown: (markdown: string) => void
  downloadCodeWithLineNumbers: (code: string) => void
}

export function useZipExport(): UseZipExportReturn {
  const downloadZip = useCallback(
    async (data: ReviewExecutionData, executionNumber: number) => {
      const zip = new JSZip()

      // Generate timestamp from executedAt (YYYY/MM/DD HH:MM:SS → YYYYMMDD-HHMMSS)
      const timestamp = data.reviewMeta.executedAt
        .replace(/[\/\s:]/g, '')
        .replace(/(\d{8})(\d{6})/, '$1-$2')
      const executionNumberFormatted = String(executionNumber).padStart(3, '0')

      // Add system prompt
      const systemPromptMd = generateSystemPromptMarkdown(data.systemPrompt)
      zip.file('system-prompt.md', systemPromptMd)

      // Add spec markdown
      zip.file('spec-markdown.md', data.specMarkdown)

      // Add code with line numbers
      zip.file('code-numbered.txt', data.codeWithLineNumbers)

      // Add review result
      zip.file('review-result.md', data.report)

      // Add README
      const readme = generateReadmeMarkdown(data.reviewMeta, executionNumber)
      zip.file('README.md', readme)

      // Generate and download
      const content = await zip.generateAsync({ type: 'blob' })
      const url = URL.createObjectURL(content)
      const a = document.createElement('a')
      a.href = url
      a.download = `${timestamp}-${executionNumberFormatted}-review-data.zip`
      a.click()
      URL.revokeObjectURL(url)
    },
    []
  )

  const downloadReport = useCallback((report: string, executionNumber: number) => {
    const blob = new Blob([report], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `review-result-${executionNumber}.md`
    a.click()
    URL.revokeObjectURL(url)
  }, [])

  const copyReport = useCallback(async (report: string) => {
    await navigator.clipboard.writeText(report)
  }, [])

  const downloadSpecMarkdown = useCallback((markdown: string) => {
    const blob = new Blob([markdown], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'spec-markdown.md'
    a.click()
    URL.revokeObjectURL(url)
  }, [])

  const downloadCodeWithLineNumbers = useCallback((code: string) => {
    const blob = new Blob([code], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'code-numbered.txt'
    a.click()
    URL.revokeObjectURL(url)
  }, [])

  return {
    downloadZip,
    downloadReport,
    copyReport,
    downloadSpecMarkdown,
    downloadCodeWithLineNumbers,
  }
}
