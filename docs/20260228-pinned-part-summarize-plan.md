# 重要セクションの事前要約機能

- 作成日: 2026/02/28
- 対象バージョン: v0.8.2
- ステータス: 計画
- 関連: `20260224-v0.8.2-split-review-improvement-plan.md`（重要パート機能）、`20260225-split-review-token-optimization-plan.md`（要約API）

## 背景

分割レビューの「重要」機能により、チェック条件表などの重要セクションを全グループのレビューに含められるようになった。しかし、重要セクションが長大な場合（例: ~15,000トークン）、全グループに同じ内容が展開され、トークン消費が大きくなる。5グループなら ~75,000トークンの消費となり、モデルの入力上限に達するリスクが高い。

## ゴール

1. 分割プレビュー画面で、各設計書パートごとに「そのまま」「要約」を選択できる
2. 「要約」が選択されたパートは、レビュー実行前に要約APIで事前要約される
3. グループレビュー時に、「要約」が選択されたパートは要約テキストで代替される

## 非ゴール

- コードパーツの事前要約（設計書パーツのみ対象）
- 要約品質の自動評価
- 重要パート以外のパーツの要約（グループレビュー時のトークン超過は既存の施策4で対応）

---

## 現在のデータフロー

```
SplitSettingsSection（重要チェックボックス）
  → pinnedDocPartIds に ID を保存
  → Phase 1 完了後、全グループの docSections に注入
  → 各グループの documentContent 構築時に DocumentPart.content を展開
  → executeGroupReview() に送信
```

## 変更後のデータフロー

```
SplitSettingsSection（重要チェック + そのまま/要約 選択）
  → DocumentPart に summarizeMode / summarizedContent を保持
  → 「要約を実行」ボタンで未要約パートを一括要約
  → レビュー実行（未要約パートがあれば disabled）
  → Phase 1 完了後、全グループの docSections に注入
  → 各グループの documentContent 構築時に、
    summarizeMode === 'summarize' && summarizedContent があれば要約テキストを使用
  → executeGroupReview() に送信
```

---

## 画面イメージ

### プレビュー結果: 設計書パーツテーブル

「要約」列を重要列の右に追加し、各パートごとに「そのまま/要約」を選択できる。
重要チェックの有無に関わらず、全パートで選択可能。

推定トークン列は、選択中のモードに応じた値を表示する:
- 「そのまま」選択時: 元テキストの推定トークン数
- 「要約」選択時（未実行）: `未実行`
- 「要約」選択時（実行済み）: 要約後の推定トークン数

一度要約したパートは、「そのまま」に切り替えても要約済みテキストがリセットされない。
再度「要約」に切り替えると、保持されている要約結果がそのまま表示される。

#### 初期状態（全て「そのまま」）

