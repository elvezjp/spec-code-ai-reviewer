# 重要セクションの事前要約機能

- 作成日: 2026/02/28
- 対象バージョン: v0.8.2
- ステータス: 実装済み
- 関連: `20260224-v0.8.2-split-review-improvement-plan.md`（重要パート機能）、`20260225-split-review-token-optimization-plan.md`（要約API）

## 背景

分割レビューの「重要」機能により、チェック条件表などの重要セクションを全グループのレビューに含められるようになった。しかし、重要セクションが長大な場合（例: ~15,000トークン）、全グループに同じ内容が展開され、トークン消費が大きくなる。5グループなら ~75,000トークンの消費となり、モデルの入力上限に達するリスクが高い。

## ゴール

1. 分割プレビュー画面で、各設計書パートごとにチェックボックスで「要約」を選択できる
2. 「要約」が選択されたパートは、レビュー実行前に要約APIで事前要約される（1パートずつ逐次実行）
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
SplitSettingsSection（重要チェック + 要約チェックボックス）
  → DocumentPart に summarizeMode / summarizedContent を保持
  → 「選択した要約を実行」ボタンで未要約パートを1パートずつ逐次要約
  → エラー時はそこで中断し、成功済みパートの結果は保持
  → レビュー実行（未要約パートがあれば disabled）
  → Phase 1 完了後、全グループの docSections に注入
  → 各グループの documentContent 構築時に、
    summarizeMode === 'summarize' && summarizedContent があれば要約テキストを使用
  → executeGroupReview() に送信
```

---

## 画面イメージ

### プレビュー結果: 設計書パーツテーブル

「要約」列を重要列の右にチェックボックスとして追加し、各パートごとに要約するかを選択できる。
重要チェックの有無に関わらず、全パートで選択可能。

推定トークン列は、選択中のモードに応じた値を表示する:
- 要約未選択時: 元テキストの推定トークン数
- 要約選択時（未実行）: `未実行`
- 要約選択時（実行済み）: 要約後の推定トークン数

一度要約したパートは、チェックを外しても要約済みテキストがリセットされない。
再度チェックすると、保持されている要約結果がそのまま表示される。

「選択した要約を実行」ボタンは分割プレビューボタンの下行に配置し、
要約チェックが1件以上ある場合に表示される。未要約パートがある場合のみ enabled。
ボタン右に完了/選択件数と説明テキスト（エラー時はエラーメッセージ）を表示する。

要約実行は1パートずつ逐次実行される。完了するたびに即座にテーブルに結果が反映される。
エラー発生時はそのパートで中断し、それまでに成功したパートの結果は保持される。

#### 初期状態（全て未選択）

```
┌─ プレビュー結果 ─────────────────────────────────────────────────────┐
│                                                                      │
│  ■ 設計書: 5 パート                                                   │
│  ・**重要**: 分割レビュー時に全てのグループで参照されます。              │
│  ・**要約**: レビュー時に要約テキストで代替されます。分割後もトークン数  │
│    が多い場合に使用してください。                                      │
│                                                                      │
│  ┌──────┬──────┬────┬──────────────────┬──────────┬──────────┐       │
│  │ 重要  │ 要約  │ #  │ セクション名      │ 行範囲    │推定トークン│       │
│  ├──────┼──────┼────┼──────────────────┼──────────┼──────────┤       │
│  │ [✓]  │ [ ]  │ 1  │ チェック条件表     │ L1-L120  │ ~4,500   │       │
│  │ [ ]  │ [ ]  │ 2  │ 別紙1: 入力仕様   │ L121-200 │ ~2,800   │       │
│  │ [ ]  │ [ ]  │ 3  │ 別紙2: 出力仕様   │ L201-280 │ ~2,200   │       │
│  │ [✓]  │ [ ]  │ 4  │ 別紙3: エラー処理 │ L281-350 │ ~1,900   │       │
│  │ [ ]  │ [ ]  │ 5  │ 別紙4: テーブル定義│ L351-400 │ ~1,500   │       │
│  └──────┴──────┴────┴──────────────────┴──────────┴──────────┘       │
│                                                                      │
│  [分割プレビュー（実行済み）]                                          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

