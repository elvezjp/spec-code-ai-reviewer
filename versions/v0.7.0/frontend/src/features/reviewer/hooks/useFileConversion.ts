import { useState, useCallback } from 'react'
import type { DesignFile, CodeFile, ConversionTool } from '../types'
import * as api from '../services/api'

interface UseFileConversionReturn {
  // Design files
  specFiles: DesignFile[]
  specMarkdown: string | null
  isSpecConverting: boolean
  specStatus: string
  addSpecFiles: (files: File[]) => void
  removeSpecFile: (filename: string) => void
  setMainSpec: (filename: string) => void
  setSpecType: (filename: string, type: string) => void
  setSpecTool: (filename: string, tool: string) => void
  applyToolToAll: (tool: string) => void
  convertSpecs: (getTypeNote: (type: string) => string) => Promise<void>
  clearSpecs: () => void
  applyOrganizedMarkdown: (
    organizedFiles: Map<string, string>,
    getTypeNote: (type: string) => string
  ) => void

  // Code files
  codeFiles: CodeFile[]
  codeWithLineNumbers: string | null
  isCodeConverting: boolean
  codeStatus: string
  addCodeFiles: (files: File[]) => void
  removeCodeFile: (filename: string) => void
  convertCodes: () => Promise<void>
  clearCodes: () => void

  // Available tools
  availableTools: ConversionTool[]
  loadTools: () => Promise<void>
}

const DEFAULT_TOOL = 'markitdown'
const DEFAULT_TYPE = '設計書'
const DOCX_TOOL = 'markitdown'

const isDocxFilename = (filename: string): boolean => filename.toLowerCase().endsWith('.docx')
const isDocFilename = (filename: string): boolean =>
  filename.toLowerCase().endsWith('.doc') && !isDocxFilename(filename)