```
┌─ プレビュー結果 ─────────────────────────────────────────────────────┐
│                                                                      │
│  ■ 設計書: 5 パート                                                   │
│  **重要**にチェックしたセクションは、分割レビュー時に全てのグループで   │
│  参照されます。                                                       │
│                                                                      │
│  ┌──────┬──────────────┬────┬──────────────────┬──────────┬──────────┐│
│  │ 重要  │ 要約          │ #  │ セクション名      │ 行範囲    │推定トークン││
│  ├──────┼──────────────┼────┼──────────────────┼──────────┼──────────┤│
│  │ [✓]  │◉そのまま ○要約│ 1  │ チェック条件表     │ L1-L120  │ ~4,500   ││
│  │ [ ]  │◉そのまま ○要約│ 2  │ 別紙1: 入力仕様   │ L121-200 │ ~2,800   ││
│  │ [ ]  │◉そのまま ○要約│ 3  │ 別紙2: 出力仕様   │ L201-280 │ ~2,200   ││
│  │ [✓]  │◉そのまま ○要約│ 4  │ 別紙3: エラー処理 │ L281-350 │ ~1,900   ││
│  │ [ ]  │◉そのまま ○要約│ 5  │ 別紙4: テーブル定義│ L351-400 │ ~1,500   ││
│  └──────┴──────────────┴────┴──────────────────┴──────────┴──────────┘│
│                                                                      │
│  [分割プレビュー（実行済み）]                                          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

#### 「要約」を選択（未実行）

推定トークンが「未実行」になり、「選択した要約を実行」ボタンが表示される。

```
│  │ [✓]  │○そのまま ◉要約│ 1  │ チェック条件表     │ L1-L120  │ 未実行   ││
│  │ [ ]  │◉そのまま ○要約│ 2  │ 別紙1: 入力仕様   │ L121-200 │ ~2,800   ││
│  │ ...                                                               │
│                                                                      │
│  [分割プレビュー（実行済み）]  [選択した要約を実行]                      │
│                               (blue/small)                           │
```

#### 要約実行中

```
│  │ [✓]  │○そのまま ◉要約│ 1  │ チェック条件表     │ L1-L120  │ ⟳ 要約中 ││
│  │ [ ]  │◉そのまま ○要約│ 2  │ 別紙1: 入力仕様   │ L121-200 │ ~2,800   ││
│  │ ...                                                               │
│                                                                      │
│  [分割プレビュー（実行済み）]  [選択した要約を実行] ← disabled          │
```

#### 要約完了

推定トークンに要約後の値と削減率が表示される。アコーディオンで要約結果をプレビュー可能。

```
│  │ [✓]  │○そのまま ◉要約│ 1  │ チェック条件表     │ L1-L120  │ ~1,500   ││
│  │      │              │    │ ▶ 要約結果を表示                        ││
│  │ [ ]  │◉そのまま ○要約│ 2  │ 別紙1: 入力仕様   │ L121-200 │ ~2,800   ││
│  │ ...                                                               │
│                                                                      │
│  [分割プレビュー（実行済み）]                                          │
```

#### 要約済みパートを「そのまま」に戻した場合

推定トークンは元の値に戻る。要約済みテキストは内部に保持されたまま。
再度「要約」に切り替えると、再要約なしで要約後トークン数が表示される。

```
│  │ [✓]  │◉そのまま ○要約│ 1  │ チェック条件表     │ L1-L120  │ ~4,500   ││
│  │ [ ]  │◉そのまま ○要約│ 2  │ 別紙1: 入力仕様   │ L121-200 │ ~2,800   ││
```

### 「要約」選択かつ未実行時のレビュー実行ボタン

```
│  [レビュー実行] ← disabled                                                │
│  ⚠ 要約が選択されていますが未実行です。「選択した要約を実行」を             │
│  クリックしてから、レビューを実行してください。                              │
```

---

## 実装ステップ

### Step 1. DocumentPart に要約関連フィールドを追加

対象: `versions/v0.8.2/frontend/src/features/reviewer/types/index.ts`

現在:
```typescript
export interface DocumentPart {
  id: string
  section: string
  displayName: string
  level: number
  path: string
  startLine: number
  endLine: number
  content: string
  estimatedTokens: number
}
```

変更後:
```typescript
export interface DocumentPart {
  id: string
  section: string
  displayName: string
  level: number
  path: string
  startLine: number
  endLine: number
  content: string
  estimatedTokens: number
  // 要約関連
  summarizeMode: 'original' | 'summarize'  // デフォルト: 'original'
  summarizedContent?: string               // 要約済みテキスト
  summarizedTokens?: number                // 要約後の推定トークン数
}
```

### Step 2. useSplitSettings に要約状態管理を追加

対象: `versions/v0.8.2/frontend/src/features/reviewer/hooks/useSplitSettings.ts`

#### 2-a. 要約モード切替関数を追加

`summarizeMode` のみを切り替え、`summarizedContent` / `summarizedTokens` はリセットしない。
これにより、一度要約したパートは「そのまま」に戻しても要約結果が保持される。

```typescript
const toggleSummarizeMode = useCallback((partId: string) => {
  setPreviewResult((prev) => {
    if (!prev || !prev.documentParts) return prev
    return {
      ...prev,
      documentParts: prev.documentParts.map((p) =>
        p.id === partId
          ? {
              ...p,
              // summarizeMode のみ切替。summarizedContent / summarizedTokens は保持
              summarizeMode: p.summarizeMode === 'summarize' ? 'original' : 'summarize',
            }
          : p
      ),
    }
  })
}, [])
```

#### 2-b. 要約実行関数を追加

要約実行中のパートIDを `summarizingPartIds` で管理し、テーブルのトークン列に「⟳ 要約中」を表示する。

```typescript
const [summarizingPartIds, setSummarizingPartIds] = useState<Set<string>>(new Set())

