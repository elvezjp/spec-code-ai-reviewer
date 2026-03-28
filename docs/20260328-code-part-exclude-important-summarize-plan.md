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

- [ ] `versions/v0.9.5` を `versions/v0.9.6` にコピー
- [ ] v0.9.6 の全バージョン番号を更新
- [ ] インフラ設定（Docker/Nginx/PM2）に v0.9.6 を追加
- [ ] `latest` シンボリックリンクを v0.9.6 に更新
- [ ] 全バージョンの `useVersions.ts` に v0.9.6 を追加

### Step 1: 型定義の拡張

- [ ] `CodePart` に `excluded`, `summarizeMode`, `summarizedContent`, `summarizedTokens` を追加

### Step 2: 状態管理の追加

- [ ] `pinnedCodePartIds` state の追加
- [ ] `toggleExcludedCodePart()` の実装（除外ON時: 重要・要約を自動解除）
- [ ] `togglePinnedCodePart()` の実装
- [ ] `toggleCodeSummarizeMode()` の実装
- [ ] `executeCodeSummarize()` の実装（`targetType: "code"`）
- [ ] `executePreview()` で `CodePart` の初期値設定（`excluded: false`, `summarizeMode: 'original'`）

### Step 3: CodePartsTable の拡張

- [ ] 「重要」「要約」「除外」チェックボックス列の追加
- [ ] 除外行のグレーアウト表示（`opacity-40`）
- [ ] 除外中の重要・要約チェックボックス無効化
- [ ] 要約実行ボタンの追加

### Step 4: レビュー実行ロジックの修正

- [ ] コードMAP.jsonの除外フィルタリング
- [ ] 構造マッチング結果からの除外済みシンボル除去
- [ ] 重要コードパートの全グループ注入
- [ ] グループレビュー時の要約コンテンツ使用

### Step 5: Props 接続

- [ ] `SplitSettingsSection` の Props 追加
- [ ] `index.tsx` から Props を渡す

### Step 6: テスト追加

- [ ] 除外関連テスト
- [ ] 重要指定関連テスト
- [ ] 要約関連テスト
- [ ] 全フロントエンドテスト通過

### Step 7: ドキュメント更新

- [ ] `versions/v0.9.6/spec.md` にコードパート操作の仕様を追記
- [ ] `docs/split-review.md` にコードパート操作の説明を追記

### 最終確認

- [ ] 全バックエンドテスト通過
- [ ] 全フロントエンドテスト通過
- [ ] 手動動作確認（コードパートの除外 → 構造マッチング → 除外シンボルがグループに含まれないことの確認）
