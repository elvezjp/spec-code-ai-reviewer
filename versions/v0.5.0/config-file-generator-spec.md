# 設定ファイルジェネレーター（単一HTMLアプリ）

## 概要

Markdown形式の設定ファイルを生成するための**汎用的な**スタンドアロンアプリケーション。
JSONスキーマを差し替えることで、様々なアプリケーション向けの設定ファイル生成に対応できる。

現在はspec-code-ai-reviewer用の設定（`reviewer-config.md`）を生成するスキーマが設定されている。

## 使い方

1. `index.html` をブラウザで開く
2. 各セクションの項目を入力・編集
3. 「ダウンロード」ボタンをクリック

### 対応プロバイダー

| プロバイダー | 必要な認証情報 |
|-------------|---------------|
| Anthropic | API Key |
| Bedrock | Access Key ID, Secret Access Key, Region |
| OpenAI | API Key |

### 出力ファイル

`reviewer-config.md` がダウンロードされる。
このファイルをspec-code-ai-reviewerにアップロードして利用する。

## カスタマイズ

`index.html` 内の `SCHEMA` オブジェクトを編集することで、別のアプリケーション向けの設定ファイル生成に対応できる。

## 背景

ユーザーは `reviewer-config.md` ファイルを使用してLLMプロバイダーの認証情報や設計書種別を設定する。このファイルを簡単に作成できるツールが必要。

ただし、このツールは spec-code-ai-reviewer 専用ではなく、**汎用的な設定ファイルジェネレーター**として設計し、以下に対応できるようにする：
- 設定ファイル仕様のバージョンアップ
- 別アプリケーションへの転用

## 出力ファイル例

```markdown
# spec-code-ai-reviewer設定ファイル

## info

- version: v0.4.0
- created_at: 2025-01-15T10:30:00+09:00

## llm

- provider: bedrock
- accessKeyId: YOUR_ACCESS_KEY_ID
- secretAccessKey: YOUR_SECRET_ACCESS_KEY
- region: ap-northeast-1
- maxTokens: 16384
- models:
  - global.anthropic.claude-haiku-4-5-20251001-v1:0
  - global.anthropic.claude-sonnet-4-5-20250929-v1:0

## specTypes

| type | note |
|------|------|
| 設計書 | 機能仕様が正しく実装されているかを確認してください |
| ... | ... |

## systemPrompts

### 標準レビュープリセット

#### role

あなたは設計書とプログラムコードを突合し、整合性を検証するレビュアーです。

#### purpose

設計書の内容がプログラムに正しく実装されているかを検証し、差異や問題点を報告してください。

以下の観点でレビューを行ってください：
1. 機能網羅性: 設計書に記載された機能がコードに実装されているか
2. 仕様整合性: 関数名・変数名・データ型・処理フローが設計書と一致しているか
3. エラー処理: 設計書に記載されたエラー処理が実装されているか
4. 境界値・制約: 設計書に記載された制約条件がコードに反映されているか

#### format

マークダウン形式で、以下の順に出力してください：
1. サマリー（突合日時、ファイル名、総合判定）
2. 突合結果一覧（テーブル形式）
3. 詳細（問題点と推奨事項）

#### notes

- メイン設計書の内容について突合してください。
- 判定は「OK」「NG」「要確認」の3段階で行ってください
- 重要度が高い問題を優先して報告してください。
- 設計書を引用する際は、見出し番号や項目番号を明示してください。
- プログラムを引用する際は、行番号を必ず添えてください。
- 各設計書の冒頭に記載されている役割、種別、注意事項を考慮してください。
- メイン以外の設計書は必要な場合に参照してください。
```

## UI案

