# 分割プレビュー設定の拡充 修正計画書

## 概要

分割プレビューの設定に、以下の md2map オプションをUI上で指定可能にする:

1. **サマリー生成オプション**: `summary_mode`（text/ai）/ `summary_max_chars`（文字数上限）
2. **最大サブスプリット数**: `max_subsections` をUI上で指定可能にし、環境変数 `MD2MAP_MAX_SUBSECTIONS` への依存を廃止する

対応 Issue: [#71](https://github.com/elvezjp/spec-code-ai-reviewer/issues/71)
md2map 側 Issue: [elvezjp/md2map#15](https://github.com/elvezjp/md2map/issues/15)

## 背景

### サマリー生成の課題

md2map が生成する INDEX.md の `summary` フィールドは、各セクションの冒頭テキストを固定100文字で切り出したものであり、要約として不十分な場合がある。

md2map の issue #15 では以下の2案が提案されている:

- **案A**: `--summary-max-chars` パラメータで文字数上限を変更可能にする（ルールベース改善）
- **案B**: `--summary-mode`（`text` / `ai`）でLLMによる要約生成を選択可能にする

これらのオプションが md2map 側で実装された際に、本プロジェクトの分割プレビュー設定UIから指定できるようにする。

### 最大サブスプリット数の課題

NLP/AIモードでのサブスプリット最大数（`max_subsections`）は、現在バックエンド側の環境変数 `MD2MAP_MAX_SUBSECTIONS`（デフォルト: 5）で制御されている。
フロントエンドの `PreImportantSplitSettings` 型には `maxSubsections` フィールドが存在するが、UIに入力欄がなく常にデフォルト値 `0`（= 環境変数にフォールバック）が送信される。

ユーザーが文書の特性に応じてサブスプリット数を調整できるよう、UIから直接指定可能にし、環境変数への依存を廃止する。

## UX フロー

### 現状のフロー（v0.9.3）

```
設計書アップロード → Markdown変換
→ 「分割」選択時にセクション一覧を取得・表示
→ 「事前重要指定」「事前除外」セクションを選択
→ 「事前重要指定」「通常」の分割モード選択 → 分割プレビュー実行
→ 一覧から重要・除外・要約を手動チェック → レビュー開始
```

### 改善後のフロー（v0.9.4）

```
設計書アップロード → Markdown変換
→ 「分割」選択時にセクション一覧を取得・表示
→ 「事前重要指定」「事前除外」セクションを選択
→ 「事前重要指定」「通常」の分割モード選択
→ 最大サブスプリット数を指定                               ← 追加（UIに昇格）
→ サマリー生成設定（サマリーモード・文字数上限）を指定       ← 追加
→ 分割プレビュー実行
→ 一覧から重要・除外・要約を手動チェック → レビュー開始
```

### 変更後の画面イメージ

#### 画面①: 事前指定パネル

変更なし。

#### 画面②: 分割プレビュー実行（分割設定の変更）

「設計書 — 事前重要指定セクション」と「設計書 — 通常セクション」の各ブロックに、サマリー生成設定を追加する。

```
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 設計書 — 事前重要指定セクション                               │ │
│ │                                                             │ │
│ │ 分割モード:                                                  │ │
│ │  ○ 見出し   ○ NLP   ◉ AI（推奨）  見出しに加えて…           │ │
│ │                                                             │ │
│ │ 分割時の注意事項（AIへの指示・任意）                           │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │                                                         │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ │                                                             │ │
│ │ 見出しレベル:                                                │ │
│ │  ◉ H2(##)まで（推奨）  ○ H3(###)まで  ○ H4(####)まで       │ │
│ │                                                             │ │
│ │ 1セクションあたりの最大分割数:  [5]               【新規追加】│ │
│ │                                                             │ │
│ │ サマリーモード:                                   【新規追加】│ │
│ │  ○ ルールベース  ◉ AI（推奨）                                │ │
│ │ サマリー最大文字数（ルールベース時）:  [100]                   │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 設計書 — 通常セクション                                       │ │
│ │                                                             │ │
│ │ （同様の分割設定 + サマリー設定を追加）                        │ │
│ └─────────────────────────────────────────────────────────────┘ │
```

- **1セクションあたりの最大分割数**: NLP/AIモード時のサブスプリット最大数。デフォルト5（現行動作と後方互換）。見出しモード時は非表示
- **サマリーモード**: `ai`（デフォルト・推奨）= LLMによる要約生成、`text` = ルールベース要約
- **サマリー最大文字数**: ルールベース時のみ有効。デフォルト100文字（現行動作と後方互換）
- AIモード選択時はサマリー最大文字数の入力は非表示（LLMが適切な長さで要約するため）

#### 画面③: 分割結果一覧

変更なし。INDEX.md の summary はバックグラウンドで生成されるため、UI表示への直接的な影響はない。

---

## 前提

- 現在の実装: `versions/v0.9.3`
- `versions/v0.9.3` を丸ごとコピーして `versions/v0.9.4` を作成し、v0.9.4 上で修正を行う
- md2map 側で案A（`--summary-max-chars`）および案B（`--summary-mode`）が実装済みであること
  - md2map Issue: [elvezjp/md2map#15](https://github.com/elvezjp/md2map/issues/15)
  - md2map が `MarkdownParser` コンストラクタに `summary_mode` / `summary_max_chars` を受け取り、`section_overrides` でセクション単位のオーバーライドも可能であること
- `max_subsections` は既に md2map の `MarkdownParser` コンストラクタ引数および `section_overrides` で対応済み
- 環境変数 `MD2MAP_MAX_SUBSECTIONS` は本計画で廃止し、UIから直接指定する方式に移行する

---

## Step 0: v0.9.4 ディレクトリの作成

- `versions/v0.9.3` を `versions/v0.9.4` にコピー
- v0.9.4 の spec.md にバージョン番号を反映

---

## Step 1: バックエンド — API スキーマの修正

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.4/backend/app/models/schemas.py` | `SplitSettingsDetail` に `summaryMode` / `summaryMaxChars` を追加、`SplitMarkdownRequest` にグローバルオプション（`summaryMode` / `summaryMaxChars` / `maxSubsections`）を追加 |

### スキーマ変更

#### SplitSettingsDetail（セクション単位オーバーライド用）

```python
class SplitSettingsDetail(BaseModel):
    """分割設定の詳細（事前重要指定セクション用 / 通常セクション用）"""

    splitMode: Literal["ai", "heading", "nlp"] | None = None
    headingLevel: int | None = None
    splitInstructions: str | None = None
    maxSubsections: int | None = None
    summaryMode: Literal["text", "ai"] | None = None       # ← 追加: サマリー生成モード
    summaryMaxChars: int | None = None                      # ← 追加: テキストモード時の文字数上限
```

#### SplitMarkdownRequest（グローバルオプション）

```python
class SplitMarkdownRequest(BaseModel):
    """Markdown分割APIのリクエスト"""

    content: str
    filename: str
    maxDepth: int = Field(default=2, ge=1, le=6)
    splitMode: Literal["ai", "heading", "nlp"] = "ai"
    llmConfig: LLMConfig | None = None
    aiPromptExtraNotes: str | None = None
    maxSubsections: int | None = None                        # ← 追加: グローバル最大サブスプリット数（デフォルト: 5）
    # 事前重要指定関連フィールド
    preImportantSections: list[int] | None = None
    preImportantSplitSettings: SplitSettingsDetail | None = None
    normalSplitSettings: SplitSettingsDetail | None = None
    # 事前除外関連フィールド
    preExcludedSections: list[int] | None = None
    # サマリー生成関連フィールド
    summaryMode: Literal["text", "ai"] | None = None        # ← 追加: グローバルサマリーモード（デフォルト: text）
    summaryMaxChars: int | None = None                       # ← 追加: グローバル文字数上限（デフォルト: 100）
```

※ `maxSubsections` を `SplitMarkdownRequest` に昇格することで、事前重要指定を使わない従来モードでもフロントエンドから指定可能にする。

---

## Step 2: バックエンド — エンドポイントの修正

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.4/backend/app/routers/split.py` | `POST /split/markdown` で `summaryMode` / `summaryMaxChars` を md2map に渡す。`max_subsections` の環境変数フォールバックを廃止し、リクエスト値のみを使用する |

### 変更ポイント

#### 2-1. 環境変数 `MD2MAP_MAX_SUBSECTIONS` の廃止

現在の `max_subsections` 決定ロジック:

```python
# 変更前（v0.9.3）: 環境変数にフォールバック
max_subsections = normal_settings.maxSubsections or int(
    os.environ.get("MD2MAP_MAX_SUBSECTIONS", "5")
)
```

```python
# 変更後（v0.9.4）: リクエスト値のみ使用、デフォルト5
max_subsections = normal_settings.maxSubsections or 5
```

従来モード（事前重要指定なし）も同様:

```python
# 変更前
max_subsections = int(os.environ.get("MD2MAP_MAX_SUBSECTIONS", "5"))
# 変更後
max_subsections = request.maxSubsections or 5
```

※ `SplitMarkdownRequest` にグローバルな `maxSubsections` フィールドを追加する（Step 1 参照）。

#### 2-2. サマリー設定の受け渡し

```python
# 1. グローバルのサマリー設定を決定
if has_pre_important and request.normalSplitSettings:
    normal_settings = request.normalSplitSettings
    summary_mode = normal_settings.summaryMode or request.summaryMode or "text"
    summary_max_chars = normal_settings.summaryMaxChars or request.summaryMaxChars or 100
else:
    summary_mode = request.summaryMode or "text"
    summary_max_chars = request.summaryMaxChars or 100

# 2. AIサマリーモードの場合もLLM設定が必要
if summary_mode == "ai" and md2map_llm_config is None:
    md2map_llm_config = _convert_to_md2map_llm_config(request.llmConfig)

# 3. section_overrides にサマリー設定を含める
if has_pre_important and request.preImportantSplitSettings:
    pre_settings = request.preImportantSplitSettings
    section_overrides = [
        {
            "start_line": start_line,
            "split_mode": pre_split_mode,
            "max_subsections": pre_settings.maxSubsections or max_subsections,
            "ai_prompt_extra_notes": pre_settings.splitInstructions or "",
            "summary_mode": pre_settings.summaryMode or summary_mode,        # ← 追加
            "summary_max_chars": pre_settings.summaryMaxChars or summary_max_chars,  # ← 追加
        }
        for start_line in request.preImportantSections
    ]

# 4. md2map に渡す
parser = MarkdownParser(
    split_mode=split_mode,
    llm_config=md2map_llm_config,
    max_subsections=max_subsections,         # ← 環境変数ではなくリクエスト値
    ai_prompt_extra_notes=ai_prompt_extra_notes,
    section_overrides=section_overrides,
    summary_mode=summary_mode,              # ← 追加
    summary_max_chars=summary_max_chars,    # ← 追加
)
```

---

## Step 3: フロントエンド — 型定義・API の修正

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.4/frontend/src/features/reviewer/types/index.ts` | `PreImportantSplitSettings` と `SplitMarkdownRequest` にフィールド追加 |
| `versions/v0.9.4/frontend/src/features/reviewer/services/api.ts` | `splitMarkdown()` リクエストにサマリー設定を含める |

### 型定義の変更

```typescript
export type SummaryMode = 'text' | 'ai'

export interface PreImportantSplitSettings {
  splitMode: DocumentSplitMode
  headingLevel: number
  splitInstructions: string
  maxSubsections: number           // 既存（UIに昇格）
  summaryMode: SummaryMode         // ← 追加
  summaryMaxChars: number          // ← 追加
}

export interface SplitMarkdownRequest {
  content: string
  filename: string
  maxDepth: number
  splitMode?: DocumentSplitMode
  llmConfig?: LlmConfig
  aiPromptExtraNotes?: string
  maxSubsections?: number          // ← 追加: グローバル最大サブスプリット数
  preImportantSections?: number[]
  preImportantSplitSettings?: PreImportantSplitSettings
  normalSplitSettings?: PreImportantSplitSettings
  preExcludedSections?: number[]
  summaryMode?: SummaryMode        // ← 追加
  summaryMaxChars?: number         // ← 追加
}
```

---

## Step 4: フロントエンド — UI コンポーネントの修正

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.4/frontend/src/features/reviewer/components/SplitSettingsSection.tsx` | `DocumentSplitSettingsBlock` にサマリー設定UIを追加 |

### UI 仕様

`DocumentSplitSettingsBlock`（事前重要指定セクション用・通常セクション用の両方）に以下を追加:

1. **1セクションあたりの最大分割数**（数値入力フィールド）— UIに昇格
   - 分割モードが `nlp` または `ai` の場合のみ表示（`heading` モード時は非表示）
   - デフォルト値: 5
   - ラベル: 「1セクションあたりの最大分割数」

2. **サマリーモード選択**（ラジオボタン）
   - `text`（ルールベース）
   - `ai`（AI / 推奨）— デフォルト
   - ラベル: 「サマリーモード」

3. **サマリー最大文字数**（数値入力フィールド）
   - サマリーモードが `text`（ルールベース）の場合のみ表示
   - デフォルト値: 100
   - ラベル: 「サマリー最大文字数」

---

## Step 5: フロントエンド — 状態管理の修正

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.4/frontend/src/features/reviewer/hooks/useSplitSettings.ts` | `preImportantSplitSettings` と `normalSplitSettings` の初期値にサマリー設定を追加、`executePreview()` でサマリー設定を API に送信 |

### 状態管理の追加

```typescript
// PreImportantSplitSettings の初期値を更新
const defaultSplitSettings: PreImportantSplitSettings = {
  splitMode: 'ai',
  headingLevel: 2,
  splitInstructions: '',
  maxSubsections: 5,         // ← 変更: 0 → 5（環境変数フォールバック廃止に伴いデフォルト値を明示）
  summaryMode: 'ai',         // ← 追加（デフォルト: AI推奨）
  summaryMaxChars: 100,      // ← 追加
}
```

### executePreview() の変更

```typescript
const response = await api.splitMarkdown({
  // ... 既存パラメータ
  // サマリー設定を含める（PreImportantSplitSettings に含まれるため、
  // preImportantSplitSettings / normalSplitSettings 経由で自動的に送信される）
})
```

※ `PreImportantSplitSettings` にサマリー設定フィールドを追加するため、既存の `preImportantSplitSettings` / `normalSplitSettings` の送信ロジックに自動的に含まれる。追加のコード変更は最小限。

---

## Step 6: テストの追加

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.4/backend/tests/` | サマリー設定パラメータのテスト追加 |
| `versions/v0.9.4/frontend/src/__tests__/` | サマリー設定UIのテスト追加 |

### バックエンドテストケース

| ケース | 内容 |
|---|---|
| summaryMode 未指定 | デフォルト（text / 100文字）で動作する（後方互換性） |
| summaryMode = "text" + summaryMaxChars = 200 | 文字数上限200でルールベース要約が生成される |
| summaryMode = "ai" | LLMによる要約が生成される |
| セクション単位でのオーバーライド | 事前重要指定セクションと通常セクションで異なるサマリー設定が適用される |
| maxSubsections をリクエストで指定 | 環境変数ではなくリクエスト値が使用される |
| maxSubsections 未指定 | デフォルト5で動作する（後方互換性） |

### フロントエンドテストケース

| ケース | 内容 |
|---|---|
| 最大サブスプリット数UIの表示 | NLP/AIモード時に入力フィールドが表示され、デフォルト値が5になっている |
| 最大サブスプリット数の見出しモード非表示 | 分割モードが見出しの場合は入力フィールドが非表示になる |
| サマリーモード選択UIの表示 | ラジオボタンが表示され、デフォルトが「テキスト」になっている |
| テキストモード時の文字数上限入力 | 文字数上限フィールドが表示される |
| AIモード時の文字数上限非表示 | サマリーモードを「AI」に切り替えると文字数上限フィールドが非表示になる |
| executePreview で設定が送信される | API リクエストに maxSubsections / summaryMode / summaryMaxChars が含まれる |

---

## Step 7: ドキュメント更新

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.4/spec.md` | サマリー生成オプションの仕様を追記 |
| `docs/split-review.md` | サマリー生成オプションの説明を追記 |

---

## 修正順序と依存関係

```
Step 0: v0.9.4 作成
  ↓
Step 1: バックエンド スキーマ修正（SplitSettingsDetail, SplitMarkdownRequest）
  ↓
Step 2: バックエンド エンドポイント修正（md2map への summary_mode / summary_max_chars 受け渡し）
  ↓
Step 3: フロントエンド 型定義・API 修正（Step 1 のスキーマに対応）
  ↓
Step 4: フロントエンド UI 修正（DocumentSplitSettingsBlock にサマリー設定を追加）
  ↓
Step 5: フロントエンド 状態管理修正（Step 4 の設定値を管理）
  ↓
Step 6: テスト追加
  ↓
Step 7: ドキュメント更新
```

---

## 影響範囲

| 対象 | 影響 |
|---|---|
| md2map | 変更なし（md2map 側で実装済みの `summary_mode` / `summary_max_chars` / `max_subsections` をそのまま利用） |
| バックエンド | `SplitSettingsDetail` / `SplitMarkdownRequest` スキーマ拡張、`POST /split/markdown` でサマリー設定を md2map に受け渡し、環境変数 `MD2MAP_MAX_SUBSECTIONS` の参照を廃止 |
| フロントエンド | `PreImportantSplitSettings` に2フィールド追加、`DocumentSplitSettingsBlock` にサマリー設定UI・最大サブスプリット数UIを追加 |
| ドキュメント | `spec.md` にサマリー設定の仕様追記・環境変数削除、`split-review.md` に機能説明追記 |
| code2map | 変更なし |
| Phase 1〜3（構造マッチング・グループレビュー・統合） | 変更なし（INDEX.md の summary 品質が向上することで間接的にフェーズ1の精度向上が期待される） |

---

## 関連

- Issue: [#71 分割プレビュー設定にsummary_modeとsummary_max_charsオプションを追加する](https://github.com/elvezjp/spec-code-ai-reviewer/issues/71)
- md2map Issue: [elvezjp/md2map#15 INDEX.md の summary が要約として不十分](https://github.com/elvezjp/md2map/issues/15)
- 事前重要指定の計画書: [20260318-pre-split-importance-plan.md](20260318-pre-split-importance-plan.md)
- 事前除外の計画書: [20260324-pre-split-exclusion-plan.md](20260324-pre-split-exclusion-plan.md)

---

## 完了チェックリスト

### Step 0: v0.9.4 作成

- [ ] `versions/v0.9.3` を `versions/v0.9.4` にコピー
- [ ] v0.9.4 の全バージョン番号を更新
- [ ] インフラ設定（Docker/Nginx/PM2）に v0.9.4 を追加
- [ ] `latest` シンボリックリンクを v0.9.4 に更新
- [ ] 全バージョンの `useVersions.ts` に v0.9.4 を追加

### Step 1: バックエンド スキーマ修正

- [ ] `SplitSettingsDetail` に `summaryMode` / `summaryMaxChars` を追加
- [ ] `SplitMarkdownRequest` に `summaryMode` / `summaryMaxChars` / `maxSubsections` を追加

### Step 2: バックエンド エンドポイント修正

- [ ] `POST /split/markdown` でサマリー設定を md2map の `MarkdownParser` コンストラクタに渡す
- [ ] `section_overrides` にサマリー設定を含める
- [ ] AIサマリーモード時の LLM 設定初期化を追加
- [ ] 環境変数 `MD2MAP_MAX_SUBSECTIONS` への参照を削除し、リクエスト値（デフォルト5）を使用

### Step 3: フロントエンド 型定義・API 修正

- [ ] `SummaryMode` 型を追加
- [ ] `PreImportantSplitSettings` に `summaryMode` / `summaryMaxChars` を追加
- [ ] `SplitMarkdownRequest` に `summaryMode` / `summaryMaxChars` / `maxSubsections` を追加
- [ ] `splitMarkdown()` リクエストにサマリー設定と `maxSubsections` を含める

### Step 4: フロントエンド UI 修正

- [ ] `DocumentSplitSettingsBlock` に「1セクションあたりの最大分割数」入力フィールドを追加（NLP/AIモード時のみ表示）
- [ ] `DocumentSplitSettingsBlock` にサマリーモード選択ラジオボタンを追加（デフォルト: AI）
- [ ] ルールベース時の「サマリー最大文字数」入力フィールドを追加
- [ ] AIモード時のサマリー最大文字数フィールド非表示制御

### Step 5: フロントエンド 状態管理修正

- [ ] `PreImportantSplitSettings` の初期値を更新（`maxSubsections: 5`、`summaryMode: 'ai'`、`summaryMaxChars: 100`）
- [ ] サマリー設定・サブスプリット数変更時のプレビュー結果クリア（既存の設定変更と同様の動作）

### Step 6: テスト追加

- [ ] バックエンドテスト追加・全テスト通過
- [ ] フロントエンドテスト追加・全テスト通過

### Step 7: ドキュメント更新

- [ ] `versions/v0.9.4/spec.md` にサマリー生成オプション・最大サブスプリット数UIの仕様を追記
- [ ] `versions/v0.9.4/spec.md` の環境変数一覧から `MD2MAP_MAX_SUBSECTIONS` を削除
- [ ] `docs/split-review.md` にサマリー生成オプション・最大サブスプリット数UIの説明を追記

### 最終確認

- [ ] 全バックエンドテスト通過
- [ ] 全フロントエンドテスト通過
- [ ] 手動動作確認（サマリーモード切替 → 分割プレビュー → INDEX.md の summary 確認）
