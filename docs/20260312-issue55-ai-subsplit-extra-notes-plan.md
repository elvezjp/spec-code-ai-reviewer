# issue#55 AIサブスプリット「分割時の注意事項」対応計画

## 概要

md2map v0.3.0 で追加された `--ai-prompt-extra-notes` オプション（`ai_prompt_extra_notes` パラメータ）を
`versions/v0.9.1` のフロントエンド・バックエンドに対して有効化する。

ユーザーがAIモードで分割する際に「分割時の注意事項」を自由テキストで入力でき、
それがAIサブスプリットのプロンプト `# 注意事項` パートの末尾に追記される。

## 背景

### issue#55 の問題

- Mermaidブロックやコードブロックの途中、ネスト構造の途中で分割が行われることがある
- ユーザーが分割の観点（粒度・ルール）を指定する手段がなかった

### md2map v0.3.0 での対応

- `MarkdownParser(ai_prompt_extra_notes=...)` パラメータを追加
- AIサブスプリットのシステムプロンプト `# 注意事項` パート末尾にユーザー指定テキストを追記
- ユーザーは「Mermaidブロックの途中では分割しない」などを自由に指定できる

### このリポジトリでの対応範囲

md2map側はすでに対応済みのため、以下の3層に追加対応が必要：

1. バックエンド: APIスキーマ・ルーターへの追加
2. フロントエンド型定義: `SplitSettings` への追加
3. フロントエンドUI: `SplitSettingsSection` へのテキストエリア追加

## 修正対象ファイル

| ファイル | 修正種別 |
|---------|---------|
| `versions/v0.9.1/backend/app/models/schemas.py` | フィールド追加 |
| `versions/v0.9.1/backend/app/routers/split.py` | パラメータ追加 |
| `versions/v0.9.1/frontend/src/features/reviewer/types/index.ts` | 型定義追加 |
| `versions/v0.9.1/frontend/src/features/reviewer/components/SplitSettingsSection.tsx` | UIフィールド追加 |
| `versions/v0.9.1/spec.md` | 仕様書追記（2.7.3 分割オプション） |
| `docs/split-review.md` | 仕様書追記（3. 分割設定） |

## 修正詳細

### 1. バックエンド: APIスキーマ（schemas.py）

`SplitMarkdownRequest` に `aiPromptExtraNotes` フィールドを追加する。

**修正前:**
```python
class SplitMarkdownRequest(BaseModel):
    content: str
    filename: str
    maxDepth: int = Field(default=2, ge=1, le=6)
    splitMode: Literal["ai", "heading", "nlp"] = "ai"
    llmConfig: LLMConfig | None = None
```

**修正後:**
```python
class SplitMarkdownRequest(BaseModel):
    content: str
    filename: str
    maxDepth: int = Field(default=2, ge=1, le=6)
    splitMode: Literal["ai", "heading", "nlp"] = "ai"
    llmConfig: LLMConfig | None = None
    aiPromptExtraNotes: str | None = None
```

### 2. バックエンド: 分割ルーター（split.py）

`MarkdownParser` のインスタンス化時に `ai_prompt_extra_notes` を渡す。

**修正前:**
```python
parser = MarkdownParser(
    split_mode=request.splitMode,
    llm_config=md2map_llm_config,
    max_subsections=max_subsections,
)
```

**修正後:**
```python
parser = MarkdownParser(
    split_mode=request.splitMode,
    llm_config=md2map_llm_config,
    max_subsections=max_subsections,
    ai_prompt_extra_notes=request.aiPromptExtraNotes,
)
```

### 3. フロントエンド: 型定義（types/index.ts）

`SplitSettings` インターフェースに `aiPromptExtraNotes` を追加する。

**修正前:**
```typescript
interface SplitSettings {
  reviewMode: SplitMode
  documentMaxDepth: number
  documentSplitMode: DocumentSplitMode
}
```

**修正後:**
```typescript
interface SplitSettings {
  reviewMode: SplitMode
  documentMaxDepth: number
  documentSplitMode: DocumentSplitMode
  aiPromptExtraNotes: string
}
```

`SplitSettings` の初期値を持つ箇所（`useSplitSettings` フックなど）にも `aiPromptExtraNotes: ''` を追加する。