```
┌──────────────────────────────────────────────────────────────┐
│  設定ファイルジェネレーター                          v0.4.0  │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  spec-code-ai-reviewer の設定ファイルを作成します。              │
│  各項目を入力して「ダウンロード」ボタンを押してください。      │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│ ■ info（設定ファイル情報）                                    │
│                                                               │
│   version:    v0.4.0（固定）                                  │
│   created_at: ダウンロード時に自動生成                        │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│ ■ llm（LLMプロバイダー設定）                                  │
│                                                               │
│   プロバイダー: ( ) Anthropic  (●) Bedrock  ( ) OpenAI       │
│                                                               │
│   Access Key ID:     [________________________]               │
│   Secret Access Key: [________________________]               │
│   Region:            [ap-northeast-1_______________]               │
│   Max Tokens:        [16384___________________]               │
│                                                               │
│   モデル:                                                     │
│   [anthropic.claude-4-5-sonnet-20241022-v2:0] [×]            │
│   [anthropic.claude-4-5-haiku-20241022-v1:0 ] [×]            │
│   [+ モデルを追加]                                            │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│ ■ specTypes（設計書種別）                                     │
│   ┌────────────────────┬──────────────────────────────┬──┐   │
│   │ 種別                │ 注意事項                      │   │   │
│   ├────────────────────┼──────────────────────────────┼──┤   │
│   │ 設計書              │ 機能仕様が正しく...           │ × │   │
│   │ 要件定義書          │ 要件が漏れなく...             │ × │   │
│   │ ...                 │ ...                           │ × │   │
│   └────────────────────┴──────────────────────────────┴──┘   │
│   [+ 行を追加]                                                │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│                                 [📥 reviewer-config.md をダウンロード] │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## 設計方針

### アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                      index.html                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Generator Engine (汎用)                    │ │
│  │  - JSONスキーマのパース                                 │ │
│  │  - 動的フォーム生成                                     │ │
│  │  - Markdownテンプレート展開                            │ │
│  │  - バリデーション                                       │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↑                                  │
│                    スキーマ定義を読み込み                      │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           Schema Definition (差し替え可能)              │ │
│  │  - 出力タイトル、バージョン                               │ │
│  │  - セクション定義（フィールド、型、デフォルト値）          │ │
│  │  - 出力Markdownテンプレート                             │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### JSONスキーマ定義仕様

HTMLファイル内にJSONとしてスキーマを埋め込む。スキーマを差し替えるだけで別の設定ファイル形式に対応可能。

```javascript
const SCHEMA = {
  // メタ情報
  meta: {
    outputTitle: "設計書-Javaプログラム突合 AIレビュアー 設定ファイル",  // 出力ファイルの見出しタイトル（# で出力）
    outputFileName: "reviewer-config.md",
    version: "v0.4.0"
  },

  // セクション定義（配列順にUIに表示）
  sections: [
    {
      id: "info",
      title: "info",
      description: "設定ファイル情報",
      outputFormat: "list",  // "list" | "table" | "custom"
      fields: [
        {
          id: "version",
          label: "version",
          type: "fixed",  // 固定値（編集不可）
          value: "v0.4.0"
        },
        {
          id: "created_at",
          label: "created_at",
          type: "auto",  // 自動生成（ダウンロード時にISO8601形式で生成）
          generator: "timestamp_iso8601"
        }
      ]
    },
    {
      id: "llm",
      title: "LLMプロバイダー設定",
      outputFormat: "list",
      // 条件分岐（プロバイダー選択に応じてフィールドが変わる）
      conditional: {
        switchField: "provider",
        cases: {
          anthropic: {
            fields: [
              { id: "provider", type: "fixed", value: "anthropic" },
              { id: "apiKey", label: "API Key", type: "password", required: true },
              { id: "maxTokens", label: "Max Tokens", type: "number", default: 16384, required: true },
              {
                id: "models",
                label: "モデル",
                type: "array",
                itemType: "text",
                placeholder: "claude-sonnet-4-5-20250929",
                defaults: ["claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001"]
              }
            ]
          },
          bedrock: {
            fields: [
              { id: "provider", type: "fixed", value: "bedrock" },
              { id: "accessKeyId", label: "Access Key ID", type: "password", required: true },
              { id: "secretAccessKey", label: "Secret Access Key", type: "password", required: true },
              { id: "region", label: "Region", type: "text", default: "ap-northeast-1", required: true },
              { id: "maxTokens", label: "Max Tokens", type: "number", default: 16384, required: true },
              {
                id: "models",
                label: "モデル",
                type: "array",
                itemType: "text",
                placeholder: "global.anthropic.claude-haiku-4-5-20251001-v1:0",
                defaults: ["global.anthropic.claude-haiku-4-5-20251001-v1:0", "global.anthropic.claude-sonnet-4-5-20250929-v1:0"]
              }
            ]
          },
          openai: {
            fields: [
              { id: "provider", type: "fixed", value: "openai" },
              { id: "apiKey", label: "API Key", type: "password", required: true },
              { id: "maxTokens", label: "Max Tokens", type: "number", default: 16384, required: true },
              {
                id: "models",
                label: "モデル",
                type: "array",
                itemType: "text",
                placeholder: "gpt-5.2",
                defaults: [
                  "gpt-5.2",
                  "gpt-5.2-chat-latest",
                  "gpt-5.2-pro",
                  "gpt-5.1",
                  "gpt-4o",
                  "gpt-4o-mini"
                ]
              }
            ]
          }
        }
      }
    },
    {
      id: "specTypes",
      title: "設計書種別",
      outputFormat: "table",
      columns: [
        { id: "type", label: "種別", type: "text", width: "30%" },
        { id: "note", label: "注意事項", type: "text", width: "70%" }
      ],
      defaults: [
        { type: "設計書", note: "機能仕様が正しく実装されているかを確認してください" },
        { type: "要件定義書", note: "要件が漏れなく実装されているかを確認してください" },
        { type: "処理ロジック", note: "処理手順やアルゴリズムが正しく実装されているかを確認してください" },
        { type: "処理フロー", note: "処理の流れが正しく実装されているかを確認してください" },
        { type: "コーディング規約", note: "コードがこの規約に準拠しているかを確認してください" },
        { type: "ネーミングルール", note: "命名規則に従っているかを確認してください" },
        { type: "製造ガイド", note: "このガイドラインに従って実装されているかを確認してください" },
        { type: "設計ガイド", note: "この設計方針に従って実装されているかを確認してください" },
        { type: "設計書とソースのマッピング", note: "このマッピングに基づいて突合を行ってください" }
      ],
      editable: true,  // 行の追加・編集・削除可能
      minRows: 0
    },
    {
      id: "systemPrompts",
      title: "systemPrompts",
      description: "システムプロンプトのプリセット定義",
      outputFormat: "sections",  // 見出し+セクション形式
      itemKey: "name",           // 各アイテムの識別キー（### 見出しに使用）
      fields: [
        { id: "name", label: "プリセット名" },
        { id: "role", label: "役割", rows: 2 },
        { id: "purpose", label: "目的", rows: 6 },
        { id: "format", label: "フォーマット", rows: 4 },
        { id: "notes", label: "注意事項", rows: 6 }
      ],
      defaults: [
        {
          name: "標準レビュープリセット",
          role: "あなたは設計書とプログラムコードを突合し、整合性を検証するレビュアーです。",
          purpose: "設計書の内容がプログラムに正しく実装されているかを検証し、...",
          format: "マークダウン形式で、以下の順に出力してください：...",
          notes: "- メイン設計書の内容について突合してください。..."
        }
      ],
      editable: true,
      minRows: 0
    }
  ]
};
```

### フィールドタイプ

| type | 説明 | 追加プロパティ |
|------|------|---------------|
| `fixed` | 固定値（編集不可、出力時に使用） | `value` |
| `auto` | 自動生成値（ダウンロード時に生成） | `generator` |
| `text` | テキスト入力 | `default`, `placeholder`, `required`, `width` |
| `textarea` | 複数行テキスト入力 | `rows`, `default`, `placeholder`, `required`, `width` |
| `password` | パスワード入力（マスク表示） | `required` |
| `number` | 数値入力 | `default`, `min`, `max`, `required` |
| `select` | セレクトボックス | `options`, `default` |
| `array` | 複数値入力（追加・削除可能） | `itemType`, `defaults`, `placeholder` |

**textareaの補足:**
- `table` フォーマットのテーブルセル内で使用可能（複数行テキストの入力に対応）
- `table` フォーマットでのMarkdown出力時、改行は `<br>` に変換される
- `sections` フォーマットでは改行がそのまま出力される（視認性が高い）
- `rows` プロパティで表示行数を指定（デフォルト: 3）
- 長文の複数行テキストには `sections` フォーマットの使用を推奨

### テーブル列プロパティ

| プロパティ | 説明 | 例 |
|-----------|------|-----|
| `width` | 列の幅（CSS値） | `"20%"`, `"200px"` |

### 自動生成タイプ（generator）

| generator | 説明 | 出力例 |
|-----------|------|--------|
| `timestamp_iso8601` | ISO 8601形式のタイムスタンプ | `2025-01-15T10:30:00+09:00` |

### 出力フォーマット

| outputFormat | 説明 | Markdown出力例 |
|--------------|------|---------------|
| `list` | リスト形式 | `- key: value` |
| `table` | テーブル形式 | `\| col1 \| col2 \|` |
| `sections` | 見出し+セクション形式 | `### 名前`<br>`#### field`<br>`内容...` |

