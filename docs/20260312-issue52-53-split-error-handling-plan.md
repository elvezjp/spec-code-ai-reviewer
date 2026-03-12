# 修正計画書: issue #52・#53 分割プレビューのエラーハンドリング改善

## 概要

| # | タイトル | 種別 |
|---|---------|------|
| [#52](https://github.com/elvezjp/20260219spec-code-ai-reviewer/issues/52) | 分割プレビュー: コード分割が失敗しても原因が特定できない | bug |
| [#53](https://github.com/elvezjp/20260219spec-code-ai-reviewer/issues/53) | 分割レビュー: コード分割失敗時にレビューが実行できてしまう | bug |

対象バージョン: `versions/v0.9.1`

---

## 現状の問題整理

### 分割プレビューエラーがトーストで消えてしまう（issue #52 の前提問題）

`useSplitSettings.ts` の `executePreview` が throw した場合、エラーは `splitPreviewError` ステートに保持される。
`index.tsx` の `useEffect` がこれを検知して `showToast()` に渡したうえで即座に `clearSplitPreviewError()` を呼ぶため、エラーはトースト（3秒で消える）としてのみ表示される。

ユーザーがエラー内容を確認する前に消えてしまうため、エラーの原因が追えない。

### issue #52: エラー原因が伝わらない

`code2map` の `JavaParser.parse()` は `(symbols, warnings)` を返す（tree-sitterベース新実装）。

`split.py` の `split_code` エンドポイントは：
- `warnings` を受け取っているが、`SplitCodeResponse` に含めていない
- `symbols` が空の場合も `success=True` で `parts=[]` を返すだけで警告なし

フロントエンド（`useSplitSettings.ts`）は：
- `response.success` が `true` かつ `parts` が空でも `codeParts = null` のままサイレントに続行
- `SplitSettingsSection.tsx` は `codeParts` が空の場合、何も表示しない

### issue #53: 失敗時もレビュー実行できてしまう

フロントエンド（`SplitSettingsSection.tsx` の呼び出し元）は：
- `codeParts` が空でもレビュー実行ボタンを無効化しない

バックエンド（`review.py` の `structure_matching` エンドポイント）は：
- `code_symbols` が空のままLLMを呼び出してしまう
- マッチングエラー後の導線が不十分

---

## 修正方針

### フェーズ0: 分割プレビューエラーの表示改善（issue #52 の前提対応）

#### 0-1. `index.tsx` のトースト変換を廃止し、`SplitSettingsSection` に直接渡す

**対象ファイル:** `versions/v0.9.1/frontend/src/features/reviewer/index.tsx`

`splitPreviewError` をトーストに流していた `useEffect` を削除し、
`SplitSettingsSection` の prop として直接渡す。

```typescript
// 削除:
useEffect(() => {
  if (!splitPreviewError) return
  showToast(splitPreviewError)
  clearSplitPreviewError()
}, [splitPreviewError, showToast, clearSplitPreviewError])

// SplitSettingsSection に追加:
previewError={splitPreviewError}
```

また、使用されなくなった `clearError: clearSplitPreviewError` の分割代入も削除する。

#### 0-2. `SplitSettingsSection.tsx` に `previewError` prop を追加し、ボタン直下に表示

**対象ファイル:** `versions/v0.9.1/frontend/src/features/reviewer/components/SplitSettingsSection.tsx`

`previewError?: string | null` prop を追加し、分割プレビューボタン直下に表示する。
エラーは次回プレビュー実行時または設定変更時（`useSplitSettings` 内で `setError(null)` が呼ばれるタイミング）に自動クリアされる。

```tsx
{/* プレビューエラー */}
{previewError && (
  <p className="text-sm text-red-600">{previewError}</p>
)}
```

---

### フェーズ1: バックエンド修正

#### 1-1. `SplitCodeResponse` スキーマに `warnings` フィールドを追加

**対象ファイル:** `versions/v0.9.1/backend/app/models/schemas.py`

```python
class SplitCodeResponse(BaseModel):
    success: bool
    parts: list[CodePart] = []
    indexContent: str | None = None
    mapJson: list[dict] | None = None
    language: str | None = None
    warnings: list[str] = []   # ← 追加
    error: str | None = None
```

#### 1-2. `split_code` エンドポイントで `warnings` をレスポンスに含める

**対象ファイル:** `versions/v0.9.1/backend/app/routers/split.py`

変更箇所（現在 L234〜L240、L288〜L294 付近）：

- シンボルが空の場合: `warnings` をそのままレスポンスに含める
- 正常時: パース結果の `warnings` をレスポンスに含める

```python
# symbols が空の場合
if not symbols:
    return SplitCodeResponse(
        success=True,
        parts=[],
        indexContent="# No symbols found\n",
        language=language,
        warnings=warnings,   # ← 追加
    )

# 正常時
return SplitCodeResponse(
    success=True,
    parts=parts,
    indexContent=index_content,
    mapJson=map_json,
    language=language,
    warnings=warnings,   # ← 追加
)
```

#### 1-3. `structure_matching` エンドポイントで `code_symbols` 空チェックを追加

**対象ファイル:** `versions/v0.9.1/backend/app/routers/review.py`

`structure_matching` 関数の先頭（LLM呼び出し前）に追加:

```python
# code_symbols が空の場合は400エラーを返す
all_code_symbols = []
for cf in request.codeFiles:
    all_code_symbols.extend(cf.mapJson.get("symbols", []))

if not all_code_symbols:
    return StructureMatchingResponse(
        success=False,
        error="コードシンボルが空です。コードの分割に失敗している可能性があります。分割設定を確認してください。",
    )
```

---

### フェーズ2: フロントエンド修正

#### 2-1. `SplitCodeResponse` 型に `warnings` フィールドを追加

**対象ファイル:** `versions/v0.9.1/frontend/src/features/reviewer/types/index.ts`

```typescript
export interface SplitCodeResponse {
  success: boolean
  parts: CodePart[]
  indexContent?: string
  mapJson?: Record<string, unknown>[]
  language?: string
  warnings?: string[]   // ← 追加
  error?: string
}
```

#### 2-2. `SplitPreviewResult` 型に `codeWarnings` フィールドを追加

**対象ファイル:** `versions/v0.9.1/frontend/src/features/reviewer/types/index.ts`

```typescript
export interface SplitPreviewResult {
  // ...既存フィールド...
  codeWarnings: string[]   // ← 追加: コード分割の警告メッセージ
}
```

#### 2-3. `useSplitSettings.ts` で warnings を収集・保持する

**対象ファイル:** `versions/v0.9.1/frontend/src/features/reviewer/hooks/useSplitSettings.ts`

コード分割ループ内で `warnings` を収集し、`setPreviewResult` 時に `codeWarnings` として設定する。

```typescript
// 変更前（L213〜L215付近）:
} else {
  console.warn(`Failed to split ${codeFile.filename}: ${response.error}`)
}

// 変更後:
} else {
  // warnings があれば収集（パース部分成功・シンボル空のケース）
  if (response.warnings && response.warnings.length > 0) {
    allCodeWarnings.push(...response.warnings.map(w => `${codeFile.filename}: ${w}`))
  }
  if (response.error) {
    allCodeWarnings.push(`${codeFile.filename}: ${response.error}`)
  }
}
```

`setPreviewResult` 呼び出し時:
```typescript
setPreviewResult({
  // ...既存フィールド...
  codeWarnings: allCodeWarnings,   // ← 追加
})
```

#### 2-4. `SplitSettingsSection.tsx` でコード分割警告・エラーを表示する

**対象ファイル:** `versions/v0.9.1/frontend/src/features/reviewer/components/SplitSettingsSection.tsx`

プレビュー結果表示エリアに以下を追加：

- `codeParts` が空 かつ `codeWarnings` が存在する場合: 警告メッセージをリスト表示
- `codeParts` が空 かつ `codeWarnings` が空の場合: 「コードシンボルが検出されませんでした」と表示

```tsx
{/* コードパーツが空の場合の警告表示 */}
{previewResult && (!previewResult.codeParts || previewResult.codeParts.length === 0) && (
  <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded">
    <p className="text-sm font-medium text-amber-800">
      コードの分割結果が0件です
    </p>
    {previewResult.codeWarnings && previewResult.codeWarnings.length > 0 ? (
      <ul className="mt-1 text-xs text-amber-700 list-disc list-inside space-y-0.5">
        {previewResult.codeWarnings.map((w, i) => (
          <li key={i}>{w}</li>
        ))}
      </ul>
    ) : (
      <p className="mt-1 text-xs text-amber-700">
        コードシンボルが検出されませんでした。対応言語（Python / Java）のファイルか確認してください。
      </p>
    )}
  </div>
)}
```

#### 2-5. レビュー実行ボタンを `codeParts` が空の場合に無効化する

**対象ファイル:** `versions/v0.9.1/frontend/src/features/reviewer/components/SplitSettingsSection.tsx` または呼び出し元

`codeParts` が空の場合にレビュー実行ボタンを disabled にする条件を追加する。
（呼び出し元で `canStartReview` フラグを制御する実装が望ましい）

```typescript
// 呼び出し元コンポーネントにて
const canStartSplitReview = !!(
  previewResult?.documentParts?.length &&
  previewResult?.codeParts?.length   // ← codeParts が空なら無効化
)
```

#### 2-6. `SplitExecutingScreen.tsx` でマッチングエラー時に設定画面への戻り導線を追加

**対象ファイル:** `versions/v0.9.1/frontend/src/features/reviewer/components/SplitExecutingScreen.tsx`

構造マッチングエラー表示部分（現在L185〜L200付近）に「設定に戻る」ボタンを追加：

```tsx
{isStructureMatchingError && (
  <>
    <p className="text-sm text-red-600 mt-2">
      構造マッチングでエラーが発生しました。
    </p>
    {state.error && (
      <p className="text-xs text-red-500 mt-1">{state.error}</p>
    )}
    <div className="flex items-center justify-center gap-3 mt-3">
      <button onClick={onRetryStructureMatching} ...>
        リトライ
      </button>
      <button onClick={onBack} ...>   {/* ← 追加 */}
        ← 設定に戻る
      </button>
    </div>
  </>
)}
```

---

## 修正ファイル一覧

| ファイル | 変更内容 |
|---------|---------|
| `versions/v0.9.1/frontend/src/features/reviewer/index.tsx` | `splitPreviewError` のトースト変換 `useEffect` を削除、`previewError` prop として渡す |
| `versions/v0.9.1/frontend/src/features/reviewer/components/SplitSettingsSection.tsx` | `previewError` prop 追加、ボタン直下にエラー表示 |
| `versions/v0.9.1/backend/app/models/schemas.py` | `SplitCodeResponse` に `warnings` フィールド追加 |
| `versions/v0.9.1/backend/app/routers/split.py` | `split_code` で `warnings` をレスポンスに含める |
| `versions/v0.9.1/backend/app/routers/review.py` | `structure_matching` で `code_symbols` 空チェック追加 |
| `versions/v0.9.1/frontend/src/features/reviewer/types/index.ts` | `SplitCodeResponse`, `SplitPreviewResult` 型に `warnings`, `codeWarnings` 追加 |
| `versions/v0.9.1/frontend/src/features/reviewer/hooks/useSplitSettings.ts` | `warnings` 収集・`codeWarnings` 保持 |
| `versions/v0.9.1/frontend/src/features/reviewer/components/SplitSettingsSection.tsx` | コード分割警告表示、レビュー実行ボタン無効化条件追加 |
| `versions/v0.9.1/frontend/src/features/reviewer/components/SplitExecutingScreen.tsx` | マッチングエラー時の「設定に戻る」ボタン追加 |

---

## 実装順序

1. フロントエンドエラー表示改善（`index.tsx`, `SplitSettingsSection.tsx`）
2. バックエンドスキーマ変更（`schemas.py`）
3. バックエンドAPIロジック変更（`split.py`, `review.py`）
4. フロントエンド型定義変更（`types/index.ts`）
5. フロントエンドフック変更（`useSplitSettings.ts`）
6. フロントエンドUI変更（`SplitSettingsSection.tsx`, `SplitExecutingScreen.tsx`）

---

## 検証方針

- 分割プレビューが失敗した場合、ボタン直下にエラーメッセージが常時表示されること（トーストで消えないこと）
- 次回プレビュー実行時または設定変更時にエラーメッセージがクリアされること
- Javaファイルで構文エラーがあるケース → 分割プレビューに警告が表示されること
- Shift-JIS等のエンコーディング問題があるケース → 警告が表示されること
- `codeParts` が0件の状態でレビュー実行ボタンが無効化されていること
- 構造マッチングAPIに空のコードシンボルを送った場合、400エラーが返ること
- 構造マッチングエラー画面から「設定に戻る」で分割設定画面に戻れること
