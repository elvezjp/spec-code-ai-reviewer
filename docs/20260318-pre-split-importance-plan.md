# 事前重要指定機能 修正計画書

## 概要

分割前に重要なシート・セクションを指定する「事前重要指定」機能を追加する。
事前重要指定セクションと通常セクションで異なる分割設定を適用し、分割品質とレビュー精度を向上させる。

詳細は [pre-split-importance.md](pre-split-importance.md) を参照。

## 前提

- 現在の実装: `versions/v0.9.1`
- `versions/v0.9.1` を丸ごとコピーして `versions/v0.9.2` を作成し、v0.9.2 上で修正を行う
- md2map の修正は `md2map/` ディレクトリで行う

---

## Step 0: v0.9.2 ディレクトリの作成

- `versions/v0.9.1` を `versions/v0.9.2` にコピー
- v0.9.2 の spec.md にバージョン番号を反映

---

## Step 1: md2map — 見出し一覧取得機能の追加

分割実行前に見出し一覧だけを軽量に取得する機能を追加する。

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `md2map/md2map/parsers/markdown_parser.py` | 見出し一覧取得メソッド `extract_headings()` を追加 |
| `md2map/md2map/cli.py` | `headings` サブコマンドを追加 |
| `md2map/tests/` | 見出し一覧取得のテストを追加 |

### 入出力

```
入力:  markdown テキスト
出力:  [{ title, level, start_line, end_line, estimated_chars }]
```

- 既存の見出し解析ロジック（正規表現による ATX 見出し抽出）を流用
- LLM 不要、高速処理

---

## Step 2: md2map — セクション単位の分割設定対応

`pre_important_sections` パラメータを受け取り、セクションごとに分割動作を切り替える。

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `md2map/md2map/parsers/markdown_parser.py` | `pre_important_sections` パラメータを受け取り、セクション単位で分割動作を切り替え |
| `md2map/md2map/models/section.py` | Section に `pre_important: bool` フィールドを追加 |
| `md2map/md2map/generators/map_generator.py` | MAP.json に `pre_important` フィールドを出力 |
| `md2map/md2map/cli.py` | `--pre-important-sections` オプションを追加 |
| `md2map/tests/` | セクション単位分割のテストを追加 |

### 分割動作

| セクション種別 | 分割動作 | サブスプリット |
|---|---|---|
| 事前重要指定 + split: **no_split** | 分割しない | 実行しない |
| 事前重要指定 + split: **fine** | 通常分割 | 上限を引き上げ（例: 10） |
| 通常セクション | 通常分割 | 一律の max_subsections |

### MAP.json の変更

```json
{ "id": "MD1", "section": "API仕様", "level": 2, "path": "...",
  "pre_important": true, ... }
```

---

## Step 3: バックエンド — API スキーマとエンドポイントの修正

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.2/backend/app/models/schemas.py` | `SplitMarkdownRequest` に `pre_important_sections` を追加、`HeadingsRequest/Response` を追加 |
| `versions/v0.9.2/backend/app/routers/split.py` | 見出し一覧取得エンドポイント `POST /split/headings` を追加、`POST /split/markdown` で `pre_important_sections` を md2map に渡す |
| `versions/v0.9.2/backend/tests/` | 新規・既存エンドポイントのテストを追加 |

### 新規エンドポイント: POST /split/headings

```
リクエスト: { markdown: string }
レスポンス: { headings: [{ title, level, start_line, end_line, estimated_chars }] }
```

### 既存エンドポイント修正: POST /split/markdown

リクエストに追加：

```
pre_important_sections: [
  { heading: "1. API仕様", split: "no_split" },
  { heading: "2. DB設計",  split: "fine" }
]
```

レスポンスの DocumentPart に `pre_important: bool` を追加。

---

## Step 4: フロントエンド — 事前重要指定 UI の追加

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.2/frontend/src/features/reviewer/types/index.ts` | `PreImportantSection` 型、`DocumentPart` に `pre_important` フィールドを追加 |
| `versions/v0.9.2/frontend/src/features/reviewer/services/api.ts` | `fetchHeadings()` API 呼び出しを追加、`splitMarkdown()` に `pre_important_sections` を追加 |
| `versions/v0.9.2/frontend/src/features/reviewer/components/PreImportantPanel.tsx` | **新規** — 事前重要指定パネルコンポーネント |
| `versions/v0.9.2/frontend/src/features/reviewer/components/SplitSettingsSection.tsx` | PreImportantPanel を組み込み |
| `versions/v0.9.2/frontend/src/features/reviewer/hooks/useSplitSettings.ts` | 事前重要指定の状態管理を追加 |
| `versions/v0.9.2/frontend/src/__tests__/` | 新規コンポーネント・フックのテストを追加 |

### UI 仕様

1. 設計書アップロード後、`POST /split/headings` で見出し一覧を取得
2. 見出し一覧を表示し、各見出しにチェックボックスを配置
   - ☑ ON → 事前重要指定セクション
   - ☐ OFF（デフォルト）→ 通常セクション
3. 事前重要指定セクションには追加オプション：「分割しない」/「細かく分割」
4. 分割実行時に `pre_important_sections` を API に送信

### 分割後の自動設定

事前重要指定セクションから生成された DocumentPart は以下を自動セット：
- 重要パート: ON
- 要約: OFF（要約禁止）

---

## Step 5: フロントエンド — 分割後設定の自動反映

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.2/frontend/src/features/reviewer/components/SplitSettingsSection.tsx` | 分割結果の `pre_important` フラグに基づき、重要・要約のチェック状態を自動セット |
| `versions/v0.9.2/frontend/src/features/reviewer/hooks/useSplitSettings.ts` | 分割結果受信時に自動設定ロジックを追加 |

---

## 修正順序と依存関係

```
Step 0: v0.9.2 作成
  ↓
Step 1: md2map 見出し一覧取得
  ↓
Step 2: md2map セクション単位分割
  ↓
Step 3: バックエンド API 修正（Step 1, 2 の md2map を利用）
  ↓
Step 4: フロントエンド 事前重要指定 UI（Step 3 の API を利用）
  ↓
Step 5: フロントエンド 分割後自動反映（Step 4 の UI 状態を利用）
```

---

## 影響範囲

| 対象 | 影響 |
|---|---|
| md2map | 見出し一覧取得の追加、セクション単位分割設定の追加、MAP.json フィールド追加 |
| バックエンド | 新規エンドポイント追加、既存エンドポイントのリクエスト/レスポンス拡張 |
| フロントエンド | 新規 UI コンポーネント追加、分割設定フローの拡張 |
| code2map | 変更なし |
| Phase 1〜3（構造マッチング・グループレビュー・統合） | MAP.json の `pre_important` をヒントとして活用可能（本計画では任意） |