**sectionsの補足:**
- 複数行テキストを含む構造化データに適している
- `itemKey` で指定したフィールドが `###` 見出しとして出力される
- 他のフィールドは `#### フィールドID` の形式で出力される
- UIはアコーディオン形式のカードで表示（展開/折りたたみ可能）

### 拡張性

**バージョンアップ時**: `meta.version` とフィールド定義を更新

**別アプリへの転用時**:
- `SCHEMA` オブジェクト全体を差し替え
- 例: 別アプリ用に `sections` を再定義するだけで対応可能

## 技術要件

- **単一HTMLファイル**で完結（`index.html` 1ファイル）
- 開発環境がない利用者のPC上でも動作可能
- TailwindCSS（CDN経由）を使用してスタイリング
- ブラウザ上で完結、サーバー通信なし

## 機能要件

### 1. 動的フォーム生成
- JSONスキーマに基づいてUIを自動生成
- 条件分岐（`conditional`）に対応（プロバイダー選択で入力欄が切り替わる）
- 配列フィールドの追加・削除
- 数値フィールドの入力サポート

### 2. テーブル編集
- 行の追加・編集・削除
- ドラッグ&ドロップでの並び替え（オプション）

### 3. 自動生成フィールド
- `auto` タイプのフィールドはダウンロード時に自動生成
- `timestamp_iso8601`: 現在時刻をISO 8601形式で出力