const executeSummarize = useCallback(async (llmConfig?: LlmConfig | null) => {
  if (!previewResult?.documentParts) return

  // 「要約」が選択されていて、かつ未要約のパートを対象
  const targets = previewResult.documentParts.filter(
    (p) => p.summarizeMode === 'summarize' && !p.summarizedContent
  )
  if (targets.length === 0) return

  setIsSummarizing(true)
  setSummarizingPartIds(new Set(targets.map((p) => p.id)))

  // 並列で要約API呼び出し
  const results = await Promise.all(
    targets.map(async (part) => {
      const response = await executeSummarizeApi({
        text: part.content,
        targetType: 'design',
        llmConfig: llmConfig || undefined,
      })
      return { partId: part.id, response }
    })
  )

  // 要約結果を DocumentPart に反映
  setPreviewResult((prev) => {
    if (!prev || !prev.documentParts) return prev
    return {
      ...prev,
      documentParts: prev.documentParts.map((p) => {
        const result = results.find((r) => r.partId === p.id)
        if (!result || !result.response.success) return p
        return {
          ...p,
          summarizedContent: result.response.summarizedText || undefined,
          summarizedTokens: result.response.summarizedTokens || undefined,
        }
      }),
    }
  })

  setSummarizingPartIds(new Set())
  setIsSummarizing(false)
}, [previewResult])
```

#### 2-c. 未要約パートの有無を判定するComputed値

```typescript
// 「要約」選択かつ未要約のパートが存在するか
const hasPendingSummarize = useMemo(() => {
  if (!previewResult?.documentParts) return false
  return previewResult.documentParts.some(
    (p) => p.summarizeMode === 'summarize' && !p.summarizedContent
  )
}, [previewResult])
```

#### 2-d. UseSplitSettingsReturn に追加

```typescript
interface UseSplitSettingsReturn {
  // ... 既存フィールド
  isSummarizing: boolean                                    // 追加
  summarizingPartIds: Set<string>                           // 追加
  hasPendingSummarize: boolean                              // 追加
  toggleSummarizeMode: (partId: string) => void             // 追加
  executeSummarize: (llmConfig?: LlmConfig | null) => Promise<void>  // 追加
}
```

#### 2-e. previewResult 初期化時に summarizeMode を設定

```typescript
setPreviewResult({
  documentParts: documentParts.map((p) => ({ ...p, summarizeMode: 'original' as const })),
  // ... 他のフィールド
})
```

#### 2-f. clearPreview 時のリセット

clearPreview は既に `setPreviewResult(null)` を行うため、追加の処理は不要。

### Step 3. SplitSettingsSection の DocumentPartsTable を拡張

対象: `versions/v0.8.2/frontend/src/features/reviewer/components/SplitSettingsSection.tsx`

#### 3-a. SplitSettingsSectionProps に追加

```typescript
interface SplitSettingsSectionProps {
  // ... 既存props
  isSummarizing: boolean                                    // 追加
  summarizingPartIds: Set<string>                           // 追加
  hasPendingSummarize: boolean                              // 追加
  onToggleSummarizeMode: (partId: string) => void           // 追加
  onExecuteSummarize: () => void                            // 追加
}
```

#### 3-b. DocumentPartsTable に「要約」列を追加

列順序: 重要 → 要約 → # → セクション名 → 行範囲 → 推定トークン

推定トークン列の表示ロジック:
- `summarizeMode === 'original'`: 元テキストの `estimatedTokens` を表示
- `summarizeMode === 'summarize'` かつ `summarizedContent` なし: 「未実行」を表示
- `summarizeMode === 'summarize'` かつ `summarizedContent` あり: `summarizedTokens` を表示
- 要約実行中（`isSummarizing` かつ対象パート）: 「⟳ 要約中」を表示

要約済みテキストの保持:
- `toggleSummarizeMode` は `summarizeMode` のみを切り替え、`summarizedContent` / `summarizedTokens` はリセットしない
- これにより「そのまま」に戻しても要約済みテキストが保持され、再度「要約」にすると再要約なしで結果が表示される

```typescript
function DocumentPartsTable({
  parts,
  pinnedDocPartIds,
  onTogglePinnedDocPart,
  onToggleSummarizeMode,
  summarizingPartIds,  // 要約実行中のパートID一覧
}: {
  parts: DocumentPart[]
  pinnedDocPartIds: string[]
  onTogglePinnedDocPart: (partId: string) => void
  onToggleSummarizeMode: (partId: string) => void
  summarizingPartIds: Set<string>
}) {
  return (
    <div className="overflow-x-auto">
      <Table className="min-w-full text-sm">
        <TableHead>
          <TableRow>
            <TableHeaderCell className="w-14">重要</TableHeaderCell>
            <TableHeaderCell className="w-40">要約</TableHeaderCell>
            <TableHeaderCell className="w-12">#</TableHeaderCell>
            <TableHeaderCell>セクション名</TableHeaderCell>
            <TableHeaderCell className="w-24">行範囲</TableHeaderCell>
            <TableHeaderCell className="w-28">推定トークン</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {parts.map((part, index) => {
            const isSummarizingThis = summarizingPartIds.has(part.id)
            return (
              <TableRow key={`${part.id}-${part.startLine}`}>
                {/* 重要チェックボックス */}
                <TableCell className="text-center">
                  <input
                    type="checkbox"
                    checked={pinnedDocPartIds.includes(part.id)}
                    onChange={() => onTogglePinnedDocPart(part.id)}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                </TableCell>
                {/* 要約選択（ラジオボタン） */}
                <TableCell>
                  <div className="flex items-center gap-2">
                    <label className="flex items-center gap-1 text-xs cursor-pointer">
                      <input
                        type="radio"
                        name={`summarize-${part.id}`}
                        checked={part.summarizeMode === 'original'}
                        onChange={() => {
                          if (part.summarizeMode !== 'original') onToggleSummarizeMode(part.id)
                        }}
                        className="w-3 h-3"
                      />
                      そのまま
                    </label>
                    <label className="flex items-center gap-1 text-xs cursor-pointer">
                      <input
                        type="radio"
                        name={`summarize-${part.id}`}
                        checked={part.summarizeMode === 'summarize'}
                        onChange={() => {
                          if (part.summarizeMode !== 'summarize') onToggleSummarizeMode(part.id)
                        }}
                        className="w-3 h-3"
                      />
                      要約
                    </label>
                  </div>
                </TableCell>
                <TableCell>{index + 1}</TableCell>
                <TableCell>
                  {part.displayName}
                  {/* 要約完了時のプレビューアコーディオン */}
                  {part.summarizedContent && part.summarizeMode === 'summarize' && (
                    <SummarizedTextPreview
                      label="要約結果を表示"
                      text={part.summarizedContent}
                    />
                  )}
                </TableCell>
                <TableCell className="text-gray-600">
                  L{part.startLine}-L{part.endLine}
                </TableCell>
                {/* 推定トークン: 選択モードに応じた表示 */}
                <TableCell className="text-gray-600">
                  {isSummarizingThis ? (
                    <span className="text-blue-600">⟳ 要約中</span>
                  ) : part.summarizeMode === 'summarize' ? (
                    part.summarizedContent && part.summarizedTokens ? (
                      <span>~{part.summarizedTokens.toLocaleString()}</span>
                    ) : (
                      <span className="text-amber-600">未実行</span>
                    )
                  ) : (
                    <span>~{part.estimatedTokens.toLocaleString()}</span>
                  )}
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}
```

#### 3-c. 「選択した要約を実行」ボタンの追加

プレビュー結果セクション内、テーブルの下（分割プレビューボタンの横）に配置。

対象: `SplitSettingsSection.tsx:264-289`（ボタン配置エリア）

```tsx
{/* 分割プレビュー実行ボタン + 要約実行ボタン */}
{isSplitEnabled && (
  <div className="mb-4 flex items-center gap-3">
    <button
      onClick={onExecutePreview}
      disabled={!canExecutePreview || isExecuting || !!previewResult}
      className="..."
    >
      {/* 既存のプレビューボタン */}
    </button>

    {/* 要約実行ボタン: 「要約」選択かつ未実行のパートがある場合に表示 */}
    {previewResult && hasPendingSummarize && (
      <button
        onClick={onExecuteSummarize}
        disabled={isSummarizing}
        className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm transition disabled:bg-gray-300 disabled:cursor-not-allowed"
      >
        {isSummarizing ? (
          <>
            <Loader2 className="w-4 h-4 inline mr-1 animate-spin" />
            要約実行中...
          </>
        ) : (
          '選択した要約を実行'
        )}
      </button>
    )}

    {settings.documentSplitMode === 'ai' && (
      <span className="text-xs text-muted text-gray-400">...</span>
    )}
  </div>
)}
```

### Step 4. レビュー実行ボタンのdisabled判定を更新

対象: `versions/v0.8.2/frontend/src/features/reviewer/index.tsx:855-873`

現在:
```typescript
disabled={!isReviewEnabled || (isSplitEnabled && !splitPreviewResult)}
```

変更後:
```typescript
disabled={!isReviewEnabled || (isSplitEnabled && !splitPreviewResult) || (isSplitEnabled && hasPendingSummarize)}
```

案内メッセージの追加:
```tsx
{isSplitEnabled && hasPendingSummarize && (
  <p className="text-xs text-orange-500 mt-1 text-center">
    ⚠ 要約が選択されていますが未実行です。「選択した要約を実行」をクリックしてから、レビューを実行してください。
  </p>
)}
```

### Step 5. グループレビューの documentContent 構築を更新

対象: `versions/v0.8.2/frontend/src/features/reviewer/index.tsx:441-448`

現在:
```typescript
const documentContent = group.docSections.map((section) => {
  const part = splitPreviewResult.documentParts?.find((p) => p.id === section.id)
  const displayName = part?.displayName || section.title
  const startLine = part?.startLine || 0
  const endLine = part?.endLine || 0
  const content = part?.content || ''
  return `### ${displayName} (L${startLine}-L${endLine})\n\n${content}`
}).join('\n\n')
```

変更後:
```typescript
const documentContent = group.docSections.map((section) => {
  const part = splitPreviewResult.documentParts?.find((p) => p.id === section.id)
  const displayName = part?.displayName || section.title
  const startLine = part?.startLine || 0
  const endLine = part?.endLine || 0
  // 「要約」が選択されていて要約済みなら要約テキストを使用
  const content = (part?.summarizeMode === 'summarize' && part?.summarizedContent)
    ? part.summarizedContent
    : part?.content || ''
  const isSummarized = part?.summarizeMode === 'summarize' && !!part?.summarizedContent
  const header = isSummarized
    ? `### ${displayName} (L${startLine}-L${endLine}) [要約版]\n`
    : `### ${displayName} (L${startLine}-L${endLine})\n`
  return `${header}\n${content}`
}).join('\n\n')
```

### Step 6. index.tsx から useSplitSettings の新しい値を SplitSettingsSection に渡す

対象: `versions/v0.8.2/frontend/src/features/reviewer/index.tsx`（SplitSettingsSection の呼び出し箇所）

```tsx
<SplitSettingsSection
  // ... 既存props
  isSummarizing={isSummarizing}
  summarizingPartIds={summarizingPartIds}
  hasPendingSummarize={hasPendingSummarize}
  onToggleSummarizeMode={toggleSummarizeMode}
  onExecuteSummarize={() => executeSummarize(llmConfig)}
/>
```

---

## 影響ファイル一覧

| ファイル | Step | 変更内容 |
|---------|------|---------|
| `versions/v0.8.2/frontend/src/features/reviewer/types/index.ts` | 1 | DocumentPart に summarizeMode / summarizedContent / summarizedTokens 追加 |
| `versions/v0.8.2/frontend/src/features/reviewer/hooks/useSplitSettings.ts` | 2 | toggleSummarizeMode / executeSummarize / hasPendingSummarize 追加 |
| `versions/v0.8.2/frontend/src/features/reviewer/components/SplitSettingsSection.tsx` | 3 | DocumentPartsTable に要約列追加、要約実行ボタン追加 |
| `versions/v0.8.2/frontend/src/features/reviewer/index.tsx` | 4, 5, 6 | レビュー実行ボタンdisabled更新、documentContent構築の要約対応、props渡し |

---

## 品質への影響と注意事項

- 要約によって設計書の細かい仕様（数値条件、境界値、例外条件）が失われる可能性がある
- 要約結果のプレビュー機能（アコーディオン表示）により、ユーザーが要約内容を確認してからレビューを実行できる
- 要約は既存の `/review/summarize` API（`targetType: "design"`）を使用するため、要約プロンプトの品質は施策3で定義済みの内容に依存する

---

## 試験項目表

### ブラウザ操作確認（UIで確認）

- [ ] 分割プレビュー結果の設計書パーツテーブルに「要約」列が重要列の右に表示されること
- [ ] 各パートに「そのまま」「要約」のラジオボタンが表示され、デフォルトは「そのまま」であること
- [ ] 「そのまま」選択時、推定トークン列に元テキストのトークン数が表示されること
- [ ] 「要約」を選択すると推定トークン列に「未実行」が表示されること
- [ ] 「要約」が選択されたパートがある場合、「選択した要約を実行」ボタンが表示されること
- [ ] 「選択した要約を実行」ボタンを押すと要約が実行され、推定トークン列に「⟳ 要約中」が表示されること
- [ ] 要約完了後、推定トークン列に要約後トークン数（例: `~1,500`）が表示されること
- [ ] 要約完了後、セクション名の下に「要約結果を表示」アコーディオンで要約テキストをプレビューできること
- [ ] 要約済みパートを「そのまま」に戻すと推定トークン列が元のトークン数に戻ること
- [ ] 要約済みパートを「そのまま」に戻しても要約結果が保持されること（再度「要約」にすると要約後トークン数が再表示される）
- [ ] 「要約」選択かつ未実行のパートがある状態でレビュー実行ボタンが disabled になること
- [ ] disabled 時に案内メッセージが表示されること
- [ ] 全ての「要約」選択パートが要約済みの状態でレビュー実行ボタンが active になること
- [ ] 「そのまま」のみの状態（要約未選択）ではレビュー実行ボタンが従来通り active であること
- [ ] 要約版の設計書でグループレビューが正常に完了すること
- [ ] グループレビューの documentContent に要約版テキストが含まれていること（API リクエストで確認）
- [ ] 要約版テキストのヘッダーに「[要約版]」が付与されていること
- [ ] 分割プレビューをクリアすると要約状態もリセットされること

### 回帰テスト

- [ ] 一括レビューが従来通り動作すること
- [ ] 要約を使用しない分割レビュー（全パート「そのまま」）が従来通り動作すること
- [ ] 重要パートのチェック機能が従来通り動作すること