### 4. フロントエンド: UIコンポーネント（SplitSettingsSection.tsx）

AIモード（`documentSplitMode === 'ai'`）選択時のみ表示されるテキストエリアを追加する。

**追加UI仕様:**

- 表示条件: `settings.documentSplitMode === 'ai'` のとき
- ラベル: 「分割時の注意事項（任意）」
- 入力形式: `<textarea>`（複数行）
- プレースホルダー: 「例: Mermaidブロックの途中では分割しない、項番単位で分割する」
- 変更ハンドラー: `onSettingsChange({ ...settings, aiPromptExtraNotes: value })`
- 配置: 分割モード選択（AIモードのラジオボタン）の直下

**UIスケッチ（AIモード選択時）:**
```
設計書・分割モード
  ○ 見出し  ○ NLP  ● AI（推奨）

  分割時の注意事項（任意）
  ┌─────────────────────────────────────────┐
  │ 例: Mermaidブロックの途中では分割しない  │
  │     項番単位で分割する                   │
  └─────────────────────────────────────────┘
```

### 5. フロントエンド: APIリクエスト送信箇所

`aiPromptExtraNotes` をAPIリクエストに含める箇所を確認し追加する。
（`/api/split/markdown` へのPOSTリクエストのボディ）

### 6. 仕様書: versions/v0.9.1/spec.md

`2.7.3 分割オプション` の **設計書分割オプション** テーブルに行を追加する。

**修正前:**

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| 分割モード | 分割方式の選択（見出し / NLP / AI） | 見出し（heading） |
| 見出しレベル | 分割する見出しレベル（H2/H3/H4まで） | H2まで（推奨） |

- 分割モードは「見出し」「NLP」「AI」の3択。ユーザーが明示的に選択する
- AIモード選択時はLLM設定が必要（レビュー実行用のLLM設定を流用する）
- 見出しレベルは全モード共通で指定可能

**修正後:**

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| 分割モード | 分割方式の選択（見出し / NLP / AI） | 見出し（heading） |
| 見出しレベル | 分割する見出しレベル（H2/H3/H4まで） | H2まで（推奨） |
| 分割時の注意事項（AIモード専用） | AIサブスプリットのプロンプトに追記する注意事項（任意） | なし |

- 分割モードは「見出し」「NLP」「AI」の3択。ユーザーが明示的に選択する
- AIモード選択時はLLM設定が必要（レビュー実行用のLLM設定を流用する）
- 見出しレベルは全モード共通で指定可能
- 「分割時の注意事項」はAIモード選択時のみ表示・有効。入力されたテキストはAIサブスプリットのシステムプロンプト `# 注意事項` パート末尾に追記される（例: 「Mermaidブロックの途中では分割しない」「項番単位で分割する」）

### 7. 仕様書: docs/split-review.md

`3. 分割設定` セクションに **3.3 AIモード分割時の注意事項指定** を追加する。

**追加内容:**