### 4. バリデーション
- 必須フィールドチェック
- スキーマ定義に基づく型チェック
- 数値フィールドの範囲チェック（min/max指定時）

### 5. 出力
- 「ダウンロード」ボタンで設定ファイルをダウンロード

## 配置場所

`config-file-generator/index.html`

## 対象バージョン

v0.5.0

## E2E試験項目

### CFG-GEN: 設定ファイルジェネレーターテスト

| # | 試験項目 | 前提条件 | 操作手順 | 期待結果 | 結果 |
|---|---------|---------|---------|---------|------|
| E2E-GEN-001 | 画面表示 | - | /config-file-generator/ にアクセス | 設定ファイルジェネレーター画面が表示される | |
| E2E-GEN-002 | プロバイダー切替（Anthropic） | 画面表示済み | プロバイダーで「Anthropic」を選択 | API Key入力欄が表示される | |
| E2E-GEN-003 | プロバイダー切替（Bedrock） | 画面表示済み | プロバイダーで「Bedrock」を選択 | Access Key ID、Secret Access Key、Region入力欄が表示される | |
| E2E-GEN-004 | プロバイダー切替（OpenAI） | 画面表示済み | プロバイダーで「OpenAI」を選択 | API Key入力欄が表示される | |
| E2E-GEN-005 | モデル追加 | プロバイダー選択済み | 「+ モデルを追加」ボタン押下 | モデル入力欄が追加される | |
| E2E-GEN-006 | モデル削除 | モデルが2つ以上ある | モデルの「×」ボタン押下 | 該当モデルが削除される | |
| E2E-GEN-007 | specTypes行追加 | 画面表示済み | 「+ 行を追加」ボタン押下 | 種別テーブルに新しい行が追加される | |
| E2E-GEN-008 | specTypes行削除 | 種別テーブルに行がある | 行の「×」ボタン押下 | 該当行が削除される | |
| E2E-GEN-009 | specTypes編集 | 種別テーブルに行がある | 種別と注意事項を編集 | 入力内容が反映される | |
| E2E-GEN-010 | systemPromptsプリセット追加 | 画面表示済み | 「+ プリセットを追加」ボタン押下 | 新しいプリセット入力欄が追加される | |
| E2E-GEN-011 | systemPromptsプリセット削除 | プリセットがある | プリセットの「×」ボタン押下 | 該当プリセットが削除される | |
| E2E-GEN-012 | systemPromptsプリセット編集 | プリセットがある | role、purpose、format、notesを編集 | 入力内容が反映される | |
| E2E-GEN-013 | ダウンロード | 必須項目入力済み | 「ダウンロード」ボタン押下 | reviewer-config.mdがダウンロードされ、info、llm、specTypes、systemPromptsセクションが含まれる | |
| E2E-GEN-014 | created_at自動生成 | - | ダウンロードボタン押下 | infoセクションのcreated_atにダウンロード時刻がISO8601形式で設定される | |
| E2E-GEN-015 | 必須項目バリデーション | API Key未入力 | 「ダウンロード」ボタン押下 | エラー表示、ダウンロードされない | |
