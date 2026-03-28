# コードパートの除外・重要指定・要約機能 修正計画書

## 概要

分割レビューのコードパート一覧に、設計書パートと同等の「除外・重要指定・要約」機能を追加する。
これにより、20,000行超の巨大クラスシンボルをレビュー対象から除外したり、事前要約でトークンを削減したりできるようにする。

対応 Issue: [#90](https://github.com/elvezjp/spec-code-ai-reviewer/issues/90)

## 背景

分割レビューモードで、code2map が生成するクラスシンボルにはクラス全体のソースコード（例: 20,000行）が含まれる。
メソッドは個別シンボル（CD2, CD3, ...）として抽出されるが、クラスシンボル（CD1）にも全メソッドのコードが重複して含まれるため、
構造マッチングでクラスシンボルがグループレビュー対象に選ばれるとトークン上限でエラーになる。

さらにこのシンボル単体でトークン上限を超えるため、リトライ時の要約実行もエラーとなり、トークン数を削減する手段がない。

### 現状

| 機能 | 設計書パート | コードパート |
|---|---|---|
| 除外 | あり（`excluded` チェックボックス） | **なし** |
| 重要指定 | あり（`pinnedDocPartIds`） | **なし** |
| 要約 | あり（`summarizeMode` + 要約実行ボタン） | **なし**（リトライ時のみ対応） |

コードパートの一覧テーブル（`CodePartsTable`）は読み取り専用で、シンボル名・種別・行範囲・推定トークンのみ表示している。

### 解決策

設計書パートの除外・重要指定・要約の仕組みをコードパートにも横展開する。
バックエンドの `/api/summarize` は既に `targetType: "code"` に対応しているため、**バックエンド変更は不要**。

## UX フロー

### 現状のフロー（v0.9.5）

```
分割プレビュー実行
→ 設計書パート一覧: 重要・要約・除外を選択可能
→ コードパート一覧: 読み取り専用（操作不可）
→ レビュー開始
```

### 改善後のフロー（v0.9.6）

```
分割プレビュー実行
→ 設計書パート一覧: 重要・要約・除外を選択可能（変更なし）
→ コードパート一覧: 重要・要約・除外を選択可能（新規追加）
→ レビュー開始
```

### 変更後の画面イメージ

#### コードパート一覧テーブル（変更前 v0.9.5）

```
│ ■ プログラム: 50 パート                                              │
│                                                                      │
│  #  シンボル名                    種別     行範囲        推定トークン  │
│ ┌───┬────────────────────────────┬────────┬────────────┬────────────┐ │
│ │  1│ MyService                  │ class  │ L1-L20000  │  ~300,000  │ │
│ │  2│ MyService#methodA          │ method │ L10-L60    │      ~750  │ │
│ │  3│ MyService#methodB          │ method │ L61-L140   │    ~1,200  │ │
│ │...│ ...                        │ ...    │ ...        │      ...   │ │
│ │ 50│ MyService#methodZ          │ method │ L19950-L20000│    ~450  │ │
│ └───┴────────────────────────────┴────────┴────────────┴────────────┘ │
```

#### コードパート一覧テーブル（変更後 v0.9.6）

```
│ ■ プログラム: 50 パート                                              │
│                                                                      │
│ 重要 要約 除外  #  シンボル名               種別     行範囲        推定トークン│
│ ┌──┬──┬──┬───┬──────────────────────────┬────────┬────────────┬──────────┐│
│ │☐ │☐ │☑ │  1│ MyService               │ class  │ L1-L20000  │ ~300,000 ││
│ │  │  │  │   │                         │        │            │ ← 除外   ││
│ │☐ │☐ │☐ │  2│ MyService#methodA       │ method │ L10-L60    │     ~750 ││
│ │☐ │☐ │☐ │  3│ MyService#methodB       │ method │ L61-L140   │   ~1,200 ││
│ │...│  │  │...│ ...                     │ ...    │ ...        │     ...  ││
│ │☐ │☐ │☐ │ 50│ MyService#methodZ       │ method │ L19950-    │     ~450 ││
│ │  │  │  │   │                         │        │ L20000     │          ││
│ └──┴──┴──┴───┴──────────────────────────┴────────┴────────────┴──────────┘│
│                                                                          │
│ 要約対象: 0件  [ 要約実行 ]                                               │
│                                                                          │
│ ※ 除外されたパートは行がグレーアウトされます（opacity-40）                 │
│ ※ 除外中は重要・要約チェックボックスが無効化されます                       │
```

---

## 前提

- 現在の実装: `versions/v0.9.5`
- `versions/v0.9.5` を丸ごとコピーして `versions/v0.9.6` を作成し、v0.9.6 上で修正を行う
- バックエンドの `/api/summarize` は既に `targetType: "code"` に対応済み（変更不要）
- 設計書パートの除外・重要指定・要約の実装パターンを踏襲する

---

## Step 0: v0.9.6 ディレクトリの作成

- `versions/v0.9.5` を `versions/v0.9.6` にコピー
- v0.9.6 の spec.md にバージョン番号を反映
- インフラ設定（Docker/Nginx/PM2）に v0.9.6 を追加
- `latest` シンボリックリンクを v0.9.6 に更新
- 全バージョンの `useVersions.ts` に v0.9.6 を追加

---

## Step 1: フロントエンド — 型定義の拡張

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.6/frontend/src/features/reviewer/types/index.ts` | `CodePart` インターフェースに除外・要約フィールドを追加 |

### CodePart の変更

```typescript
export interface CodePart {
  id: string
  symbol: string
  symbolType: string // class, method, function
  parentSymbol: string | null
  startLine: number
  endLine: number
  content: string
  estimatedTokens: number
  // ↓ 追加フィールド
  excluded: boolean                              // 除外フラグ
  summarizeMode: 'original' | 'summarize'        // 要約モード
  summarizedContent?: string                     // 要約済みコンテンツ
  summarizedTokens?: number                      // 要約後の推定トークン数
}
```

※ 重要指定は設計書パートと同様に `pinnedCodePartIds` として別管理するため、`CodePart` 自体にはフィールドを追加しない。

---

## Step 2: フロントエンド — 状態管理の追加

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.6/frontend/src/features/reviewer/hooks/useSplitSettings.ts` | コードパート用の状態管理・トグル関数・要約実行ロジックを追加 |

### 追加する状態・関数

```typescript
// 状態
const [pinnedCodePartIds, setPinnedCodePartIds] = useState<string[]>([])

// 除外トグル（設計書の toggleExcludedDocPart と同じパターン）
const toggleExcludedCodePart = (partId: string) => {
  setPreviewResult(prev => {
    if (!prev?.codeParts) return prev
    return {
      ...prev,
      codeParts: prev.codeParts.map(part =>
        part.id === partId
          ? {
              ...part,
              excluded: !part.excluded,
              // 除外ON時: 要約モードをリセット
              ...(!part.excluded ? { summarizeMode: 'original' as const } : {}),
            }
          : part
      ),
    }
  })
  // 除外ON時: 重要指定からも除外
  setPinnedCodePartIds(prev => prev.filter(id => id !== partId))
}

// 重要指定トグル（設計書の togglePinnedDocPart と同じパターン）
const togglePinnedCodePart = (partId: string) => {
  setPinnedCodePartIds(prev =>
    prev.includes(partId)
      ? prev.filter(id => id !== partId)
      : [...prev, partId]
  )
}

// 要約モードトグル（設計書の toggleSummarizeMode と同じパターン）
const toggleCodeSummarizeMode = (partId: string) => {
  setPreviewResult(prev => {
    if (!prev?.codeParts) return prev
    return {
      ...prev,
      codeParts: prev.codeParts.map(part =>
        part.id === partId
          ? {
              ...part,
              summarizeMode: part.summarizeMode === 'original' ? 'summarize' : 'original',
            }
          : part
      ),
    }
  })
}

// コードパート要約実行（設計書の executeSummarize と同じパターン、targetType: "code"）
const executeCodeSummarize = async (llmConfig?: LlmConfig) => {
  const codeParts = previewResult?.codeParts
  if (!codeParts) return

  const targets = codeParts.filter(
    p => p.summarizeMode === 'summarize' && !p.summarizedContent && !p.excluded
  )

  for (const part of targets) {
    const result = await api.executeSummarize({
      text: part.content,
      targetType: 'code',
      llmConfig,
    })
    if (result.success && result.summarizedText) {
      // previewResult を更新
      setPreviewResult(prev => ({
        ...prev!,
        codeParts: prev!.codeParts!.map(p =>
          p.id === part.id
            ? {
                ...p,
                summarizedContent: result.summarizedText!,
                summarizedTokens: result.summarizedTokens ?? undefined,
              }
            : p
        ),
      }))
    }
  }
}
```

### executePreview() の変更

プレビュー結果受信時に `CodePart` の初期値を設定する:

```typescript
// コードパートの初期化
codeParts: codeResponse.parts.map(part => ({
  ...part,
  excluded: false,
  summarizeMode: 'original' as const,
}))
```

### useSplitSettings の返却値に追加

```typescript
return {
  // ... 既存の返却値
  pinnedCodePartIds,
  toggleExcludedCodePart,
  togglePinnedCodePart,
  toggleCodeSummarizeMode,
  executeCodeSummarize,
}
```

---

## Step 3: フロントエンド — CodePartsTable の拡張

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.6/frontend/src/features/reviewer/components/SplitSettingsSection.tsx` | `CodePartsTable` にチェックボックス列と要約実行ボタンを追加 |

### CodePartsTable の Props 拡張

```typescript
interface CodePartsTableProps {
  parts: CodePart[]
  pinnedCodePartIds: string[]
  onTogglePinnedCodePart: (partId: string) => void
  onToggleCodeSummarizeMode: (partId: string) => void
  onToggleExcludedCodePart: (partId: string) => void
  isSummarizing: boolean
  summarizingPartIds: string[]
  hasPendingSummarize: boolean
  onExecuteCodeSummarize: () => void
  summarizeError: string | null
}
```

### UI 変更

1. テーブルヘッダに「重要」「要約」「除外」の3列を追加
2. 各行にチェックボックスを配置
3. 除外行は `opacity-40` でグレーアウト（設計書と同じ）
4. 除外中は重要・要約チェックボックスを `disabled`
5. テーブル下に「要約対象: N件」と「要約実行」ボタンを配置（設計書の `SummarizeExecuteRow` と同じパターン）

---

## Step 4: フロントエンド — レビュー実行ロジックの修正

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.6/frontend/src/features/reviewer/index.tsx` | コードMAP.jsonフィルタリング、重要コードパート注入、要約コンテンツ使用 |

### 4.1 構造マッチング実行前のフィルタリング

設計書の除外と同様に、コードパートの除外もMAP.jsonフィルタリングで実現する。

```typescript
// 設計書の除外（既存）
const excludedDocPartIds = new Set(
  splitPreviewResult.documentParts?.filter(p => p.excluded).map(p => p.id) ?? []
)

// コードの除外（新規追加）
const excludedCodePartIds = new Set(
  splitPreviewResult.codeParts?.filter(p => p.excluded).map(p => p.id) ?? []
)

// コードMAP.jsonのフィルタリング（新規追加）
const filteredCodeMapJson = splitPreviewResult.codeMapJson
  ? splitPreviewResult.codeMapJson.filter(
      (s) => !excludedCodePartIds.has(s.id as string)
    )
  : null
```

### 4.2 構造マッチング結果の安全フィルタ

```typescript
// 構造マッチング結果から除外済みコードシンボルを除去（新規追加）
matchedGroups = matchedGroups.map(group => ({
  ...group,
  codeSymbols: group.codeSymbols.filter(id => !excludedCodePartIds.has(id)),
}))
```

### 4.3 重要コードパートの全グループ注入

設計書の重要パート注入と同じロジックで、コードの重要パートも全グループに注入する。

```typescript
// 重要コードパートを全グループに注入（新規追加）
if (pinnedCodePartIds.length > 0) {
  const pinnedCodeSymbols = pinnedCodePartIds
    .filter(id => !excludedCodePartIds.has(id))
    .map(id => {
      const part = splitPreviewResult.codeParts?.find(p => p.id === id)
      return part ? id : null
    })
    .filter(Boolean) as string[]

  matchedGroups = matchedGroups.map(group => ({
    ...group,
    codeSymbols: [
      ...group.codeSymbols,
      ...pinnedCodeSymbols.filter(id => !group.codeSymbols.includes(id)),
    ],
  }))
}
```

### 4.4 グループレビュー時の要約コンテンツ使用

コードコンテンツ組み立て時に、要約済みの場合は要約テキストを使用する。

```typescript
// コードコンテンツの組み立て（変更）
const codeContent = group.codeSymbols
  .map(symbolId => {
    const part = splitPreviewResult.codeParts?.find(p => p.id === symbolId)
    if (!part) return ''

    // 要約版を使用する場合
    const usesSummary = part.summarizeMode === 'summarize' && part.summarizedContent
    const content = usesSummary ? part.summarizedContent : part.content
    const summaryMarker = usesSummary ? ' [要約版]' : ''

    return `### ${part.symbol} (${part.symbolType}, L${part.startLine}-L${part.endLine})${summaryMarker}\n\`\`\`\n${content}\n\`\`\``
  })
  .filter(Boolean)
  .join('\n\n')
