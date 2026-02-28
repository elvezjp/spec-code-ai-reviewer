import { useState } from 'react'
import { CheckCircle, Loader2, Circle, AlertCircle, SkipForward, RotateCcw, ChevronDown, ChevronRight, Ban } from 'lucide-react'
import { Card, Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '@core/index'
import type { SplitReviewState } from '../types'

interface SplitExecutingScreenProps {
  state: SplitReviewState
  onBack: () => void
  onRetryStructureMatching: () => void
  onRetryGroup: (groupId: string) => void
  onSkipGroup: (groupId: string) => void
  onRetryIntegrate: () => void
}

type StepStatus = 'completed' | 'in_progress' | 'pending' | 'error' | 'skipped'

function StatusIcon({ status }: { status: StepStatus }) {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-5 h-5 text-green-600" />
    case 'in_progress':
      return <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
    case 'error':
      return <AlertCircle className="w-5 h-5 text-red-600" />
    case 'skipped':
      return <Ban className="w-5 h-5 text-gray-400" />
    default:
      return <Circle className="w-5 h-5 text-gray-400" />
  }
}

function StatusText({ status }: { status: StepStatus }) {
  const config: Record<StepStatus, { text: string; className: string }> = {
    completed: { text: '完了', className: 'text-green-600' },
    in_progress: { text: '実行中', className: 'text-blue-600' },
    pending: { text: '待機中', className: 'text-gray-500' },
    error: { text: 'エラー', className: 'text-red-600' },
    skipped: { text: 'スキップ', className: 'text-gray-400' },
  }
  const { text, className } = config[status]
  return <span className={className}>{text}</span>
}

function getPhaseStatus(
  phase: SplitReviewState['phase'],
  targetPhase: 'structure-matching' | 'group-review' | 'integrate'
): StepStatus {
  if (phase === 'error') return 'error'
  if (phase === 'completed') return 'completed'
  if (phase === 'paused') {
    // 一時停止はグループレビュー中にのみ発生する
    if (targetPhase === 'structure-matching') return 'completed'
    return 'pending'
  }

  const phaseOrder = ['idle', 'structure-matching', 'group-review', 'integrate', 'completed']
  const currentIndex = phaseOrder.indexOf(phase)
  const targetIndex = phaseOrder.indexOf(targetPhase)

  if (currentIndex > targetIndex) return 'completed'
  if (currentIndex === targetIndex) return 'in_progress'
  return 'pending'
}

function StepCard({
  stepLabel,
  title,
  status,
  children,
}: {
  stepLabel: string
  title: string
  status: StepStatus
  children?: React.ReactNode
}) {
  const [isOpen, setIsOpen] = useState(false)
  const canExpand = status !== 'pending' && !!children

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div
        className={`flex items-center justify-between ${canExpand ? 'cursor-pointer' : ''}`}
        onClick={() => canExpand && setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-3">
          <span className="text-sm font-mono text-gray-500 w-8">{stepLabel}</span>
          <span className="font-medium text-gray-800">{title}</span>
        </div>
        <div className="flex items-center gap-2">
          <StatusIcon status={status} />
          <StatusText status={status} />
          {canExpand && (
            isOpen
              ? <ChevronDown className="w-4 h-4 text-gray-400" />
              : <ChevronRight className="w-4 h-4 text-gray-400" />
          )}
        </div>
      </div>
      {isOpen && (
        <div className="mt-3 pt-3 border-t ml-11">
          {children}
        </div>
      )}
    </div>
  )
}

