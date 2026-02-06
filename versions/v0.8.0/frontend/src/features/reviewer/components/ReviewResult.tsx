import {
  XCircle,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  FileText,
  Clipboard,
  Save,
  Package,
  Download,
} from 'lucide-react'
import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '@core/index'
import { ExecutionInfo } from './ExecutionInfo'
import type { ReviewExecutionData, SimpleJudgment, SplitReviewState } from '../types'

interface ReviewResultProps {
  results: (ReviewExecutionData | null)[]
  currentTab: number
  onTabChange: (tab: number) => void
  onCopyReport: (report: string) => void
  onDownloadReport: (report: string, executionNumber: number) => void
  onDownloadZip: (data: ReviewExecutionData, executionNumber: number) => void
  getSimpleJudgment: (reportText: string) => SimpleJudgment
  onBack: () => void
  // 分割レビュー用（オプション）
  splitReviewState?: SplitReviewState
  splitReviewData?: ReviewExecutionData // 分割レビュー用のダウンロードデータ
  isSplitMode?: boolean
}

export function ReviewResult({
  results,
  currentTab,
  onTabChange,
  onCopyReport,
  onDownloadReport,
  onDownloadZip,
  getSimpleJudgment,
  onBack,
  splitReviewState,
  splitReviewData,
  isSplitMode = false,
}: ReviewResultProps) {
  const currentResult = results[currentTab - 1]

  const statusConfig = {
    ng: {
      label: '問題あり',
      icon: <XCircle className="w-6 h-6 text-red-600" />,
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      textColor: 'text-red-700',
      iconBg: 'bg-red-100',
    },
    warning: {
      label: '確認が必要',
      icon: <AlertTriangle className="w-6 h-6 text-yellow-600" />,
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      textColor: 'text-yellow-700',
      iconBg: 'bg-yellow-100',
    },
    ok: {
      label: '問題なし',
      icon: <CheckCircle className="w-6 h-6 text-green-600" />,
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      textColor: 'text-green-700',
      iconBg: 'bg-green-100',
    },
    unknown: {
      label: '不明',
      icon: <HelpCircle className="w-6 h-6 text-gray-600" />,
      bgColor: 'bg-gray-50',
      borderColor: 'border-gray-200',
      textColor: 'text-gray-700',
      iconBg: 'bg-gray-100',
    },
  }

  const renderSimpleJudgment = (judgment: SimpleJudgment) => {
    const config = statusConfig[judgment.status]
    const countParts = []
    if (judgment.ngCount > 0) {
      countParts.push(`NG: ${judgment.ngCount}件`)
    }
    if (judgment.warningCount > 0) {
      countParts.push(`要確認: ${judgment.warningCount}件`)
    }
    if (judgment.okCount > 0) {
      countParts.push(`OK: ${judgment.okCount}件`)
    }
    const countText = countParts.length > 0 ? countParts.join(' / ') : '検出なし'

    return (
      <div className={`${config.bgColor} ${config.borderColor} border rounded-lg p-4`}>
        <div className="flex items-center gap-3">
          <span className={`${config.iconBg} rounded-full p-2`}>{config.icon}</span>
          <div>
            <div className={`font-bold ${config.textColor} text-lg`}>{config.label}</div>
            <div className="text-sm text-gray-600">{countText}</div>
          </div>
        </div>
      </div>
    )
  }

  const downloadFiles = [
    { name: 'README.md', desc: 'レビュー情報と同梱ファイルの説明' },
    { name: 'system-prompt.md', desc: 'システムプロンプト（役割・目的・出力形式・注意事項）' },
    { name: 'spec-markdown.md', desc: '変換後の設計書（マークダウン形式）' },
    { name: 'code-numbered.txt', desc: '行番号付きプログラム' },
    { name: 'review-result.md', desc: 'AIレビュー結果' },
  ]

  // 分割レビュー用のグループ一覧テーブル（カスタム領域）
  const renderGroupsTable = () => {
    if (!splitReviewState?.structureMatchingResult) return null

    return (
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">グループ一覧:</h3>
        <div className="overflow-x-auto">
          <Table className="min-w-full text-sm">
            <TableHead>
              <TableRow>
                <TableHeaderCell>グループ名</TableHeaderCell>
                <TableHeaderCell>設計書セクション</TableHeaderCell>
                <TableHeaderCell>コードシンボル</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {splitReviewState.structureMatchingResult.groups.map((group) => (
                <TableRow key={group.groupId}>
                  <TableCell>{group.groupName}</TableCell>
                  <TableCell>{group.docSections.map((s) => s.title).join(', ')}</TableCell>
                  <TableCell>{group.codeSymbols.map((s) => s.symbol).join(', ')}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    )
  }

  // 分割モードかつ結果がある場合
  if (isSplitMode && splitReviewState?.integrateResult) {
    // APIから返されたMarkdownレポートを使用
    const splitReportText = splitReviewState.integrateResult.report || ''
    // 一括レビューと同じ方法で簡易判定を行う
    const splitJudgment = getSimpleJudgment(splitReportText)

    return (
      <div className="max-w-4xl mx-auto p-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex justify-between items-center">
            <h1 className="text-xl font-bold text-gray-800">分割レビュー結果</h1>
            <button onClick={onBack} className="text-blue-500 hover:text-blue-700">
              ← 戻る
            </button>
          </div>
        </div>

        {/* Simple judgment */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">簡易判定</h2>
          {renderSimpleJudgment(splitJudgment)}
          <p className="text-xs text-gray-400 mt-3">
            ※ この判定はキーワードに基づく簡易的なものです。AIの出力によっては正しく判定されない場合があります。詳細レポートを確認してください。
          </p>
        </div>

        {/* Execution info */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">実行情報</h2>
          <ExecutionInfo
            version={splitReviewData?.reviewMeta.version || 'unknown'}
            modelId={splitReviewData?.reviewMeta.modelId || 'unknown'}
            executedAt={splitReviewData?.reviewMeta.executedAt || new Date().toISOString()}
            inputTokens={splitReviewData?.reviewMeta.inputTokens}
            outputTokens={splitReviewData?.reviewMeta.outputTokens}
            designs={splitReviewData?.reviewMeta.designs}
            programs={splitReviewData?.reviewMeta.programs}
          >
            {renderGroupsTable()}
          </ExecutionInfo>
        </div>

        {/* Detailed report */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5" /> 詳細レポート
          </h2>
          <div className="bg-gray-50 rounded-lg p-4 font-mono text-sm overflow-auto max-h-96 mb-4">
            <pre className="whitespace-pre-wrap text-gray-700">{splitReportText}</pre>
          </div>
          {/* Action buttons */}
          <div className="flex gap-4">
            <button
              onClick={() => onCopyReport(splitReportText)}
              className="flex-1 bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 rounded-lg shadow-md transition text-sm flex items-center justify-center gap-2"
            >
              <Clipboard className="w-4 h-4" /> コピー
            </button>
            <button
              onClick={() => onDownloadReport(splitReportText, 1)}
              className="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 rounded-lg shadow-md transition text-sm flex items-center justify-center gap-2"
            >
              <Save className="w-4 h-4" /> ダウンロード
            </button>
          </div>
        </div>

        {/* Zip download */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Package className="w-5 h-5" /> レビュー実行データ一式ダウンロード
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            レビュー実行の入出力データを一式ダウンロードできます。
          </p>

          {/* Download file list */}
          <div className="bg-gray-50 rounded-lg p-4 mb-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">ダウンロード内容:</h3>
            <Table className="text-sm text-gray-600">
              <TableBody>
                {downloadFiles.map((f) => (
                  <TableRow key={f.name}>
                    <TableCell className="font-mono text-xs py-1 pr-2 align-top whitespace-nowrap border-0">
                      {f.name}
                    </TableCell>
                    <TableCell className="py-1 border-0">{f.desc}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          <button
            onClick={() => splitReviewData && onDownloadZip(splitReviewData, 1)}
            disabled={!splitReviewData}
            className={`w-full font-bold py-3 rounded-lg shadow-md transition flex items-center justify-center gap-2 ${
              splitReviewData
                ? 'bg-green-500 hover:bg-green-600 text-white'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            <Download className="w-5 h-5" /> 一式ダウンロード（ZIP）
          </button>
        </div>
      </div>
    )
  }

  // 通常モード
  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header with tabs */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-xl font-bold text-gray-800">レビュー結果</h1>
          <button onClick={onBack} className="text-blue-500 hover:text-blue-700">
            ← 戻る
          </button>
        </div>
        {/* Tab buttons */}
        <div className="flex gap-2">
          {[1, 2].map((tabNum) => (
            <button
              key={tabNum}
              onClick={() => onTabChange(tabNum)}
              className={`flex-1 py-2 px-4 rounded-lg font-medium transition ${
                currentTab === tabNum
                  ? 'text-white bg-blue-500'
                  : 'text-gray-600 bg-gray-100 hover:bg-gray-200'
              }`}
            >
              {tabNum}回目
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-400 mt-2 text-center">
          ※ 同じ設定で2回レビューを実行しました。それぞれ個別に結果を確認できます。
        </p>
      </div>

      {currentResult && (
        <>
          {/* Simple judgment */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">簡易判定</h2>
            {renderSimpleJudgment(getSimpleJudgment(currentResult.report))}
            <p className="text-xs text-gray-400 mt-3">
              ※
              この判定はキーワードに基づく簡易的なものです。AIの出力によっては正しく判定されない場合があります。詳細レポートを確認してください。
            </p>
          </div>

          {/* Execution info */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">実行情報</h2>
            <ExecutionInfo
              version={currentResult.reviewMeta.version}
              modelId={currentResult.reviewMeta.modelId}
              executedAt={currentResult.reviewMeta.executedAt}
              inputTokens={currentResult.reviewMeta.inputTokens}
              outputTokens={currentResult.reviewMeta.outputTokens}
              designs={currentResult.reviewMeta.designs}
              programs={currentResult.reviewMeta.programs}
            />
          </div>

          {/* Detailed report */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5" /> 詳細レポート
            </h2>
            <div className="bg-gray-50 rounded-lg p-4 font-mono text-sm overflow-auto max-h-96 mb-4">
              <pre className="whitespace-pre-wrap text-gray-700">{currentResult.report}</pre>
            </div>
            {/* Action buttons */}
            <div className="flex gap-4">
              <button
                onClick={() => onCopyReport(currentResult.report)}
                className="flex-1 bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 rounded-lg shadow-md transition text-sm flex items-center justify-center gap-2"
              >
                <Clipboard className="w-4 h-4" /> コピー
              </button>
              <button
                onClick={() => onDownloadReport(currentResult.report, currentTab)}
                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 rounded-lg shadow-md transition text-sm flex items-center justify-center gap-2"
              >
                <Save className="w-4 h-4" /> ダウンロード
              </button>
            </div>
          </div>

          {/* Zip download */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Package className="w-5 h-5" /> レビュー実行データ一式ダウンロード
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              レビュー実行の入出力データを一式ダウンロードできます。
            </p>

            {/* Download file list */}
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">ダウンロード内容:</h3>
              <Table className="text-sm text-gray-600">
                <TableBody>
                  {downloadFiles.map((f) => (
                    <TableRow key={f.name}>
                      <TableCell className="font-mono text-xs py-1 pr-2 align-top whitespace-nowrap border-0">
                        {f.name}
                      </TableCell>
                      <TableCell className="py-1 border-0">{f.desc}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <button
              onClick={() => onDownloadZip(currentResult, currentTab)}
              className="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-3 rounded-lg shadow-md transition flex items-center justify-center gap-2"
            >
              <Download className="w-5 h-5" /> 一式ダウンロード（ZIP）
            </button>
          </div>
        </>
      )}
    </div>
  )
}