```

---

## Step 5: フロントエンド — SplitSettingsSection の Props 接続

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.6/frontend/src/features/reviewer/components/SplitSettingsSection.tsx` | `SplitSettingsSection` の Props に新しいコードパート操作を追加 |
| `versions/v0.9.6/frontend/src/features/reviewer/index.tsx` | `SplitSettingsSection` への Props 渡しを追加 |

### SplitSettingsSection の Props 追加

```typescript
interface SplitSettingsSectionProps {
  // ... 既存の Props
  // ↓ 追加
  pinnedCodePartIds: string[]
  onTogglePinnedCodePart: (partId: string) => void
  onToggleCodeSummarizeMode: (partId: string) => void
  onToggleExcludedCodePart: (partId: string) => void
  isCodeSummarizing: boolean
  codeSummarizingPartIds: string[]
  hasCodePendingSummarize: boolean
  codeSummarizeError: string | null
  onExecuteCodeSummarize: () => void
}
```

---

## Step 6: テストの追加

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.6/frontend/src/__tests__/` | コードパートの除外・重要指定・要約のテストを追加 |

### テストケース

#### 除外

| ケース | 内容 |
|---|---|
| 除外チェックボックスの表示 | CodePartsTable に除外チェックボックスが表示される |
| 除外トグル | チェックONで `excluded: true`、行がグレーアウト |
| 除外時の重要・要約無効化 | 除外ONで重要・要約チェックボックスが `disabled` |
| 除外時の自動解除 | 除外ONで重要指定・要約モードが自動解除される |
| MAP.jsonフィルタリング | 除外済みシンボルが構造マッチングに送信されない |

#### 重要指定

| ケース | 内容 |
|---|---|
| 重要チェックボックスの表示 | CodePartsTable に重要チェックボックスが表示される |
| 重要トグル | チェックONで `pinnedCodePartIds` に追加 |
| 全グループ注入 | 重要コードパートが全グループの `codeSymbols` に追加される |
| 重複除外 | 既にグループに含まれるシンボルは重複追加されない |

#### 要約

| ケース | 内容 |
|---|---|
| 要約チェックボックスの表示 | CodePartsTable に要約チェックボックスが表示される |
| 要約モードトグル | チェックONで `summarizeMode: 'summarize'` |
| 要約実行 | `targetType: "code"` で `/api/summarize` が呼ばれる |
| 要約コンテンツ使用 | グループレビュー時に要約テキストが使用される |
| 要約マーカー | 要約版使用時にヘッダに `[要約版]` が表示される |

---

## Step 7: ドキュメント更新

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.6/spec.md` | コードパートの除外・重要指定・要約の仕様を追記 |
| `docs/split-review.md` | コードパートの操作に関する説明を追記 |