#### 「要約」を選択（未実行）

推定トークンが「未実行」になり、「選択した要約を実行」ボタン行が表示される。

```
│  │ [✓]  │ [✓] │ 1  │ チェック条件表     │ L1-L120  │ 未実行   │       │
│  │ [ ]  │ [ ] │ 2  │ 別紙1: 入力仕様   │ L121-200 │ ~2,800   │       │
│  │ [ ]  │ [ ] │ 3  │ 別紙2: 出力仕様   │ L201-280 │ ~2,200   │       │
│  │ [✓]  │ [✓] │ 4  │ 別紙3: エラー処理 │ L281-350 │ 未実行   │       │
│  │ ...                                                               │
│                                                                      │
│  [分割プレビュー（実行済み）]                                          │
│  [選択した要約を実行]  0/2件  「要約」を選択したセクションを事前に...   │
│  ※ 要約によって微妙なニュアンスや制約が失われることがあります。         │
```

#### 要約実行中（1パートずつ逐次実行）

```
│  │ [✓]  │ [✓] │ 1  │ チェック条件表     │ L1-L120  │ ⟳ 要約中 │       │
│  │ [✓]  │ [✓] │ 4  │ 別紙3: エラー処理 │ L281-350 │ 未実行   │       │
│  │ ...                                                               │
│                                                                      │
│  [分割プレビュー（実行済み）]                                          │
│  [要約実行中...] ← disabled  0/2件  「要約」を選択したセクション...    │
│  ※ 要約によって微妙なニュアンスや制約が失われることがあります。         │
```

#### 要約完了

推定トークンに要約後の値が表示される。アコーディオンで要約結果をプレビュー可能。

```
│  │ [✓]  │ [✓] │ 1  │ チェック条件表     │ L1-L120  │ ~1,500   │       │
│  │      │     │    │ ▶ 要約結果を表示                                │
│  │ [✓]  │ [✓] │ 4  │ 別紙3: エラー処理 │ L281-350 │ ~800     │       │
│  │      │     │    │ ▶ 要約結果を表示                                │
│  │ ...                                                               │
│                                                                      │
│  [分割プレビュー（実行済み）]                                          │
│  [選択した要約を実行] ← disabled  2/2件  「要約」を選択した...         │
│  ※ 要約によって微妙なニュアンスや制約が失われることがあります。         │
```

#### 要約エラー時

エラーが発生したパートで中断。成功済みパートの結果は保持。

```
│  │ [✓]  │ [✓] │ 1  │ チェック条件表     │ L1-L120  │ ~1,500   │       │
│  │ [✓]  │ [✓] │ 4  │ 別紙3: エラー処理 │ L281-350 │ 未実行   │       │
│  │ ...                                                               │
│                                                                      │
│  [分割プレビュー（実行済み）]                                          │
│  [選択した要約を実行]  1/2件  「別紙3: エラー処理」の要約に失敗...     │
│                              (赤色エラーメッセージ)                   │
│  ※ 要約によって微妙なニュアンスや制約が失われることがあります。         │
```

#### 要約済みパートのチェックを外した場合

推定トークンは元の値に戻る。要約済みテキストは内部に保持されたまま。
再度チェックすると、再要約なしで要約後トークン数が表示される。

```
│  │ [✓]  │ [ ] │ 1  │ チェック条件表     │ L1-L120  │ ~4,500   │       │
│  │ [ ]  │ [ ] │ 2  │ 別紙1: 入力仕様   │ L121-200 │ ~2,800   │       │
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

1パートずつ逐次実行し、完了するたびに即座にテーブルに結果を反映する。
エラー発生時はそのパートで中断し、成功済みパートの結果は保持される。
要約実行中のパートIDを `summarizingPartIds` で管理し、テーブルのトークン列に「⟳ 要約中」を表示する。

```typescript
const [summarizingPartIds, setSummarizingPartIds] = useState<Set<string>>(new Set())
const [summarizeError, setSummarizeError] = useState<string | null>(null)

