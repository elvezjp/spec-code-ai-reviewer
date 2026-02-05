import { CheckCircle, Loader2, Circle, Pause, Play, AlertCircle } from 'lucide-react'
import type {
  SplitReviewState,
  GroupReviewState,
  MatchedGroup,
  ReviewFinding,
} from '../types'

interface SplitExecutingScreenProps {
  state: SplitReviewState
  onBack: () => void
  onPause: () => void
  onResume: () => void
}

function StatusIcon({ status }: { status: 'completed' | 'in_progress' | 'pending' | 'error' }) {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-5 h-5 text-green-600" />
    case 'in_progress':
      return <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
    case 'error':
      return <AlertCircle className="w-5 h-5 text-red-600" />
    default:
      return <Circle className="w-5 h-5 text-gray-400" />
  }
}

function StatusText({ status }: { status: 'completed' | 'in_progress' | 'pending' | 'error' }) {
  const config = {
    completed: { text: '完了', className: 'text-green-600' },
    in_progress: { text: '実行中', className: 'text-blue-600' },
    pending: { text: '待機中', className: 'text-gray-500' },
    error: { text: 'エラー', className: 'text-red-600' },
  }
  const { text, className } = config[status]
  return <span className={className}>{text}</span>
}

function getPhaseStatus(
  phase: SplitReviewState['phase'],
  targetPhase: 'structure-matching' | 'group-review' | 'integrate'
): 'completed' | 'in_progress' | 'pending' | 'error' {
  const phaseOrder = ['idle', 'structure-matching', 'group-review', 'integrate', 'completed', 'paused', 'error']
  const currentIndex = phaseOrder.indexOf(phase)
  const targetIndex = phaseOrder.indexOf(targetPhase)

  if (phase === 'error') return 'error'
  if (phase === 'paused') {
    return 'pending'
  }
  if (phase === 'completed') return 'completed'
  if (currentIndex > targetIndex) return 'completed'
  if (currentIndex === targetIndex) return 'in_progress'
  return 'pending'
}

function SeverityBadge({ severity }: { severity: string }) {
  const config = {
    error: { text: 'エラー', className: 'bg-red-100 text-red-700' },
    warning: { text: '警告', className: 'bg-yellow-100 text-yellow-700' },
    info: { text: '情報', className: 'bg-blue-100 text-blue-700' },
  }
  const { text, className } = config[severity as keyof typeof config] || config.info
  return <span className={`px-2 py-0.5 text-xs rounded ${className}`}>{text}</span>
}

