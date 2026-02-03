import { useState, useCallback, useRef } from 'react'
import type {
  ProgressiveSummaryState,
  ChunkWithStatus,
  LlmConfig,
} from '../types'
import { splitChunks, executeProgressiveSummary } from '../services/api'

const DEFAULT_SPEC_POLICY = `以下のルールで設計書を要約してください。
- 要約や推測は禁止。原文の意味を変えない。
- 機能、入出力、制約、例外、非機能要件の観点で整理する。
- 重複する内容は統合し、矛盾があれば明記する。`

const DEFAULT_CODE_POLICY = `以下のルールでコードを要約してください。
- 推測は禁止。コードにない事項は書かない。
- エントリーポイント、API、DB操作、クラス、関数の観点で整理する。
- 重複する内容は統合し、矛盾があれば明記する。`

const initialState: ProgressiveSummaryState = {
  type: 'spec',
  chunks: [],
  currentIndex: -1,
  currentSummary: '',
  totalTokenCount: 0,
  status: 'idle',
  error: null,
}

export function useProgressiveSummary() {
  const [state, setState] = useState<ProgressiveSummaryState>(initialState)
  const [policy, setPolicy] = useState(DEFAULT_SPEC_POLICY)
  const abortRef = useRef(false)

  // Split chunks from markdown
  const splitMarkdown = useCallback(
    async (type: 'spec' | 'code', markdown: string, filenames: string[]) => {
      setState((prev) => ({ ...prev, type, status: 'splitting', error: null }))

      try {
        const result = await splitChunks({ type, markdown, sourceFilenames: filenames })

        if (!result.success) {
          setState((prev) => ({
            ...prev,
            status: 'error',
            error: result.error || 'チャンク分割に失敗しました',
          }))
          return
        }

        const chunksWithStatus: ChunkWithStatus[] = result.chunks.map((c) => ({
          ...c,
          status: 'pending',
        }))

        setState((prev) => ({
          ...prev,
          chunks: chunksWithStatus,
          totalTokenCount: result.totalTokenCount,
          status: 'ready',
          currentIndex: -1,
          currentSummary: '',
        }))

        // Set default policy based on type
        setPolicy(type === 'spec' ? DEFAULT_SPEC_POLICY : DEFAULT_CODE_POLICY)
      } catch (e) {
        setState((prev) => ({
          ...prev,
          status: 'error',
          error: e instanceof Error ? e.message : 'チャンク分割に失敗しました',
        }))
      }
    },
    []
  )

  // Start summarization
  const startSummarization = useCallback(
    async (llmConfig?: LlmConfig) => {
      if (state.chunks.length === 0) return

      abortRef.current = false

      // Find the first chunk that is not completed
      const startIndex = state.chunks.findIndex((c) => c.status !== 'completed')
      if (startIndex === -1) {
        // All chunks are already completed
        setState((prev) => ({ ...prev, status: 'completed' }))
        return
      }

      setState((prev) => ({ ...prev, status: 'summarizing' }))

      // Build chunk outline
      const chunkOutline = state.chunks
        .map((c, i) => `${i + 1}. ${c.title} (${c.tokenCount} tokens)`)
        .join('\n')

      let currentSummary = state.currentSummary

      for (let i = startIndex; i < state.chunks.length; i++) {
        if (abortRef.current) {
          setState((prev) => ({ ...prev, status: 'stopped' }))
          return
        }

        const chunk = state.chunks[i]

        // Update status to processing
        setState((prev) => ({
          ...prev,
          currentIndex: i,
          chunks: prev.chunks.map((c, idx) =>
            idx === i ? { ...c, status: 'processing' } : c
          ),
        }))

        try {
          const result = await executeProgressiveSummary({
            type: state.type,
            chunk: { id: chunk.id, title: chunk.title, text: chunk.text },
            chunkOutline,
            currentSummary,
            policy,
            llmConfig,
          })

          if (!result.success) {
            setState((prev) => ({
              ...prev,
              status: 'error',
              error: result.error || '要約に失敗しました',
              chunks: prev.chunks.map((c, idx) =>
                idx === i ? { ...c, status: 'error', error: result.error } : c
              ),
            }))
            return
          }

          currentSummary = result.updatedSummary || currentSummary

          // Update chunk status to completed
          setState((prev) => ({
            ...prev,
            currentSummary,
            chunks: prev.chunks.map((c, idx) =>
              idx === i ? { ...c, status: 'completed' } : c
            ),
          }))
        } catch (e) {
          const errorMsg = e instanceof Error ? e.message : '要約に失敗しました'
          setState((prev) => ({
            ...prev,
            status: 'error',
            error: errorMsg,
            chunks: prev.chunks.map((c, idx) =>
              idx === i ? { ...c, status: 'error', error: errorMsg } : c
            ),
          }))
          return
        }
      }

      setState((prev) => ({ ...prev, status: 'completed' }))
    },
    [state.chunks, state.currentSummary, state.type, policy]
  )

  // Stop summarization
  const stopSummarization = useCallback(() => {
    abortRef.current = true
  }, [])

  // Reset state
  const reset = useCallback(() => {
    abortRef.current = true
    setState(initialState)
    setPolicy(DEFAULT_SPEC_POLICY)
  }, [])

  return {
    state,
    policy,
    setPolicy,
    splitMarkdown,
    startSummarization,
    stopSummarization,
    reset,
    defaultSpecPolicy: DEFAULT_SPEC_POLICY,
    defaultCodePolicy: DEFAULT_CODE_POLICY,
  }
}