### spec.md の更新箇所

| セクション | 更新内容 |
|---|---|
| 分割プレビュー結果 | コードパート一覧テーブルに除外・重要・要約チェックボックスが追加された旨を追記 |
| 分割後の設定 | 重要パート・セクション除外・事前要約の説明にコードパートが含まれることを追記 |

### split-review.md の更新箇所

| セクション | 更新内容 |
|---|---|
| 4. 分割後の設定 | 4.1〜4.3 の説明をコードパートにも適用される旨に更新 |

---

## 修正順序と依存関係

```
Step 0: v0.9.6 作成
  ↓
Step 1: 型定義の拡張（CodePart インターフェース）
  ↓
Step 2: 状態管理の追加（useSplitSettings.ts）
  ↓
Step 3: CodePartsTable の拡張（UI チェックボックス追加）
  ↓
Step 4: レビュー実行ロジックの修正（MAP.jsonフィルタリング、重要パート注入、要約コンテンツ使用）
  ↓
Step 5: Props 接続（SplitSettingsSection ↔ index.tsx）
  ↓
Step 6: テスト追加
  ↓
Step 7: ドキュメント更新
```

---

## 影響範囲

| 対象 | 影響 |
|---|---|
| バックエンド | **変更なし**（`/api/summarize` の `targetType: "code"` は既に対応済み） |
| フロントエンド | `CodePart` 型の拡張、`useSplitSettings` に状態管理追加、`CodePartsTable` にUI追加、`index.tsx` にフィルタリング・注入ロジック追加 |
| ドキュメント | `spec.md` と `split-review.md` にコードパート操作の仕様を追記 |
| code2map | 変更なし |
| md2map | 変更なし |

