# 修正計画書: 分割プレビューのサイレントフォールバック・分割モード不整合

## 概要

分割プレビューに関する2つの問題を修正する。

1. **サイレントフォールバック問題**: AIモードまたはAIサマリー選択時、LLM認証情報が不正でもエラー表示なく `success: true` で結果が返る
2. **分割モード送信元の不整合**: 事前重要指定なし時にUIの分割モード選択がリクエストに反映されない

対応 Issue:
- [#84 AIモード分割プレビューでLLM認証情報が不正な場合にエラーなく結果が返る](https://github.com/elvezjp/spec-code-ai-reviewer/issues/84)
- [#86 分割プレビューで事前重要指定なし時にUIの分割モード選択が反映されない](https://github.com/elvezjp/spec-code-ai-reviewer/issues/86)

## 背景

### LLM設定の優先順位（仕様通り・変更なし）

1. UI画面で設定ファイルから指定された認証情報+モデルIDを使用
2. 上記がなければシステムLLM設定（環境変数）を使用

このフォールバック自体は正しい動作である。

### 問題1: フロントエンドが `llmConfig` を渡す条件が不十分

`useSplitSettings.ts` で `llmConfig` を渡す条件が **通常セクションの `splitMode === 'ai'`** のみになっている:

```typescript
// 現在のコード（問題あり）
llmConfig: (hasPreImportant ? normalSplitSettings.splitMode === 'ai' : settings.documentSplitMode === 'ai')
  ? (llmConfig ?? undefined) : undefined,
```

以下のケースでUIのLLM設定が送信されず、バックエンドがシステム環境変数にフォールバックしてしまう:

| 通常splitMode | 事前重要splitMode | summaryMode | llmConfig送信 | 問題 |
|---|---|---|---|---|
| ai | any | any | 送信される | なし |
| heading | heading | **ai** | **送信されない** | UIのLLM設定が使われない |
| heading | **ai** | any | **送信されない** | 同上 |

md2map は `llm_config` を渡しても実際にAIが必要になるまでプロバイダーを初期化しない（遅延初期化）ため、**常に渡しても問題ない**。

### 問題2: 分割モード送信元の不整合（#86）

`useSplitSettings.ts` の `executePreview` でリクエストを構築する際、`splitMode` の取得元が `hasPreImportant` の有無で分岐している:

```typescript
// useSplitSettings.ts:310-311
splitMode: hasPreImportant ? normalSplitSettings.splitMode : settings.documentSplitMode,
```

- `hasPreImportant = true` → `normalSplitSettings.splitMode`（UIの選択が反映される）
- `hasPreImportant = false` → `settings.documentSplitMode`（デフォルト `'ai'` のまま）

一方、`summaryMode` / `maxSubsections` / `summaryMaxChars` は常に `normalSplitSettings` から取得されており、`splitMode` だけが不整合になっている:

```typescript
// こちらは常に normalSplitSettings（hasPreImportant 非依存）
summaryMode: normalSplitSettings.summaryMode,
summaryMaxChars: normalSplitSettings.summaryMaxChars,
maxSubsections: normalSplitSettings.maxSubsections,
```

この結果、ユーザーがUIでNLPや見出しモードを選択しても、事前重要指定なし時は常にAIモードがバックエンドに送信される。同様に `maxDepth` と `aiPromptExtraNotes` にも同じ不整合がある。

### 問題3: md2map がAIフォールバック時に警告を返さない（別途修正済み）

`_select_chunks_ai()` でLLM API呼び出しが失敗すると、例外をキャッチして空リストを返す:

```python
# markdown_parser.py:917-921
try:
    response_text = self._llm_provider.send_message(system_text, user_text)
except Exception as exc:
    logger.warning(f"AI API call failed: {exc}")
    return [], None  # ← サイレントに空リストを返す
```

`_refine_sections()` は空リストを受け取ると `_chunk_lines_by_threshold()` にフォールバックするが、`parse()` の戻り値 `warnings` にフォールバック情報が含まれないため、呼び出し元が検知できない。

> **md2map 側の修正は別途進行中。** 本計画書のスコープでは、md2map が `warnings` を返すことを前提として、バックエンド・フロントエンド側の伝搬・表示を実装する。

---

## 前提

- 現在の実装: `versions/v0.9.5`（`latest` シンボリックリンク先）
- v0.9.5 上で修正を行う
- md2map の warnings 対応は別途進行中。本計画書では md2map の修正は行わない

---

## Step 1: フロントエンド — `llmConfig` を常に渡す

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.5/frontend/src/features/reviewer/hooks/useSplitSettings.ts` | `llmConfig` の渡し方を簡素化 |

### 修正内容

`splitMarkdown` 呼び出し時に、条件分岐を削除して常に `llmConfig` を渡す。

```typescript
// 修正前
llmConfig: (hasPreImportant ? normalSplitSettings.splitMode === 'ai' : settings.documentSplitMode === 'ai')
  ? (llmConfig ?? undefined) : undefined,

// 修正後
llmConfig: llmConfig ?? undefined,
```

md2map は遅延初期化のため、AI分割もAIサマリーも使わない設定なら `llm_config` は無視される。条件分岐は不要。

---

## Step 2: バックエンド — warnings を SplitMarkdownResponse に含める

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.5/backend/app/models/schemas.py` | `SplitMarkdownResponse` に `warnings` フィールドを追加 |
| `versions/v0.9.5/backend/app/routers/split.py` | `parse()` の warnings をレスポンスに含める |

### 修正内容

#### schemas.py

```python
class SplitMarkdownResponse(BaseModel):
    """Markdown分割APIのレスポンス"""

    success: bool
    parts: list[DocumentPart] = []
    indexContent: str | None = None
    mapJson: list[dict] | None = None
    warnings: list[str] = []  # ★ 追加: パース時の警告メッセージ
    error: str | None = None
```

> `SplitCodeResponse` は既に `warnings: list[str] = []` を持っているため、設計書側も同じ形式に揃える。

#### split.py

```python
sections, warnings = parser.parse(input_path, request.maxDepth)

# ... 既存処理 ...

return SplitMarkdownResponse(
    success=True,
    parts=parts,
    indexContent=index_content,
    mapJson=map_json,
    warnings=warnings,  # ★ 追加
)
```

---

## Step 3: フロントエンド — 設計書分割の warnings を表示

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.5/frontend/src/features/reviewer/types/index.ts` | `SplitMarkdownResponse` に `warnings` フィールドを追加 |
| `versions/v0.9.5/frontend/src/features/reviewer/hooks/useSplitSettings.ts` | 設計書分割の warnings を収集・保持 |
| `versions/v0.9.5/frontend/src/features/reviewer/components/SplitSettingsSection.tsx` | 設計書分割の warnings を表示 |

### 修正内容

#### types/index.ts

```typescript
export interface SplitMarkdownResponse {
  success: boolean
  parts: DocumentPart[]
  indexContent?: string
  mapJson?: Record<string, unknown>[]
  warnings?: string[]  // ★ 追加
  error?: string
}
```

#### useSplitSettings.ts

設計書分割の warnings を `SplitPreviewResult` に追加し、コード分割の warnings と同様に保持する。

```typescript
// SplitPreviewResult に追加
documentWarnings?: string[]

// executePreview 内
if (response.success) {
  documentParts = response.parts
  documentIndex = response.indexContent || null
  documentMapJson = response.mapJson || null
  documentWarnings = response.warnings || []  // ★ 追加
}
```

#### SplitSettingsSection.tsx

コード分割の警告パネル（既存）と同じUI形式で、設計書分割の警告を表示する。

```tsx
{/* 設計書分割の警告（AIフォールバック等） */}
{previewResult.documentWarnings && previewResult.documentWarnings.length > 0 && (
  <div className="mt-2 p-3 bg-amber-50 border border-amber-200 rounded">
    <p className="text-sm font-medium text-amber-800">
      設計書分割時に警告があります
    </p>
    <ul className="mt-1 text-xs text-amber-700 list-disc list-inside space-y-0.5">
      {previewResult.documentWarnings.map((w, i) => (
        <li key={i}>{w}</li>
      ))}
    </ul>
  </div>
)}
```

---

## Step 4: フロントエンド — 分割モード送信元の統一（#86）

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.5/frontend/src/features/reviewer/hooks/useSplitSettings.ts` | `splitMode` / `maxDepth` / `aiPromptExtraNotes` の取得元を `normalSplitSettings` に統一 |

### 修正内容

`splitMarkdown` リクエスト構築時、`hasPreImportant` の有無で分岐していた3つのパラメータを `normalSplitSettings` から常に取得するよう統一する。

```typescript
// 修正前（splitMode だけ settings から取得 — 不整合）
maxDepth: hasPreImportant ? normalSplitSettings.headingLevel : settings.documentMaxDepth,
splitMode: hasPreImportant ? normalSplitSettings.splitMode : settings.documentSplitMode,
aiPromptExtraNotes: hasPreImportant
  ? (normalSplitSettings.splitMode === 'ai' && normalSplitSettings.splitInstructions
    ? normalSplitSettings.splitInstructions
    : undefined)
  : (settings.documentSplitMode === 'ai' && settings.aiPromptExtraNotes
    ? settings.aiPromptExtraNotes
    : undefined),

// 修正後（全て normalSplitSettings に統一）
maxDepth: normalSplitSettings.headingLevel,
splitMode: normalSplitSettings.splitMode,
aiPromptExtraNotes: normalSplitSettings.splitMode === 'ai' && normalSplitSettings.splitInstructions
  ? normalSplitSettings.splitInstructions
  : undefined,
```

`summaryMode` / `summaryMaxChars` / `maxSubsections` は既に `normalSplitSettings` から取得されているため変更不要。

---

## Step 5: テスト

### バックエンド テスト

| テストケース | 内容 |
|---|---|
| warnings のレスポンス伝搬 | `parse()` が返した warnings が `SplitMarkdownResponse.warnings` に含まれること |

### フロントエンド テスト

| テストケース | 内容 |
|---|---|
| llmConfig の常時送信 | `splitMarkdown` 呼び出し時に splitMode に関わらず `llmConfig` が含まれること |
| 設計書警告の表示 | warnings が存在する場合、警告パネルが表示されること |
| splitMode の送信元 | `hasPreImportant` の有無にかかわらず `normalSplitSettings.splitMode` が送信されること |

---

## 修正順序と依存関係

```
Step 1: フロントエンド — llmConfig を常に渡す（独立して実施可能）
  ↓
Step 2: バックエンド — warnings を SplitMarkdownResponse に含める（独立して実施可能）
  ↓
Step 3: フロントエンド — 設計書分割の warnings を表示（Step 2 に依存）
  ↓
Step 4: フロントエンド — 分割モード送信元の統一（独立して実施可能）
  ↓
Step 5: テスト
```

> md2map 側の warnings 対応が完了すると、バックエンド・フロントエンドの伝搬経路を通じて自動的にユーザーに警告が表示される。

---

## 影響範囲

| 対象 | 影響 |
|---|---|
| バックエンド（schemas.py） | `SplitMarkdownResponse` に `warnings` フィールド追加（デフォルト空リストのため後方互換） |
| バックエンド（split.py） | warnings の伝搬追加 |
| フロントエンド（hooks） | `llmConfig` の条件分岐削除、documentWarnings の追加、splitMode 送信元の統一 |
| フロントエンド（UI） | 設計書警告パネルの追加 |
| md2map | subtree最新化済み（LLM失敗時の warnings 対応を含む v0.4.1） |
| code2map | 変更なし |

---

## 関連

- Issue: [#84 AIモード分割プレビューでLLM認証情報が不正な場合にエラーなく結果が返る](https://github.com/elvezjp/spec-code-ai-reviewer/issues/84)
- Issue: [#86 分割プレビューで事前重要指定なし時にUIの分割モード選択が反映されない](https://github.com/elvezjp/spec-code-ai-reviewer/issues/86)
- 分割レビュー機能の詳細: [split-review.md](split-review.md)
- 分割エラーハンドリング計画書: [20260312-issue52-53-split-error-handling-plan.md](20260312-issue52-53-split-error-handling-plan.md)

---

## 完了チェックリスト

### Step 1: フロントエンド — llmConfig を常に渡す

- [x] `useSplitSettings.ts` の `llmConfig` 条件分岐を削除し常時渡しに変更

### Step 2: バックエンド — warnings を SplitMarkdownResponse に含める

- [x] `SplitMarkdownResponse` に `warnings: list[str] = []` フィールドを追加
- [x] `split_markdown` エンドポイントで warnings をレスポンスに含める

### Step 3: フロントエンド — 設計書分割の warnings を表示

- [x] `SplitMarkdownResponse` 型に `warnings` フィールドを追加
- [x] `SplitPreviewResult` に `documentWarnings` を追加
- [x] `executePreview` で documentWarnings を収集・保持
- [x] `SplitSettingsSection.tsx` に設計書警告パネルを追加

### Step 4: フロントエンド — 分割モード送信元の統一

- [x] `splitMode` を `normalSplitSettings.splitMode` から常に取得するよう修正
- [x] `maxDepth` を `normalSplitSettings.headingLevel` から常に取得するよう修正
- [x] `aiPromptExtraNotes` を `normalSplitSettings` から常に取得するよう修正

### Step 5: テスト

- [x] バックエンド: warnings 伝搬テスト（UT-SPL-024）
- [x] フロントエンド: llmConfig 常時送信テスト（UT-SPLA-012）
- [x] フロントエンド: warnings レスポンス処理テスト（UT-SPLA-011）
- [x] フロントエンド: splitMode 送信元テスト（UT-SPLA-013）
- [x] 全バックエンドテスト通過（190件）
- [x] 全フロントエンドテスト通過（205件）