const executeSummarize = useCallback(async (llmConfig?: LlmConfig | null) => {
  if (!previewResult?.documentParts) return

  const targets = previewResult.documentParts.filter(
    (p) => p.summarizeMode === 'summarize' && !p.summarizedContent
  )
  if (targets.length === 0) return

  setIsSummarizing(true)
  setSummarizeError(null)

  // 1パートずつ逐次実行
  for (const part of targets) {
    setSummarizingPartIds(new Set([part.id]))

    try {
      const response = await api.executeSummarize({
        text: part.content,
        targetType: 'design',
        llmConfig: llmConfig || undefined,
      })

      if (response.success) {
        // 完了したパートの結果を即座に反映
        setPreviewResult((prev) => {
          if (!prev || !prev.documentParts) return prev
          return {
            ...prev,
            documentParts: prev.documentParts.map((p) =>
              p.id === part.id
                ? {
                    ...p,
                    summarizedContent: response.summarizedText || undefined,
                    summarizedTokens: response.summarizedTokens || undefined,
                  }
                : p
            ),
          }
        })
      } else {
        setSummarizeError(`「${part.displayName}」の要約に失敗しました: ${response.error || '不明なエラー'}`)
        break  // エラー時は中断、成功済みパートの結果は保持
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : '不明なエラー'
      setSummarizeError(`「${part.displayName}」の要約に失敗しました: ${message}`)
      break
    }
  }

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
  summarizeError: string | null                             // 追加
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
  summarizeError: string | null                             // 追加
  onToggleSummarizeMode: (partId: string) => void           // 追加
  onExecuteSummarize: () => void                            // 追加
}
```

#### 3-b. DocumentPartsTable に「要約」列を追加

列順序: 重要 → 要約 → # → セクション名 → 行範囲 → 推定トークン

要約列はチェックボックス（重要列と同じスタイル）。

推定トークン列の表示ロジック:
- `summarizeMode === 'original'`: 元テキストの `estimatedTokens` を表示
- `summarizeMode === 'summarize'` かつ `summarizedContent` なし: 「未実行」を表示
- `summarizeMode === 'summarize'` かつ `summarizedContent` あり: `summarizedTokens` を表示
- 要約実行中（`isSummarizing` かつ対象パート）: 「⟳ 要約中」を表示

要約済みテキストの保持:
- `toggleSummarizeMode` は `summarizeMode` のみを切り替え、`summarizedContent` / `summarizedTokens` はリセットしない
- これによりチェックを外しても要約済みテキストが保持され、再度チェックすると再要約なしで結果が表示される

案内テキスト（箇条書き形式）:
- 「**重要**: 分割レビュー時に全てのグループで参照されます。」
- 「**要約**: レビュー時に要約テキストで代替されます。分割後もトークン数が多い場合に使用してください。」

```typescript
// 要約列: チェックボックス
<TableHeaderCell className="w-14">要約</TableHeaderCell>

// 各行
<TableCell className="text-center">
  <input
    type="checkbox"
    checked={part.summarizeMode === 'summarize'}
    onChange={() => onToggleSummarizeMode(part.id)}
    className="w-4 h-4 text-blue-600 rounded"
  />
</TableCell>
```

#### 3-c. 「選択した要約を実行」ボタンの追加（SummarizeExecuteRow コンポーネント）

分割プレビューボタンの下行に配置。要約チェックが1件以上ある場合に表示される。

- ボタンは常に表示、未要約パートがある場合のみ enabled
- ボタン右に完了/選択件数（例: `1/2件`）を表示
- さらに右に説明テキスト、エラー時はエラーメッセージ（赤色）を表示
- ボタン行の下に注意書き「※ 要約によって微妙なニュアンスや制約が失われることがあります。」を表示

```tsx
{/* ボタンレイアウト */}
<div className="mb-4 space-y-2">
  {/* 1行目: 分割プレビューボタン */}
  <div className="flex items-center gap-3">
    <button>...</button>
  </div>
  {/* 2行目: 要約実行ボタン（要約チェックが1件以上ある場合に表示） */}
  {previewResult && previewResult.documentParts && (
    <SummarizeExecuteRow ... />
  )}
</div>

{/* SummarizeExecuteRow コンポーネント */}
function SummarizeExecuteRow({ parts, isSummarizing, hasPendingSummarize, summarizeError, onExecuteSummarize }) {
  const totalSelected = parts.filter((p) => p.summarizeMode === 'summarize').length
  const completedCount = parts.filter((p) => p.summarizeMode === 'summarize' && p.summarizedContent).length
  if (totalSelected === 0) return null
  return (
    <div className="flex items-center gap-3">
      <button disabled={!hasPendingSummarize || isSummarizing}>選択した要約を実行</button>
      <span>{completedCount}/{totalSelected}件</span>
      {summarizeError
        ? <span className="text-red-600">{summarizeError}</span>
        : <span>「要約」を選択したセクションを事前に要約します。</span>}
    </div>
  )
}
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
  summarizeError={summarizeError}
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

- [ ] 分割プレビュー結果の設計書パーツテーブルに「要約」列がチェックボックスとして重要列の右に表示されること
- [ ] 各パートの要約チェックボックスのデフォルトが未選択であること
- [ ] 要約チェック未選択時、推定トークン列に元テキストのトークン数が表示されること
- [ ] 要約をチェックすると推定トークン列に「未実行」が表示されること
- [ ] 要約がチェックされたパートがある場合、「選択した要約を実行」ボタン行が表示されること
- [ ] ボタン右に完了/選択件数（例: `0/2件`）と説明テキストが表示されること
- [ ] 「選択した要約を実行」ボタンを押すと1パートずつ逐次実行され、実行中パートの推定トークン列に「⟳ 要約中」が表示されること
- [ ] 各パートの要約完了後、即座に推定トークン列が要約後トークン数（例: `~1,500`）に更新されること
- [ ] 要約完了後、セクション名の下に「要約結果を表示」アコーディオンで要約テキストをプレビューできること
- [ ] 要約済みパートのチェックを外すと推定トークン列が元のトークン数に戻ること
- [ ] 要約済みパートのチェックを外しても要約結果が保持されること（再度チェックすると要約後トークン数が再表示される）
- [ ] 全パート要約完了時、ボタンが disabled になり件数が `2/2件` と表示されること
- [ ] 要約エラー時、エラーメッセージが赤色でボタン右に表示されること
- [ ] 要約エラー時、成功済みパートの結果が保持されていること
- [ ] 要約エラー後に再度ボタンを押すと未要約パートから再実行されること
- [ ] 「要約」選択かつ未実行のパートがある状態でレビュー実行ボタンが disabled になること
- [ ] disabled 時に案内メッセージが表示されること
- [ ] 全ての「要約」選択パートが要約済みの状態でレビュー実行ボタンが active になること
- [ ] 要約未選択の状態ではレビュー実行ボタンが従来通り active であること
- [ ] 要約版の設計書でグループレビューが正常に完了すること
- [ ] グループレビューの documentContent に要約版テキストが含まれていること（API リクエストで確認）
- [ ] 要約版テキストのヘッダーに「[要約版]」が付与されていること
- [ ] 分割プレビューをクリアすると要約状態もリセットされること
- [ ] テーブル上部に重要・要約それぞれの案内テキストが表示されること

### 回帰テスト

- [ ] 一括レビューが従来通り動作すること
- [ ] 要約を使用しない分割レビュー（全パート「そのまま」）が従来通り動作すること
- [ ] 重要パートのチェック機能が従来通り動作すること
