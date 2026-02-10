import { useState, useCallback } from 'react'
import type {
  DesignFile,
  CodeFile,
  ReviewExecutionData,
  SystemPromptValues,
  LlmConfig,
  SimpleJudgment,
  MappingResult,
  MappingSummary,
  StructureMapInfo,
} from '../types'
import type { ReviewMode } from '@core/types'
import * as api from '../services/api'

interface UseReviewExecutionReturn {
  reviewResults: (ReviewExecutionData | null)[]
  isReviewing: boolean
  currentExecutionNumber: number
  currentTab: number
  reviewError: string | null
  executeReview: (params: {
    specFiles: DesignFile[]
    codeFiles: CodeFile[]
    specMarkdown: string
    codeWithLineNumbers: string
    systemPrompt: SystemPromptValues
    llmConfig?: LlmConfig
    mode?: ReviewMode
    useStructureMap?: boolean
    structureMap?: StructureMapInfo | null
  }) => Promise<void>
  setCurrentTab: (tab: number) => void
  clearResults: () => void
  getSimpleJudgment: (reportText: string) => SimpleJudgment
  parseMappingResult: (rawOutput: string) => MappingResult | null
  calculateMappingSummary: (result: MappingResult) => MappingSummary
}

const REVIEW_EXECUTION_COUNT = 2

export function useReviewExecution(): UseReviewExecutionReturn {
  const [reviewResults, setReviewResults] = useState<(ReviewExecutionData | null)[]>([null, null])
  const [isReviewing, setIsReviewing] = useState(false)
  const [currentExecutionNumber, setCurrentExecutionNumber] = useState(0)
  const [currentTab, setCurrentTab] = useState(1)
  const [reviewError, setReviewError] = useState<string | null>(null)

  const getSimpleJudgment = useCallback((reportText: string): SimpleJudgment => {
    if (!reportText) {
      return { status: 'unknown', ngCount: 0, warningCount: 0, okCount: 0 }
    }

    const text = reportText

    // NG keywords detection
    const ngMatches = text.match(/\bNG\b/gi) || []
    const ngEmojiMatches = text.match(/❌/g) || []
    const ngCount = ngMatches.length + ngEmojiMatches.length

    // Warning keywords detection
    const warningMatches = text.match(/要確認/g) || []
    const warningEmojiMatches = text.match(/⚠️/g) || []
    const warningCount = warningMatches.length + warningEmojiMatches.length

    // OK keywords detection
    const okMatches = text.match(/\bOK\b/gi) || []
    const okEmojiMatches = text.match(/✅/g) || []
    const okCount = okMatches.length + okEmojiMatches.length

    // Determine status
    let status: SimpleJudgment['status']
    if (ngCount > 0) {
      status = 'ng'
    } else if (warningCount > 0) {
      status = 'warning'
    } else {
      status = 'ok'
    }

    return { status, ngCount, warningCount, okCount }
  }, [])

  // マッピング結果JSONパーサー
  const parseMappingResult = useCallback((rawOutput: string): MappingResult | null => {
    if (!rawOutput) return null

    try {
      // ```json ... ``` ブロックからJSONを抽出
      const jsonBlockMatch = rawOutput.match(/```json\s*([\s\S]*?)```/)
      const jsonStr = jsonBlockMatch ? jsonBlockMatch[1].trim() : rawOutput.trim()
      const parsed = JSON.parse(jsonStr)

      // 最低限の構造バリデーション
      if (!parsed.files || !Array.isArray(parsed.files)) return null

      return parsed as MappingResult
    } catch {
      return null
    }
  }, [])

  // マッピングサマリー集計（フロントエンド計算）
  const calculateMappingSummary = useCallback((result: MappingResult): MappingSummary => {
    let designItemCount = 0
    let unmappedCount = 0

    for (const file of result.files) {
      for (const item of file.items) {
        designItemCount++
        if (item.confidence === '-') {
          unmappedCount++
        }
      }
    }

    const mappedCount = designItemCount - unmappedCount
    const coveragePercent = designItemCount > 0 ? Math.round((mappedCount / designItemCount) * 100) : 0

    return { designItemCount, mappedCount, unmappedCount, coveragePercent }
  }, [])

  const executeReview = useCallback(
    async (params: {
      specFiles: DesignFile[]
      codeFiles: CodeFile[]
      specMarkdown: string
      codeWithLineNumbers: string
      systemPrompt: SystemPromptValues
      llmConfig?: LlmConfig
      mode?: ReviewMode
      useStructureMap?: boolean
      structureMap?: StructureMapInfo | null
    }) => {
      const {
        specFiles,
        codeFiles,
        specMarkdown,
        codeWithLineNumbers,
        systemPrompt,
        llmConfig,
        mode = 'review',
        useStructureMap = false,
        structureMap = null,
      } = params

      setIsReviewing(true)
      setReviewError(null)
      setReviewResults([null, null])
      setCurrentExecutionNumber(1)

      const specFilename = specFiles.map((f) => f.filename).join(', ')
      const codeFilename = codeFiles.map((f) => f.filename).join(', ')

      try {
        const results: (ReviewExecutionData | null)[] = [null, null]

        for (let i = 1; i <= REVIEW_EXECUTION_COUNT; i++) {
          setCurrentExecutionNumber(i)

          const executedAt = new Date().toLocaleString('ja-JP', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
          })

          const designs = specFiles
            .filter((f) => f.markdown)
            .map((f) => ({
              filename: f.filename,
              content: f.markdown!,
              role: f.isMain ? 'メイン' : '参照',
              isMain: f.isMain,
              type: f.type,
              tool: f.tool,
              note: f.note || '',
            }))

          const codes = codeFiles
            .filter((f) => f.contentWithLineNumbers)
            .map((f) => ({
              filename: f.filename,
              contentWithLineNumbers: f.contentWithLineNumbers!,
            }))

          const result = await api.executeReview({
            specMarkdown,
            specFilename,
            codeWithLineNumbers,
            codeFilename,
            designs,
            codes,
            systemPrompt,
            executedAt,
            executionNumber: i,
            llmConfig,
            mode,
            useStructureMap,
            structureMap: useStructureMap ? structureMap : undefined,
          })

          if (!result.success) {
            throw new Error(result.error || `レビュー実行に失敗しました（${i}回目）`)
          }

          results[i - 1] = {
            systemPrompt,
            specMarkdown,
            codeWithLineNumbers,
            report: result.report!,
            rawOutput: result.rawOutput,
            reviewMeta: result.reviewMeta!,
          }

          // Update results immediately so UI can show progress
          setReviewResults([...results])
        }

        setCurrentTab(1)
      } catch (error) {
        setReviewError(error instanceof Error ? error.message : 'レビュー実行に失敗しました')
        throw error
      } finally {
        setIsReviewing(false)
        setCurrentExecutionNumber(0)
      }
    },
    []
  )

  const clearResults = useCallback(() => {
    setReviewResults([null, null])
    setCurrentTab(1)
    setReviewError(null)
  }, [])

  return {
    reviewResults,
    isReviewing,
    currentExecutionNumber,
    currentTab,
    reviewError,
    executeReview,
    setCurrentTab,
    clearResults,
    getSimpleJudgment,
    parseMappingResult,
    calculateMappingSummary,
  }
}