export function useFileConversion(): UseFileConversionReturn {
  const [specFiles, setSpecFiles] = useState<DesignFile[]>([])
  const [specMarkdown, setSpecMarkdown] = useState<string | null>(null)
  const [isSpecConverting, setIsSpecConverting] = useState(false)
  const [specStatus, setSpecStatus] = useState('')

  const [codeFiles, setCodeFiles] = useState<CodeFile[]>([])
  const [codeWithLineNumbers, setCodeWithLineNumbers] = useState<string | null>(null)
  const [isCodeConverting, setIsCodeConverting] = useState(false)
  const [codeStatus, setCodeStatus] = useState('')

  const [availableTools, setAvailableTools] = useState<ConversionTool[]>([
    { name: 'markitdown', display_name: 'MarkItDown' },
    { name: 'excel2md', display_name: 'excel2md' },
  ])

  const loadTools = useCallback(async () => {
    const tools = await api.fetchAvailableTools()
    setAvailableTools(tools)
  }, [])

  const addSpecFiles = useCallback((files: File[]) => {
    const filtered = files.filter((file) => !isDocFilename(file.name))
    const excludedCount = files.length - filtered.length

    const newFiles: DesignFile[] = filtered.map((file, index) => ({
      file,
      filename: file.name,
      isMain: index === 0,
      type: DEFAULT_TYPE,
      tool: isDocxFilename(file.name) ? DOCX_TOOL : DEFAULT_TOOL,
    }))

    setSpecFiles(newFiles)
    setSpecMarkdown(null)
    if (excludedCount > 0) {
      const suffix = excludedCount > 0 ? `（${excludedCount}件を除外）` : ''
      setSpecStatus(`❌ .doc形式は非対応です。.docx形式で保存し直してください${suffix}`)
    } else {
      setSpecStatus('')
    }
  }, [])

  const removeSpecFile = useCallback((filename: string) => {
    setSpecFiles((prev) => {
      const filtered = prev.filter((f) => f.filename !== filename)
      // If main file was removed, set first file as main
      if (filtered.length > 0 && !filtered.some((f) => f.isMain)) {
        filtered[0].isMain = true
      }
      return filtered
    })
    setSpecMarkdown(null)
    setSpecStatus('')
  }, [])

  const setMainSpec = useCallback((filename: string) => {
    setSpecFiles((prev) =>
      prev.map((f) => ({
        ...f,
        isMain: f.filename === filename,
      }))
    )
    setSpecMarkdown(null)
    setSpecStatus('⚠️ メイン設計書が変更されました。再変換してください。')
  }, [])

  const setSpecType = useCallback((filename: string, type: string) => {
    setSpecFiles((prev) =>
      prev.map((f) =>
        f.filename === filename ? { ...f, type } : f
      )
    )
    setSpecMarkdown(null)
    setSpecStatus('⚠️ 種別が変更されました。再変換してください。')
  }, [])

  const setSpecTool = useCallback((filename: string, tool: string) => {
    setSpecFiles((prev) =>
      prev.map((f) =>
        f.filename === filename
          ? { ...f, tool: isDocxFilename(f.filename) ? DOCX_TOOL : tool }
          : f
      )
    )
    setSpecMarkdown(null)
    setSpecStatus('⚠️ ツールが変更されました。再変換してください。')
  }, [])

  const applyToolToAll = useCallback((tool: string) => {
    setSpecFiles((prev) =>
      prev.map((f) => ({
        ...f,
        tool: isDocxFilename(f.filename) ? DOCX_TOOL : tool,
      }))
    )
    setSpecMarkdown(null)
    setSpecStatus('⚠️ ツールが変更されました。再変換してください。')
  }, [])

  const convertSpecs = useCallback(
    async (getTypeNote: (type: string) => string) => {
      if (specFiles.length === 0) return

      setIsSpecConverting(true)
      setSpecStatus('変換中...')

      try {
        const results: DesignFile[] = []

        for (const specFile of specFiles) {
          const normalizedTool = isDocxFilename(specFile.filename) ? DOCX_TOOL : specFile.tool
          const result = await api.convertExcelToMarkdown(specFile.file, normalizedTool)

          if (!result.success) {
            throw new Error(`[${specFile.filename}] ${result.error || '変換に失敗しました'}`)
          }

          results.push({
            ...specFile,
            tool: normalizedTool,
            markdown: result.markdown,
            note: getTypeNote(specFile.type),
          })
        }

        setSpecFiles(results)

        // Generate combined markdown
        const markdown = results
          .map((r) => {
            const note = getTypeNote(r.type)
            const role = r.isMain ? 'メイン' : '参照'
            return `# 設計書: ${r.filename}\n- 役割: ${role}\n- 種別: ${r.type}\n- 注意事項: ${note}\n\n${r.markdown}`
          })
          .join('\n\n---\n\n')

        setSpecMarkdown(markdown)
        setSpecStatus('✅ 変換済み')
      } catch (error) {
        setSpecStatus(`❌ ${error instanceof Error ? error.message : '変換に失敗しました'}`)
      } finally {
        setIsSpecConverting(false)
      }
    },
    [specFiles]
  )

  const clearSpecs = useCallback(() => {
    setSpecFiles([])
    setSpecMarkdown(null)
    setSpecStatus('')
  }, [])

  const applyOrganizedMarkdown = useCallback(
    (organizedFiles: Map<string, string>, getTypeNote: (type: string) => string) => {
      // 各ファイルのmarkdownを更新
      setSpecFiles((prev) =>
        prev.map((f) => {
          const organized = organizedFiles.get(f.filename)
          return organized ? { ...f, markdown: organized } : f
        })
      )

      // 結合済みMarkdownを再生成
      setSpecFiles((prev) => {
        const markdown = prev
          .filter((f) => f.markdown)
          .map((f) => {
            const note = getTypeNote(f.type)
            const role = f.isMain ? 'メイン' : '参照'
            return `# 設計書: ${f.filename}\n- 役割: ${role}\n- 種別: ${f.type}\n- 注意事項: ${note}\n\n${f.markdown}`
          })
          .join('\n\n---\n\n')
        setSpecMarkdown(markdown)
        return prev
      })

      setSpecStatus('✅ AI整理済み')
    },
    []
  )

  const addCodeFiles = useCallback((files: File[]) => {
    const newFiles: CodeFile[] = files.map((file) => ({
      file,
      filename: file.name,
    }))

    setCodeFiles(newFiles)
    setCodeWithLineNumbers(null)
    setCodeStatus('')
  }, [])

  const removeCodeFile = useCallback((filename: string) => {
    setCodeFiles((prev) => prev.filter((f) => f.filename !== filename))
    setCodeWithLineNumbers(null)
    setCodeStatus('')
  }, [])

  const convertCodes = useCallback(async () => {
    if (codeFiles.length === 0) return

    setIsCodeConverting(true)
    setCodeStatus('変換中...')

    try {
      const results: CodeFile[] = []

      for (const codeFile of codeFiles) {
        const result = await api.addLineNumbers(codeFile.file)

        if (!result.success) {
          throw new Error(`[${codeFile.filename}] ${result.error || '変換に失敗しました'}`)
        }

        results.push({
          ...codeFile,
          contentWithLineNumbers: result.content,
        })
      }

      setCodeFiles(results)

      // Generate combined code with line numbers
      const combined = results
        .map((r) => `# プログラム: ${r.filename}\n\n${r.contentWithLineNumbers}`)
        .join('\n\n---\n\n')

      setCodeWithLineNumbers(combined)
      setCodeStatus('✅ 変換済み')
    } catch (error) {
      setCodeStatus(`❌ ${error instanceof Error ? error.message : '変換に失敗しました'}`)
    } finally {
      setIsCodeConverting(false)
    }
  }, [codeFiles])

  const clearCodes = useCallback(() => {
    setCodeFiles([])
    setCodeWithLineNumbers(null)
    setCodeStatus('')
  }, [])

  return {
    specFiles,
    specMarkdown,
    isSpecConverting,
    specStatus,
    addSpecFiles,
    removeSpecFile,
    setMainSpec,
    setSpecType,
    setSpecTool,
    applyToolToAll,
    convertSpecs,
    clearSpecs,
    applyOrganizedMarkdown,

    codeFiles,
    codeWithLineNumbers,
    isCodeConverting,
    codeStatus,
    addCodeFiles,
    removeCodeFile,
    convertCodes,
    clearCodes,

    availableTools,
    loadTools,
  }
}
