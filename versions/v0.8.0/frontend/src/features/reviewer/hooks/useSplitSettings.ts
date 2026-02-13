import { useState, useCallback } from 'react'
import type {
  SplitSettings,
  SplitPreviewResult,
  DocumentPart,
  CodePart,
} from '../types'
import * as api from '../services/api'

interface UseSplitSettingsReturn {
  // State
  settings: SplitSettings
  previewResult: SplitPreviewResult | null
  isExecutingPreview: boolean
  error: string | null

  // Actions
  setSettings: (settings: SplitSettings) => void
  executePreview: (
    designMarkdown: string | null,
    designFilename: string,
    codeFiles: Array<{ filename: string; content: string }>
  ) => Promise<void>
  clearPreview: () => void
  clearError: () => void

  // Computed
  isSplitEnabled: boolean
  reviewMode: 'batch' | 'split'
  estimatedReviewCount: number
}

const DEFAULT_SETTINGS: SplitSettings = {
  reviewMode: 'batch',
  documentMaxDepth: 2,
}

export function useSplitSettings(): UseSplitSettingsReturn {
  const [settings, setSettings] = useState<SplitSettings>(DEFAULT_SETTINGS)
  const [previewResult, setPreviewResult] = useState<SplitPreviewResult | null>(null)
  const [isExecutingPreview, setIsExecutingPreview] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const executePreview = useCallback(async (
    designMarkdown: string | null,
    designFilename: string,
    codeFiles: Array<{ filename: string; content: string }>
  ) => {
    setIsExecutingPreview(true)
    setError(null)

    try {
      if (settings.reviewMode === 'split') {
        if (!designMarkdown) {
          throw new Error('分割レビューには設計書が必要です')
        }
        if (codeFiles.length === 0) {
          throw new Error('分割レビューにはプログラムが必要です')
        }
      }

      let documentParts: DocumentPart[] | null = null
      let documentIndex: string | null = null
      let codeParts: CodePart[] | null = null
      let codeIndex: string | null = null
      let codeLanguage: string | null = null

      // 設計書分割
      if (settings.reviewMode === 'split' && designMarkdown) {
        const response = await api.splitMarkdown({
          content: designMarkdown,
          filename: designFilename,
          maxDepth: settings.documentMaxDepth,
        })

        if (response.success) {
          documentParts = response.parts
          documentIndex = response.indexContent || null
        } else {
          throw new Error(response.error || '設計書の分割に失敗しました')
        }
      }

      // コード分割（対応言語のファイルのみ）
      if (settings.reviewMode === 'split' && codeFiles.length > 0) {
        const allCodeParts: CodePart[] = []
        const allIndexContents: string[] = []
        const unsupportedFiles: string[] = []

        for (const codeFile of codeFiles) {
          const ext = codeFile.filename.toLowerCase().split('.').pop()
          if (ext !== 'py' && ext !== 'java') {
            unsupportedFiles.push(codeFile.filename)
            continue // 未対応言語はスキップ
          }

          const response = await api.splitCode({
            content: codeFile.content,
            filename: codeFile.filename,
          })

          if (response.success) {
            allCodeParts.push(...response.parts)
            if (response.indexContent) {
              allIndexContents.push(response.indexContent)
            }
            if (response.language && !codeLanguage) {
              codeLanguage = response.language
            }
          } else {
            console.warn(`Failed to split ${codeFile.filename}: ${response.error}`)
          }
        }

        if (unsupportedFiles.length > 0) {
          throw new Error(
            `未対応言語が含まれるため分割できません: ${unsupportedFiles.join(', ')}`
          )
        }

        if (allCodeParts.length > 0) {
          codeParts = allCodeParts
          codeIndex = allIndexContents.join('\n\n---\n\n')
        }
      }

      setPreviewResult({
        documentParts,
        codeParts,
        documentIndex,
        codeIndex,
        codeLanguage,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : '分割プレビューに失敗しました'
      setError(message)
      setPreviewResult(null)
    } finally {
      setIsExecutingPreview(false)
    }
  }, [settings.reviewMode, settings.documentMaxDepth])

  const clearPreview = useCallback(() => {
    setPreviewResult(null)
    setError(null)
  }, [])

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  const handleSetSettings = useCallback((newSettings: SplitSettings) => {
    setSettings(newSettings)
    // 設定が変更されたらプレビュー結果をクリア
    setPreviewResult(null)
    setError(null)
  }, [])

  // Computed values
  const isSplitEnabled = settings.reviewMode === 'split'

  const reviewMode = settings.reviewMode

  // レビュー回数の推定
  const estimatedReviewCount = (() => {
    if (!previewResult) return 1

    const docCount = previewResult.documentParts?.length || 0
    const codeCount = previewResult.codeParts?.length || 0

    switch (reviewMode) {
      case 'split':
        // フェーズ1: 構造マッチング 1回
        // フェーズ2: ペアレビュー（最大 docCount + codeCount、実際は関連ペアのみ）
        return 1 + docCount + codeCount
      default:
        return 1
    }
  })()

  return {
    settings,
    previewResult,
    isExecutingPreview,
    error,
    setSettings: handleSetSettings,
    executePreview,
    clearPreview,
    clearError,
    isSplitEnabled,
    reviewMode,
    estimatedReviewCount,
  }
}
