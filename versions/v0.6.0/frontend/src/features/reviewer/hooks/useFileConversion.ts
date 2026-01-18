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
    const newFiles: DesignFile[] = files.map((file, index) => ({
      file,
      filename: file.name,
      isMain: specFiles.length === 0 && index === 0,
      type: DEFAULT_TYPE,
      tool: DEFAULT_TOOL,
    }))

    setSpecFiles((prev) => {
      const existingNames = new Set(prev.map((f) => f.filename))
      const unique = newFiles.filter((f) => !existingNames.has(f.filename))
      return [...prev, ...unique]
    })
    setSpecMarkdown(null)
    setSpecStatus('')
  }, [specFiles.length])

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
        f.filename === filename ? { ...f, tool } : f
      )
    )
    setSpecMarkdown(null)
    setSpecStatus('⚠️ ツールが変更されました。再変換してください。')
  }, [])

  const applyToolToAll = useCallback((tool: string) => {
    setSpecFiles((prev) => prev.map((f) => ({ ...f, tool })))
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
          const result = await api.convertExcelToMarkdown(specFile.file, specFile.tool)

          if (!result.success) {
            throw new Error(`[${specFile.filename}] ${result.error || '変換に失敗しました'}`)
          }

          results.push({
            ...specFile,
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

  const addCodeFiles = useCallback((files: File[]) => {
    const newFiles: CodeFile[] = files.map((file) => ({
      file,
      filename: file.name,
    }))

    setCodeFiles((prev) => {
      const existingNames = new Set(prev.map((f) => f.filename))
      const unique = newFiles.filter((f) => !existingNames.has(f.filename))
      return [...prev, ...unique]
    })
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