export function SplitExecutingScreen({
  state,
  onBack,
  onRetryStructureMatching,
  onRetryGroup,
  onSkipGroup,
  onRetryIntegrate,
}: SplitExecutingScreenProps) {
  const isPaused = state.phase === 'paused'
  const isError = state.phase === 'error'
  const hasErrorGroup = state.groupReviews.some((g) => g.status === 'error')
  const isErrorPaused = isPaused && hasErrorGroup

  // エラーがどのフェーズで発生したかを判定
  const isStructureMatchingError = isError && !state.structureMatchingResult
  const allGroupsProcessed = state.groupReviews.length > 0 &&
    state.groupReviews.every((g) => g.status === 'completed' || g.status === 'skipped')
  const isIntegrateError = isError && state.structureMatchingResult && allGroupsProcessed && !state.integrateResult

  const structureMatchingStatus = isStructureMatchingError ? 'error' : getPhaseStatus(state.phase, 'structure-matching')
  const groupReviewStatus = getPhaseStatus(state.phase, 'group-review')
  const integrateStatus = isIntegrateError ? 'error' : getPhaseStatus(state.phase, 'integrate')

  const groups = state.structureMatchingResult?.groups || []
  const completedGroups = state.groupReviews.filter((g) => g.status === 'completed' || g.status === 'skipped').length

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <Card>
        <div className="flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-800">分割レビュー実行中</h1>
          <button onClick={onBack} className="text-blue-500 hover:text-blue-700">
            ← 戻る
          </button>
        </div>
      </Card>

      {/* Progress Overview */}
      <Card>
        <div className="text-center">
          <div className="flex items-center justify-center gap-8 mb-4">
            <div className="flex items-center gap-2">
              <StatusIcon status={structureMatchingStatus} />
              <span className="text-sm text-gray-700">1. 構造マッチング</span>
            </div>
            <div className="flex items-center gap-2">
              <StatusIcon status={groupReviewStatus} />
              <span className="text-sm text-gray-700">
                2. グループレビュー
                {groups.length > 0 && ` (${completedGroups}/${groups.length})`}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <StatusIcon status={integrateStatus} />
              <span className="text-sm text-gray-700">3. 結果統合</span>
            </div>
          </div>

          {isStructureMatchingError && (
            <>
              <p className="text-sm text-red-600 mt-2">
                構造マッチングでエラーが発生しました。
              </p>
              <div className="flex items-center justify-center gap-3 mt-3">
                <button
                  onClick={onRetryStructureMatching}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded-md transition"
                >
                  <RotateCcw className="w-4 h-4" />
                  リトライ
                </button>
              </div>
            </>
          )}

          {isErrorPaused && (
            <>
              <p className="text-sm text-red-600 mt-2">
                グループレビューでエラーが発生しました。リトライまたはスキップを選択してください。
              </p>
              <div className="flex items-center justify-center gap-3 mt-3">
                <button
                  onClick={() => {
                    const errorGroup = state.groupReviews.find((g) => g.status === 'error')
                    if (errorGroup) onRetryGroup(errorGroup.groupId)
                  }}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded-md transition"
                >
                  <RotateCcw className="w-4 h-4" />
                  リトライ
                </button>
                <button
                  onClick={() => {
                    const errorGroup = state.groupReviews.find((g) => g.status === 'error')
                    if (errorGroup) onSkipGroup(errorGroup.groupId)
                  }}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-gray-400 hover:bg-gray-500 text-white text-sm rounded-md transition"
                >
                  <SkipForward className="w-4 h-4" />
                  スキップ
                </button>
              </div>
            </>
          )}

          {isIntegrateError && (
            <>
              <p className="text-sm text-red-600 mt-2">
                結果統合でエラーが発生しました。
              </p>
              <div className="flex items-center justify-center gap-3 mt-3">
                <button
                  onClick={onRetryIntegrate}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded-md transition"
                >
                  <RotateCcw className="w-4 h-4" />
                  リトライ
                </button>
              </div>
            </>
          )}
        </div>
      </Card>

      {/* Steps */}
      <Card>
        <h2 className="text-lg font-semibold text-gray-800 mb-4">実行ステップ</h2>
        <div className="space-y-4">
          <StepCard stepLabel="1" title="構造マッチング" status={structureMatchingStatus}>
            {structureMatchingStatus === 'in_progress' && (
              <div className="flex items-center gap-2 text-blue-600 text-sm">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>構造を分析中...</span>
              </div>
            )}
            {structureMatchingStatus === 'completed' && state.structureMatchingResult && (
              <div className="text-sm text-gray-700 space-y-2">
                <div>マッチング結果: {state.structureMatchingResult.totalGroups} グループ</div>
                <div className="overflow-x-auto">
                  <Table className="min-w-full text-sm">
                    <TableHead>
                      <TableRow>
                        <TableHeaderCell>グループ名</TableHeaderCell>
                        <TableHeaderCell>設計書セクション</TableHeaderCell>
                        <TableHeaderCell>プログラムシンボル</TableHeaderCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {state.structureMatchingResult.groups.map((group) => (
                        <TableRow key={group.groupId}>
                          <TableCell>{group.groupName}</TableCell>
                          <TableCell>
                            {group.docSections.length > 0
                              ? group.docSections.map((s) => s.title).join(', ')
                              : '（分割なし）'}
                          </TableCell>
                          <TableCell>
                            {group.codeSymbols.length > 0
                              ? group.codeSymbols.map((s) => s.symbol).join(', ')
                              : '（分割なし）'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            )}
            {structureMatchingStatus === 'error' && state.error && (
              <div className="text-sm text-red-600">
                <span className="text-gray-500">エラー: </span>
                {state.error}
              </div>
            )}
          </StepCard>

          {/* Steps 2.x: Group Reviews */}
          {groups.map((group, index) => {
            const reviewState = state.groupReviews.find((g) => g.groupId === group.groupId)
            const status = reviewState?.status || 'pending'
            const result = reviewState?.result

            return (
              <StepCard
                key={group.groupId}
                stepLabel={`2.${index + 1}`}
                title={group.groupName}
                status={status}
              >
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-gray-500">設計書: </span>
                    <span className="text-gray-700">
                      {group.docSections.length > 0
                        ? group.docSections.map((s) => s.title).join('、')
                        : '（分割なし）'}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">プログラム: </span>
                    <span className="text-gray-700">
                      {group.codeSymbols.length > 0
                        ? group.codeSymbols.map((s) => s.symbol).join('、')
                        : '（分割なし）'}
                    </span>
                  </div>

                  {status === 'in_progress' && (
                    <div className="flex items-center gap-2 text-blue-600 mt-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>レビュー実行中...</span>
                    </div>
                  )}

                  {status === 'completed' && result && (
                    <div className="mt-2 pt-2 border-t">
                      <div className="text-gray-700 text-xs whitespace-pre-wrap max-h-40 overflow-y-auto">
                        {result.report}
                      </div>
                    </div>
                  )}

                  {status === 'skipped' && (
                    <div className="mt-2 pt-2 border-t text-gray-500">
                      このグループはスキップされました
                    </div>
                  )}

                  {status === 'error' && reviewState?.error && (
                    <div className="mt-2 pt-2 border-t">
                      <div className="text-red-600">
                        <span className="text-gray-500">エラー: </span>
                        {reviewState.error}
                      </div>
                    </div>
                  )}
                </div>
              </StepCard>
            )
          })}

          {/* Step 3: Integration */}
          <StepCard stepLabel="3" title="結果統合" status={integrateStatus}>
            {integrateStatus === 'in_progress' && (
              <div className="flex items-center gap-2 text-blue-600 text-sm">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>結果を統合中...</span>
              </div>
            )}
            {integrateStatus === 'error' && state.error && (
              <div className="text-sm text-red-600">
                <span className="text-gray-500">エラー: </span>
                {state.error}
              </div>
            )}
          </StepCard>
        </div>
      </Card>
    </div>
  )
}