function GroupCard({ group, reviewState }: { group: MatchedGroup; reviewState?: GroupReviewState }) {
  const status = reviewState?.status || 'pending'
  const result = reviewState?.result

  return (
    <div className="border rounded-md overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b">
        <span className="font-medium text-gray-800">{group.groupName}</span>
        <div className="flex items-center gap-2">
          <StatusIcon status={status} />
          <StatusText status={status} />
        </div>
      </div>

      {status !== 'pending' && (
        <div className="px-4 py-3 space-y-2 text-sm">
          <div>
            <span className="text-gray-500">設計: </span>
            <span className="text-gray-700">
              {group.docSections.map((s) => s.title).join('、')}
            </span>
          </div>
          <div>
            <span className="text-gray-500">コード: </span>
            <span className="text-gray-700">
              {group.codeSymbols.length > 0
                ? group.codeSymbols.map((s) => s.symbol).join('、')
                : '（なし）'}
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
              <div className="text-gray-700">
                <span className="text-gray-500">サマリー: </span>
                {result.summary}
                {result.statistics && (
                  <span className="ml-2 text-gray-500">
                    （{result.statistics.errors > 0 && `エラー${result.statistics.errors}件`}
                    {result.statistics.warnings > 0 && ` 警告${result.statistics.warnings}件`}）
                  </span>
                )}
              </div>

              {result.findings.length > 0 && (
                <div className="mt-2 space-y-2">
                  {result.findings.slice(0, 3).map((finding) => (
                    <FindingItem key={finding.id} finding={finding} />
                  ))}
                  {result.findings.length > 3 && (
                    <div className="text-gray-500 text-xs">
                      ...他 {result.findings.length - 3} 件
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {status === 'error' && reviewState?.error && (
            <div className="mt-2 pt-2 border-t text-red-600">
              <span className="text-gray-500">エラー: </span>
              {reviewState.error}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function FindingItem({ finding }: { finding: ReviewFinding }) {
  return (
    <div className="bg-gray-50 rounded p-2 text-xs">
      <div className="flex items-center gap-2 mb-1">
        <SeverityBadge severity={finding.severity} />
        <span className="text-gray-700">{finding.description}</span>
      </div>
      <div className="text-gray-500 pl-2">
        {finding.docLocation && (
          <span>設計書: {finding.docLocation.section} L{finding.docLocation.line}</span>
        )}
        {finding.docLocation && finding.codeLocation && <span> / </span>}
        {finding.codeLocation && (
          <span>コード: {finding.codeLocation.symbol} L{finding.codeLocation.line}</span>
        )}
      </div>
    </div>
  )
}

export function SplitExecutingScreen({
  state,
  onBack,
  onPause,
  onResume,
}: SplitExecutingScreenProps) {
  const isPaused = state.phase === 'paused'
  const isRunning = ['structure-matching', 'group-review', 'integrate'].includes(state.phase)

  const structureMatchingStatus = getPhaseStatus(state.phase, 'structure-matching')
  const groupReviewStatus = getPhaseStatus(state.phase, 'group-review')
  const integrateStatus = getPhaseStatus(state.phase, 'integrate')

  const groups = state.structureMatchingResult?.groups || []
  const completedGroups = state.groupReviews.filter((g) => g.status === 'completed').length

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-800">分割レビュー実行中</h1>
          <button onClick={onBack} className="text-blue-500 hover:text-blue-700">
            ← 戻る
          </button>
        </div>
      </div>

      {/* Paused Banner */}
      {isPaused && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-center gap-2 text-yellow-700">
            <Pause className="w-5 h-5" />
            <span className="font-medium">一時停止中</span>
          </div>
          <p className="text-center text-sm text-yellow-600 mt-2">
            2. グループレビュー ({completedGroups}/{groups.length} グループ完了)
          </p>
          <p className="text-center text-sm text-yellow-600">
            完了済みの結果は保持されています。再開すると続きから処理を継続します。
          </p>
        </div>
      )}

      {/* Phase 1: Structure Matching */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-800">1. 構造マッチング</h2>
          <div className="flex items-center gap-2">
            <StatusIcon status={structureMatchingStatus} />
            <StatusText status={structureMatchingStatus} />
          </div>
        </div>

        {structureMatchingStatus === 'in_progress' && (
          <div className="flex items-center gap-2 text-blue-600">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>構造を分析中...</span>
          </div>
        )}

        {structureMatchingStatus === 'completed' && state.structureMatchingResult && (
          <div className="text-sm text-gray-700">
            マッチング結果: {state.structureMatchingResult.totalGroups} グループ
          </div>
        )}
      </div>

      {/* Phase 2: Group Review */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-800">2. グループレビュー</h2>
          <div className="flex items-center gap-2">
            <StatusIcon status={groupReviewStatus} />
            <StatusText status={groupReviewStatus} />
          </div>
        </div>

        {groupReviewStatus !== 'pending' && groups.length > 0 && (
          <div className="space-y-4">
            {groups.map((group, index) => {
              const reviewState = state.groupReviews.find((g) => g.groupId === group.groupId)
              return (
                <div key={group.groupId}>
                  <div className="text-sm text-gray-500 mb-1">2.{index + 1}</div>
                  <GroupCard group={group} reviewState={reviewState} />
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Phase 3: Integration */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-800">3. 結果統合</h2>
          <div className="flex items-center gap-2">
            <StatusIcon status={integrateStatus} />
            <StatusText status={integrateStatus} />
          </div>
        </div>

        {integrateStatus === 'in_progress' && (
          <div className="flex items-center gap-2 text-blue-600">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>結果を統合中...</span>
          </div>
        )}

        {integrateStatus === 'completed' && state.integrateResult?.integratedReport && (
          <div className="text-sm text-gray-700">
            <div className="mb-2">
              <span className="text-gray-500">総合評価: </span>
              {state.integrateResult.integratedReport.overallSummary}
            </div>
            <div>
              <span className="text-gray-500">整合性スコア: </span>
              {Math.round(state.integrateResult.integratedReport.consistencyScore * 100)}%
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex justify-center">
        {isRunning && (
          <button
            onClick={onPause}
            className="flex items-center gap-2 px-6 py-3 bg-yellow-500 hover:bg-yellow-600 text-white rounded-md transition"
          >
            <Pause className="w-5 h-5" />
            一時停止
          </button>
        )}

        {isPaused && (
          <button
            onClick={onResume}
            className="flex items-center gap-2 px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-md transition"
          >
            <Play className="w-5 h-5" />
            再開
          </button>
        )}
      </div>
    </div>
  )
}