```markdown
### 3.3 AIモード分割時の注意事項指定

AIモード選択時、分割オプションに「分割時の注意事項（任意）」テキストエリアが表示される。

- ユーザーが入力したテキストは md2map の AIサブスプリットプロンプト `# 注意事項` パートの末尾に追記される
- ドメイン固有の分割ルールを柔軟に指定できる
- 入力例: 「Mermaidブロックの途中では分割しない」「処理フロー単位で分割する」「項番単位で分割する」
- 空欄の場合は md2map のデフォルトプロンプトのみが使用される
- 見出し（heading）モード・NLPモードでは表示されない（AIサブスプリット専用）
```

## 修正しないもの

- AIモード以外（heading / nlp）では `aiPromptExtraNotes` は無視される（バックエンドで `split_mode != 'ai'` の場合は md2map 側が無視するため、フロントエンドで送信しても問題ない）

## 確認事項

- [ ] `aiPromptExtraNotes` が空文字 `''` のとき、バックエンドで `None` として扱われるか確認（`or None` で変換する）
- [ ] テキストエリアのリサイズはCSSで `resize: vertical` または固定サイズで対応
- [ ] 既存の `SplitSettings` 初期値・初期化箇所への追加漏れがないか確認

## 完了チェックリスト

### バックエンド
- [x] `schemas.py`: `SplitMarkdownRequest` に `aiPromptExtraNotes: str | None = None` を追加
- [x] `split.py`: `MarkdownParser` に `ai_prompt_extra_notes=request.aiPromptExtraNotes` を渡す

### フロントエンド
- [x] `types/index.ts`: `SplitSettings` に `aiPromptExtraNotes: string` を追加
- [x] `useSplitSettings.ts`: `SplitSettings` 初期値に `aiPromptExtraNotes: ''` を追加
- [x] `SplitSettingsSection.tsx`: AIモード選択時のみ表示されるテキストエリアを追加
- [x] `useSplitSettings.ts`: `/api/split/markdown` リクエストボディに `aiPromptExtraNotes` を含める

### 仕様書
- [x] `versions/v0.9.1/spec.md`: `2.7.3 分割オプション` テーブルと説明文に追記
- [x] `docs/split-review.md`: `3.2 AIモード分割時の注意事項指定` セクションを追加

### 動作確認
- [ ] AIモードを選択するとテキストエリアが表示される
- [ ] 見出し / NLP モードではテキストエリアが表示されない
- [ ] テキストエリアに入力した内容がリクエストに含まれてバックエンドに渡る
- [ ] 空欄のまま分割プレビューを実行しても正常に動作する

---

## 追加: 分割オプションUIの視認性改善

`SplitSettingsSection.tsx` の分割オプション表示を改善する。

### 8. UIの視認性改善（SplitSettingsSection.tsx）

#### 8.1 設計書・プログラムエリアの背景分割

現状は設計書とプログラムが同一の `bg-gray-50` 背景で区別しづらい。
それぞれを独立したカードに分ける。

- 設計書エリア: `bg-white border border-gray-200 rounded p-3`
- プログラムエリア: `bg-white border border-gray-200 rounded p-3`
- 両エリアを `space-y-2` で区切る

#### 8.2 ラベルの太字化

以下のラベルを `font-medium` → `font-semibold` または `font-medium` に統一して太字にする：

| ラベル | 変更前 | 変更後 |
|-------|--------|--------|
| 設計書 | `text-sm font-medium` | `text-sm font-semibold` |
| プログラム | `text-sm font-medium` | `text-sm font-semibold` |
| 分割モード: | `text-sm text-gray-600` | `text-sm font-medium text-gray-700` |
| 分割時の注意事項（AIへの指示・任意） | `text-sm text-gray-600` | `text-sm font-medium text-gray-700` |
| 見出しレベル: | `text-sm text-gray-600` | `text-sm font-medium text-gray-700` |
| 対応言語 | （`<p>` テキスト） | `text-sm font-medium text-gray-700` に変更 |

#### 8.3 テキストエリアの白背景化

現在のテキストエリアは `bg-gray-50` 背景内に配置されており背景が馴染みすぎる。
`bg-white` を明示的に追加する：

```tsx
className="w-full text-sm bg-white border border-gray-300 rounded px-2 py-1 resize-vertical focus:outline-none focus:border-blue-400"
```

#### 8.4 ラベルテキストの変更

```
分割時の注意事項（任意）
→ 分割時の注意事項（AIへの指示・任意）
```

### 追加の完了チェックリスト

- [ ] `SplitSettingsSection.tsx`: 設計書・プログラムエリアを白背景カードに分割
- [ ] `SplitSettingsSection.tsx`: 「設計書」「プログラム」見出しを `font-semibold` に変更
- [ ] `SplitSettingsSection.tsx`: 「分割モード:」「分割時の注意事項」「見出しレベル:」「対応言語」ラベルを `font-medium text-gray-700` に変更
- [ ] `SplitSettingsSection.tsx`: テキストエリアに `bg-white` を追加
- [ ] `SplitSettingsSection.tsx`: ラベルを `分割時の注意事項（AIへの指示・任意）` に変更

## 関連

- issue#55: https://github.com/elvezjp/spec-code-ai-reviewer/issues/55
- md2map CHANGELOG: `md2map/CHANGELOG.md` (v0.3.0)
- md2map 実装: `md2map/md2map/parsers/markdown_parser.py` (行 645-646)
- 分割レビュー仕様: `docs/split-review.md`
