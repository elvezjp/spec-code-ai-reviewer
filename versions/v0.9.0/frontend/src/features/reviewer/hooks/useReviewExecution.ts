import { useState, useCallback } from 'react'
import type {
  DesignFile,
  CodeFile,
  ReviewExecutionData,
  SystemPromptValues,
  LlmConfig,
  SimpleJudgment,
  SimpleMappingJudgment,
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
  getSimpleMappingJudgment: (reportText: string) => SimpleMappingJudgment
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

  // マッピング用簡易判定ロジック
  const getSimpleMappingJudgment = useCallback((reportText: string): SimpleMappingJudgment => {
    if (!reportText) {
      return {
        status: 'ng',
        designItemCount: 0,
        mappedCount: 0,
        unmappedCount: 0,
        coveragePercent: 0,
      }
    }

    // 1. サマリーから数値を取得
    const parseSummaryInt = (pattern: RegExp): number | null => {
      const m = reportText.match(pattern)
      return m ? parseInt(m[1], 10) : null
    }

    let designItemCount = parseSummaryInt(/設計書項目数:\s*(\d+)/)
    let mappedCount = parseSummaryInt(/マッピング済み:\s*(\d+)/)
    let unmappedCount = parseSummaryInt(/未マッピング:\s*(\d+)/)
    let coveragePercent = parseSummaryInt(/カバレッジ:\s*(\d+)/)

    // 2. サマリーから取得できない場合、テーブル行数からカウント
    if (designItemCount === null) {
      // マッピング一覧テーブル（6カラム）のデータ行をカウント
      const tableRowPattern = /^\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|$/gm
      const tableRows = reportText.match(tableRowPattern) || []
      // ヘッダー行と区切り行を除外
      mappedCount = Math.max(0, tableRows.length - 2)

      // 未マッピング項目テーブル（3カラム）のデータ行をカウント
      const unmappedTablePattern = /未マッピング[\s\S]*?((?:^\|[^|]+\|[^|]+\|[^|]+\|$\n?)+)/m
      const unmappedTableMatch = reportText.match(unmappedTablePattern)
      if (unmappedTableMatch) {
        const unmappedRows = unmappedTableMatch[1].match(/^\|[^|]+\|[^|]+\|[^|]+\|$/gm) || []
        // ヘッダー行と区切り行を除外
        unmappedCount = Math.max(0, unmappedRows.length - 2)
      } else {
        unmappedCount = 0
      }

      designItemCount = mappedCount + unmappedCount
    } else {
      // サマリーから項目数は取得できたが、内訳が欠けている場合の補完
      if (mappedCount === null && unmappedCount !== null) {
        mappedCount = designItemCount - unmappedCount
      } else if (unmappedCount === null && mappedCount !== null) {
        unmappedCount = designItemCount - mappedCount
      }
      mappedCount = mappedCount ?? 0
      unmappedCount = unmappedCount ?? 0
    }

    // 3. カバレッジが取得できていなければ計算
    if (coveragePercent === null) {
      coveragePercent = designItemCount > 0 ? Math.round((mappedCount / designItemCount) * 100) : 0
    }

    // ステータス判定
    let status: SimpleMappingJudgment['status']
    if (designItemCount === 0 || coveragePercent === 0) {
      status = 'ng'
    } else if (coveragePercent === 100) {
      status = 'ok'
    } else {
      status = 'warning'
    }

    return {
      status,
      designItemCount,
      mappedCount,
      unmappedCount,
      coveragePercent,
    }
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
    getSimpleMappingJudgment,
  }
}