---

## 関連

- Issue: [#90 分割レビュー: コードパートに除外・重要指定・要約機能を追加](https://github.com/elvezjp/spec-code-ai-reviewer/issues/90)
- 設計書の除外機能: [20260324-pre-split-exclusion-plan.md](20260324-pre-split-exclusion-plan.md)
- 設計書の重要指定機能: [20260318-pre-split-importance-plan.md](20260318-pre-split-importance-plan.md)
- 分割レビュー詳細: [split-review.md](split-review.md)

---

## 完了チェックリスト

### Step 0: v0.9.6 作成

- [x] `versions/v0.9.5` を `versions/v0.9.6` にコピー
- [x] v0.9.6 の全バージョン番号を更新
- [x] インフラ設定（Docker/Nginx/PM2）に v0.9.6 を追加
- [x] `latest` シンボリックリンクを v0.9.6 に更新
- [x] 全バージョンの `useVersions.ts` に v0.9.6 を追加

### Step 1: 型定義の拡張

- [x] `CodePart` に `excluded`, `summarizeMode`, `summarizedContent`, `summarizedTokens` を追加

### Step 2: 状態管理の追加

- [x] `pinnedCodePartIds` state の追加
- [x] `toggleExcludedCodePart()` の実装（除外ON時: 重要・要約を自動解除）
- [x] `togglePinnedCodePart()` の実装
- [x] `toggleCodeSummarizeMode()` の実装
- [x] `executeCodeSummarize()` の実装（`targetType: "code"`）
- [x] `executePreview()` で `CodePart` の初期値設定（`excluded: false`, `summarizeMode: 'original'`）

### Step 3: CodePartsTable の拡張

- [x] 「重要」「要約」「除外」チェックボックス列の追加
- [x] 除外行のグレーアウト表示（`opacity-40`）
- [x] 除外中の重要・要約チェックボックス無効化
- [x] 要約実行ボタンの追加

### Step 4: レビュー実行ロジックの修正

- [x] コードMAP.jsonの除外フィルタリング
- [x] 構造マッチング結果からの除外済みシンボル除去
- [x] 重要コードパートの全グループ注入
- [x] グループレビュー時の要約コンテンツ使用

### Step 5: Props 接続

- [x] `SplitSettingsSection` の Props 追加
- [x] `index.tsx` から Props を渡す

### Step 6: テスト追加

- [x] 既存テストにコードパート新Props・新フィールドを追加
- [x] 全フロントエンドテスト通過（205件）

### Step 7: ドキュメント更新

- [x] `versions/v0.9.6/spec.md` にコードパート操作の仕様を追記
- [x] `docs/split-review.md` にコードパート操作の説明を追記

### 最終確認

- [x] 全バックエンドテスト通過（190件）
- [x] 全フロントエンドテスト通過（205件）
- [ ] 手動動作確認（コードパートの除外 → 構造マッチング → 除外シンボルがグループに含まれないことの確認）

---

## 追加修正計画（コードレビュー指摘事項）

v0.9.6 の実装完了後のコードレビューで、設計書パートとコードパートの処理を比較した結果、以下の不足・不整合が判明した。

### 問題一覧

| # | 分類 | 概要 | 重要度 |
|---|---|---|---|
| 1 | コードパート不足 | `hasCodePendingSummarize` 時の警告メッセージが未実装 | 中 |
| 2 | コードパート不足 | CodePartsTable にコード内容プレビュー（`PartContentPreview`）がない | 低 |
| 3 | コードパート不足 | CodePartsTable に要約結果プレビュー（`SummarizedTextPreview`）がない | 低 |
| 4 | コードパート不足 | コードパーツテーブルに「重要/要約/除外」の説明テキストがない | 低 |
| 5 | フィルタリング不整合 | `executeSummarize`（設計書）に `!p.excluded` 防御フィルタがない | 低 |
| 6 | フィルタリング不整合 | `hasPendingSummarize`（設計書）に `!p.excluded` 防御フィルタがない | 低 |
| 7 | 両者共通バグ | `clearPreview` で `summarizeError` / `codeSummarizeError` がクリアされない | 中 |
| 8 | 両者共通バグ | `estimatedReviewCount` が除外パートを考慮していない | 低 |

---

### 問題 1: `hasCodePendingSummarize` 時の警告メッセージが未実装

**対象ファイル:** `versions/v0.9.6/frontend/src/features/reviewer/index.tsx`

**現状:** レビューボタンは `hasCodePendingSummarize` で正しく disabled されるが、設計書パートにある「⚠ 要約が選択されていますが未実行です」に相当するメッセージがコードパート側にない。ユーザーにはレビューボタンが押せない理由が分からない。

**修正内容:** `hasPendingSummarize` の警告メッセージの直後に、`hasCodePendingSummarize` 用の同等メッセージを追加する。

```tsx
{isSplitEnabled && hasCodePendingSummarize && (
  <p className="text-xs text-orange-500 mt-1 text-center">
    ⚠ コードパートの要約が選択されていますが未実行です。「選択した要約を実行」をクリックしてから、レビューを実行してください。
  </p>
)}
```

---

### 問題 2: CodePartsTable にコード内容プレビューがない

**対象ファイル:** `versions/v0.9.6/frontend/src/features/reviewer/components/SplitSettingsSection.tsx`

**現状:** 設計書パートの `DocumentPartsTable` には各セクションの内容を展開表示できる `PartContentPreview` コンポーネントがあるが、`CodePartsTable` にはない。

**修正内容:** `CodePartsTable` のシンボル名セルに `PartContentPreview` を追加する。既存の `PartContentPreview` コンポーネントはそのまま再利用可能。

```tsx
<TableCell>
  {part.parentSymbol ? `${part.parentSymbol}#${part.symbol}` : part.symbol}
  <PartContentPreview content={part.content} />  {/* 追加 */}
</TableCell>
```

---

### 問題 3: CodePartsTable に要約結果プレビューがない

**対象ファイル:** `versions/v0.9.6/frontend/src/features/reviewer/components/SplitSettingsSection.tsx`

**現状:** 設計書パートには要約完了後に `SummarizedTextPreview` で要約結果を確認できるが、コードパートには要約結果を確認する手段がない。

**修正内容:** `CodePartsTable` のシンボル名セルに `SummarizedTextPreview` を追加する。

```tsx
<TableCell>
  {part.parentSymbol ? `${part.parentSymbol}#${part.symbol}` : part.symbol}
  <PartContentPreview content={part.content} />
  {/* 追加 ↓ */}
  {part.summarizedContent && part.summarizeMode === 'summarize' && (
    <SummarizedTextPreview text={part.summarizedContent} />
  )}
</TableCell>
```

---

### 問題 4: コードパーツテーブルに説明テキストがない

**対象ファイル:** `versions/v0.9.6/frontend/src/features/reviewer/components/SplitSettingsSection.tsx`

**現状:** 設計書パーツセクションにはチェックボックスの使い方を説明するリスト（重要/要約/除外の意味）があるが、コードパーツセクションにはない。

**修正内容:** コードパーツの `<h4>` タグと `<CodePartsTable>` の間に説明テキストを追加する。

```tsx
<ul className="text-xs text-gray-500 mb-2 list-disc list-inside space-y-0.5">
  <li><strong>重要</strong>: 分割レビュー時に全てのグループで参照されます。</li>
  <li><strong>要約</strong>: レビュー時に要約テキストで代替されます。トークン数が大きいシンボルに使用してください。</li>
  <li><strong>除外</strong>: 構造マッチング・グループレビューの対象から外します。メソッドが個別に存在するクラス全体シンボルの除外に有効です。</li>
</ul>
```

---

### 問題 5: `executeSummarize`（設計書）に `!p.excluded` 防御フィルタがない

**対象ファイル:** `versions/v0.9.6/frontend/src/features/reviewer/hooks/useSplitSettings.ts`

**現状:** コードパートの `executeCodeSummarize` は `!p.excluded` でフィルタしているが、設計書パートの `executeSummarize` にはこのフィルタがない。`toggleExcludedDocPart` が `summarizeMode` を `'original'` にリセットするため実害は薄いが、防御的コーディングとして不統一。

**修正内容:** `executeSummarize` のターゲットフィルタに `!p.excluded` を追加する。

```typescript
// 修正前
const targets = previewResult.documentParts.filter(
  (p) => p.summarizeMode === 'summarize' && !p.summarizedContent
)

// 修正後
const targets = previewResult.documentParts.filter(
  (p) => p.summarizeMode === 'summarize' && !p.summarizedContent && !p.excluded
)
```

---

### 問題 6: `hasPendingSummarize`（設計書）に `!p.excluded` 防御フィルタがない

**対象ファイル:** `versions/v0.9.6/frontend/src/features/reviewer/hooks/useSplitSettings.ts`

**現状:** 問題 5 と同じ理由で、`hasPendingSummarize` にも `!p.excluded` フィルタがない。

**修正内容:**

```typescript
// 修正前
const hasPendingSummarize = useMemo(() => {
  if (!previewResult?.documentParts) return false
  return previewResult.documentParts.some(
    (p) => p.summarizeMode === 'summarize' && !p.summarizedContent
  )
}, [previewResult])

// 修正後
const hasPendingSummarize = useMemo(() => {
  if (!previewResult?.documentParts) return false
  return previewResult.documentParts.some(
    (p) => p.summarizeMode === 'summarize' && !p.summarizedContent && !p.excluded
  )
}, [previewResult])
```

---

### 問題 7: `clearPreview` で要約エラー状態がクリアされない

**対象ファイル:** `versions/v0.9.6/frontend/src/features/reviewer/hooks/useSplitSettings.ts`

**現状:** `clearPreview` は `setError(null)` でプレビューエラーをクリアするが、`summarizeError` と `codeSummarizeError` はクリアしない。プレビュー再実行後に前回の要約エラーメッセージが画面に残る可能性がある。

**修正内容:**

```typescript
const clearPreview = useCallback(() => {
  setPreviewResult(null)
  setPinnedDocPartIds([])
  setPinnedCodePartIds([])
  setError(null)
  setSummarizeError(null)        // 追加
  setCodeSummarizeError(null)    // 追加
}, [])
```

---

### 問題 8: `estimatedReviewCount` が除外パートを考慮していない

**対象ファイル:** `versions/v0.9.6/frontend/src/features/reviewer/hooks/useSplitSettings.ts`

**現状:** レビュー回数の推定で `documentParts?.length` と `codeParts?.length` をそのまま使用しており、除外パートも含めてカウントされるため推定値が過大になる。

**修正内容:**

```typescript
// 修正前
const docCount = previewResult.documentParts?.length || 0
const codeCount = previewResult.codeParts?.length || 0

// 修正後
const docCount = previewResult.documentParts?.filter(p => !p.excluded).length || 0
const codeCount = previewResult.codeParts?.filter(p => !p.excluded).length || 0
```

---

### ドキュメント更新（追加修正に伴う）

問題 1〜4 の修正に伴い、以下のドキュメントも更新が必要。

#### `versions/v0.9.6/spec.md` の更新

**2.7.5 分割プレビュー — コードパーツテーブル（問題 2, 3 対応）:**

コードパーツテーブルの説明にコンテンツプレビュー・要約結果プレビュー機能を追記する。

```markdown
// 修正前（推定トークン行の後）
コードパートの除外・重要指定・要約は設計書パートと同じ操作性で提供される。

// 修正後
各コードシンボルは「内容を表示」で展開表示でき、要約実行後は「要約結果を表示」で要約内容を確認できる。
コードパートの除外・重要指定・要約は設計書パートと同じ操作性で提供される。
```

**2.7.7 事前要約機能（問題 1 対応）:**

事前要約機能の説明がほぼ設計書パートのみの記述になっているため、コードパートにも適用される旨を追記する。

```markdown
// 修正前
分割プレビューで設計書パートを事前に要約し、グループレビュー時のトークン消費を削減する機能。

// 修正後
分割プレビューで設計書パートおよびコードパートを事前に要約し、グループレビュー時のトークン消費を削減する機能。
```

```markdown
// 修正前（要約フロー 1行目）
1. 分割プレビューの設計書パーツテーブルで、各パートの「要約」チェックボックスを選択

// 修正後
1. 分割プレビューの設計書パーツテーブルまたはコードパーツテーブルで、各パートの「要約」チェックボックスを選択
```

```markdown
// 修正前（レビュー実行時の動作）
- 「要約」選択かつ未実行のパートがある場合、レビュー実行ボタンは disabled

// 修正後
- 設計書またはコードで「要約」選択かつ未実行のパートがある場合、レビュー実行ボタンは disabled となり、該当する警告メッセージが表示される
```

```markdown
// 修正前（要約API）
- 要約は `/api/summarize` エンドポイントを使用（`targetType: "design"`）

// 修正後
- 設計書の要約は `/api/summarize` エンドポイントを使用（`targetType: "design"`）
- コードの要約は同エンドポイントを使用（`targetType: "code"`）
```

**2.7.6 セクション除外機能（問題 2 対応）:**

除外フローの確認手段にコードパートの記述を追記する。

```markdown
// 修正前（除外フロー 1行目）
1. 分割プレビューの設計書パーツテーブルで、各パートの「内容を表示」で内容を確認する

// 修正後
1. 分割プレビューの設計書パーツテーブルまたはコードパーツテーブルで、各パートの「内容を表示」で内容を確認する
```

#### `docs/split-review.md` の更新

**4.2 セクション除外（問題 2 対応）:**

コードパートでもコンテンツプレビューが利用できる旨を補足する（現状は設計書側の除外フローでのみ言及あり、変更後は両方で「内容を表示」が利用可能になるため）。

**4.3 事前要約（問題 1 対応）:**

レビュー実行ボタンのdisabled条件に警告メッセージの表示を追記する。

```markdown
// 追記
- 設計書またはコードで「要約」選択かつ未実行のパートがある場合、レビュー実行ボタンは disabled となり、該当する警告メッセージが表示される
```

---

### 追加修正の完了チェックリスト

- [x] 問題 1: `hasCodePendingSummarize` 警告メッセージの追加
- [x] 問題 2: CodePartsTable に `PartContentPreview` を追加
- [x] 問題 3: CodePartsTable に `SummarizedTextPreview` を追加
- [x] 問題 4: コードパーツテーブルに説明テキストを追加
- [x] 問題 5: `executeSummarize` に `!p.excluded` フィルタを追加
- [x] 問題 6: `hasPendingSummarize` に `!p.excluded` フィルタを追加
- [x] 問題 7: `clearPreview` に要約エラー状態のクリアを追加
- [x] 問題 8: `estimatedReviewCount` で除外パートを除外
- [x] `versions/v0.9.6/spec.md` のドキュメント更新（2.7.5, 2.7.6, 2.7.7）
- [x] `docs/split-review.md` のドキュメント更新（4.2, 4.3）
- [x] 全フロントエンドテスト通過（205件）

---

## 追加機能: 結果統合リトライのグループスキップ機能

対応 Issue: [#93](https://github.com/elvezjp/spec-code-ai-reviewer/issues/93)

### 背景

結果統合（フェーズ3）でトークン上限エラーが発生した場合、現状ではトークン数が上限を下回るまで多くのグループレビュー結果を「要約」する必要がある。グループ数が多い場合は要約の実行回数が増え、時間的・コスト的な負担が大きい。

最終レポートに含める必要がないグループ（重要度の低いグループ、問題なしと判明しているグループ等）をスキップできれば、要約の実行回数を減らしつつトークン消費を効率的に削減できる。

### 現状

リトライ設定パネルでは各グループに対して以下の2択のみ:
- **そのまま**: 原文のレビュー結果を統合に使用
- **要約**: 要約版のレビュー結果を統合に使用

### 変更後

3つ目の選択肢を追加:
- **スキップ**: そのグループのレビュー結果を統合対象から除外する

```
コーディング規約の適用と命名規則
  ○ そのまま（~3,348 トークン）  ◉ 要約（~1,693 トークン 49%削減）  ○ スキップ
  > 要約結果を表示

コーディングスタイルの実装                                          ← グレーアウト表示
  ○ そのまま（~3,769 トークン）  ○ 要約（未実行）  ◉ スキップ
```

### 制約

- 全グループをスキップにすることはできない（最低1グループは統合対象に残す必要がある）
- スキップされたグループは最終レポートに含まれない旨をユーザーに明示する

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.6/frontend/src/features/reviewer/types/index.ts` | `IntegrateGroupSummarizeEntry.mode` の型に `'skip'` を追加 |
| `versions/v0.9.6/frontend/src/features/reviewer/components/IntegrateRetrySettingsPanel.tsx` | 「スキップ」ラジオボタン追加、スキップ行のグレーアウト表示、全スキップ防止 |
| `versions/v0.9.6/frontend/src/features/reviewer/index.tsx` | `handleRetryIntegrate` でスキップされたグループを統合APIリクエストから除外 |
| `versions/v0.9.6/spec.md` | 結果統合リトライのスキップ機能についての仕様を追記 |
| `docs/split-review.md` | 結果統合エラー時のスキップ機能についての説明を追記 |

### 修正詳細

#### 1. 型定義の拡張（types/index.ts）

```typescript
export interface IntegrateGroupSummarizeEntry {
  groupId: string
  mode: 'original' | 'summarize' | 'skip'  // ← 'skip' 追加
  summarizedReport?: string
  originalTokens?: number
  summarizedTokens?: number
}
```

#### 2. IntegrateRetrySettingsPanel.tsx

- `groupModes` の型を `Record<string, 'original' | 'summarize' | 'skip'>` に変更
- `handleModeChange` の引数型に `'skip'` を追加
- 各グループの行に3つ目のラジオボタン「スキップ」を追加
- `computeHasPending`: スキップのグループは要約未実行判定の対象外（変更不要、`'summarize'` のみチェック）
- スキップ行をグレーアウト表示（`opacity-40`）
- 全グループスキップ防止: 統合対象が0件の場合はリトライボタンを disabled にし、警告メッセージを表示
- `onModeChange` の通知: スキップは要約不要なので `hasPending` には影響しない（ただし全スキップの場合はリトライ不可にする必要あり）

#### 3. handleRetryIntegrate（index.tsx）

```typescript
// 修正後: skip のグループを除外
const groupReviewSummaries = groupReviews
  .filter((g) => g.status === 'completed' && g.result)
  .filter((g) => {
    const entry = integrateSummarizeState.groups.find((s) => s.groupId === g.groupId)
    return entry?.mode !== 'skip'
  })
  .map((g) => { ... })
```

### 確認事項（追加実装不要）

- **要約結果の保持**: 要約→スキップ→要約に戻しても再要約は不要。要約結果は `summarizeState.groups` に `summarizedReport` として保持されており、`handleModeChange` は `groupModes`（UIの選択状態）のみを変更するため、既存の要約結果はそのまま使われる
- **ZIP ダウンロードへの影響**: スキップしたグループのレビュー結果もZIPには含まれる。ZIP に含めるグループは `splitReviewState.groupReviews` の `status === 'completed'` でフィルタしており、`integrateSummarizeState` の `mode` とは独立しているため、スキップの影響を受けない

### 完了チェックリスト

- [x] 型定義に `'skip'` を追加
- [x] IntegrateRetrySettingsPanel に「スキップ」ラジオボタンを追加
- [x] スキップ行のグレーアウト表示
- [x] 全グループスキップ防止（リトライボタン disabled + 警告メッセージ）
- [x] handleRetryIntegrate でスキップグループを統合対象から除外
- [x] 全フロントエンドテスト通過（205件）
- [x] `versions/v0.9.6/spec.md` のドキュメント更新
- [x] `docs/split-review.md` のドキュメント更新
