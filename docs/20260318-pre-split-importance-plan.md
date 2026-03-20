# 事前重要指定機能 修正計画書

## 概要

分割前に重要なシート・セクションを指定する「事前重要指定」機能を追加する。
事前重要指定セクションと通常セクションで異なる分割設定を適用し、分割品質とレビュー精度を向上させる。

詳細は [pre-split-importance.md](pre-split-importance.md) を参照。

## UX フロー

### 現状のフロー

```
設計書アップロード → Markdown変換
→ 分割モード選択 → 分割プレビュー実行
→ 一覧から重要・除外・要約を手動チェック → レビュー開始
```

### 改善後のフロー

```
設計書アップロード → Markdown変換
→ 「分割」選択時にセクション一覧を取得・表示 → 「事前重要指定」セクションを選択
→ 「事前重要指定」「通常」の分割モード選択 → 分割プレビュー実行
→ 一覧から重要・除外・要約を手動チェック → レビュー開始
```

### UI 変更イメージ（3段階の操作）

1. **事前重要指定**: H2 見出しで自動分割し、セクションごとに「事前重要指定」にチェック
2. **分割プレビュー実行**: 事前重要指定セクションと通常セクションで別々に分割モードを指定し、分割プレビューを実行
3. **「重要」「除外」を再設定**: 分割後のセクションも従来通り重要・要約・除外を選択可

### 変更後の画面イメージ

#### 画面①: 事前重要指定（新規追加エリア）

レビュー方式で「分割」を選択したタイミングで `POST /split/headings` を実行し、セクション一覧を表示する。

- 取得結果はキャッシュし、一括↔分割を切り替えても再取得しない
- 設計書のマークダウンが変更された場合はキャッシュをリセットし、次に「分割」を選んだ時に再取得する

```
┌─────────────────────────────────────────────────────────────────┐
│ 分割設定                                                        │
│ 設計書やプログラムが大きくAIのトークン上限を超える場合、            │
│ 分割してレビューできます。                                        │
│                                                                 │
│ レビュー方式:  ○ 一括   ◉ 分割  ← 分割を選んだ時に見出し取得      │
│                                                                 │
│ ▼ 分割オプション                                                 │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 事前重要指定                               【新規追加エリア】 │ │
│ │                                                             │ │
│ │ 設計書の見出し（H2）単位でセクションを表示しています。         │ │
│ │ 事前重要指定するセクションにチェックを入れてください。         │ │
│ │                                                             │ │
│ │  事前重要                                                    │ │
│ │  指定    #   セクション名                  行範囲   推定文字数 │ │
│ │ ┌─────┬───┬──────────────────────────┬────────┬──────────┐  │ │
│ │ │ ☐   │ 1 │ 概要                     │ L1-L5  │   ~104   │  │ │
│ │ │ ☐   │ 2 │ 業務フロー               │ L6-L7  │    ~41   │  │ │
│ │ │ ☐   │ 3 │ 機能一覧                 │ L8-L48 │   ~961   │  │ │
│ │ │ ☐   │ 4 │ 画面設計                 │ L47-L78│   ~521   │  │ │
│ │ │ ☑   │ 5 │ 変更履歴                 │ L79-L110│ ~1,084  │  │ │
│ │ │ ☑   │ 6 │ 常駐処理設計書           │L111-L2357│~69,273 │  │ │
│ │ │ ☐   │ 7 │ 入力チェック             │L2358-L2382│  ~967  │  │ │
│ │ │ ☐   │ 8 │ バッチ転送単位数_消費税   │L2383-L2729│~23,327 │  │ │
│ │ │ ☐   │ 9 │ 常駐処理設計書（記述変更）│L2730-L2763│ ~1,370 │  │ │
│ │ │ ☐   │10 │ 入力チェック（記述変更）  │L2764-L2797│ ~1,359 │  │ │
│ │ └─────┴───┴──────────────────────────┴────────┴──────────┘  │ │
│ └─────────────────────────────────────────────────────────────┘ │
```

#### 画面②: 分割プレビュー実行（分割設定の変更）

従来の1つの分割設定を、事前重要指定セクション用と通常セクション用の2つに分離する。

```
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 設計書 — 事前重要指定セクション              【新規追加エリア】│ │
│ │                                                             │ │
│ │ 分割モード:                                                  │ │
│ │  ○ 見出し   ○ NLP   ◉ AI（推奨）  見出しに加えて…           │ │
│ │                                                             │ │
│ │ 分割時の注意事項（AIへの指示・任意）                           │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ 例: Mermaidブロックの途中では分割しない、項番単位で分割する │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ │                                                             │ │
│ │ 見出しレベル:                                                │ │
│ │  ◉ H2(##)まで（推奨）  ○ H3(###)まで  ○ H4(####)まで       │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 設計書 — 通常セクション                   【従来エリアを改名】│ │
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
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ プログラム                                     【変更なし】  │ │
│ │                                                             │ │
│ │ 対応言語: Python (.py) / Java (.java)                        │ │
│ │ 対応ファイル: KazeiUsekitoSoshinService.java                 │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ [ 分割プレビュー ]                                               │
│ ※ 設計書が大きい場合は、処理に時間が掛かったり、                  │
│   タイムアウトや制限等でエラーになる可能性があります。              │
```

#### 画面③: 分割結果一覧（「重要」「除外」を再設定）

分割後の結果テーブルに `pre_important` フラグに基づく自動設定が反映される。
ユーザーは手動で重要・要約・除外を変更可能。

```
│ ■ 設計書: 24 パート                                             │
│                                                                 │
│ 重要 要約 除外  #  セクション名                   行範囲  推定トークン│
│ ┌──┬──┬──┬───┬─────────────────────────────┬────────┬──────────┐│
│ │☑ │☐ │☐ │ 15│ 常駐処理設計書              │L111-   │  ~69,273 ││
│ │  │  │  │   │ ▶ 内容を表示                │L2357   │  ← 重要ON││
│ │☐ │☐ │☐ │ 16│ 常駐処理設計書: part-1      │L111-L417│  ~3,448 ││
│ │  │  │  │   │ ▶ 内容を表示                │        │          ││
│ │☐ │☐ │☐ │ 17│ 常駐処理設計書: part-2      │L418-L976│  ~8,911 ││
│ │☐ │☐ │☐ │ 18│ 常駐処理設計書: part-3      │L977-   │ ~20,482 ││
│ │  │  │  │   │                             │L1411   │          ││
│ │☐ │☐ │☐ │ 19│ 常駐処理設計書: part-4      │L1412-  │ ~25,050 ││
│ │  │  │  │   │                             │L2054   │          ││
│ │☐ │☐ │☐ │ 20│ 常駐処理設計書: part-5      │L2055-  │ ~11,381 ││
│ │  │  │  │   │                             │L2357   │          ││
│ │☑ │☐ │☐ │ 21│ 入力チェック               │L2358-  │    ~967 ││
│ │  │  │  │   │                             │L2382   │  ← 重要ON││
│ │☐ │☐ │☐ │ 22│ 入力チェック: part-1        │L2358-  │    ~323 ││
│ │  │  │  │   │                             │L2366   │          ││
│ │☐ │☐ │☐ │ 23│ 入力チェック: part-2        │L2367-  │    ~278 ││
│ │  │  │  │   │                             │L2373   │          ││
│ │☐ │☐ │☐ │ 24│ 入力チェック: part-3        │L2374-  │    ~364 ││
│ │  │  │  │   │                             │L2380   │          ││
│ └──┴──┴──┴───┴─────────────────────────────┴────────┴──────────┘│
│                                                                 │
│ ※ 事前重要指定セクションのうち、サブスプリットされていない          │
│   パート（#15, #21）は自動的に重要=ON が設定されています           │
│   （手動変更可）                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 画面変更のポイント

| 変更箇所 | 変更前（v0.9.1） | 変更後（v0.9.2） |
|---|---|---|
| 事前重要指定 | なし | H2 見出し一覧 + 事前重要指定チェックボックス（新規追加） |
| 見出し取得タイミング | — | 「分割」選択時に取得、結果をキャッシュ（MD変更でリセット） |
| 設計書の分割設定 | 1つの分割設定 | 「事前重要指定セクション」「通常セクション」の2つに分離 |
| プログラムの分割設定 | そのまま | 変更なし |
| 分割結果テーブル | 重要・要約・除外を全て手動設定 | 事前重要指定のサブスプリットなしパートのみ重要=ON を自動設定（手動変更可） |

---

## 前提

- 現在の実装: `versions/v0.9.1`
- `versions/v0.9.1` を丸ごとコピーして `versions/v0.9.2` を作成し、v0.9.2 上で修正を行う
- md2map の修正は別計画書で実施: [20260320-section-overrides-plan.md](../md2map/docs/20260320-section-overrides-plan.md)

---

## Step 0: v0.9.2 ディレクトリの作成

- `versions/v0.9.1` を `versions/v0.9.2` にコピー
- v0.9.2 の spec.md にバージョン番号を反映

---

## Step 1: md2map — 見出し一覧取得 / セクション単位オーバーライド

md2map 側の修正は別計画書を参照: [20260320-section-overrides-plan.md](../md2map/docs/20260320-section-overrides-plan.md)

本計画で利用する md2map の機能:

| 機能 | 概要 |
|---|---|
| `extract_headings(content, max_depth)` | 見出し一覧を取得。`[{ title, level, start_line, end_line, estimated_chars }]` を返す |
| `section_overrides` | セクション単位で分割設定をオーバーライド。フラットなリスト形式 `[{"start_line": N, "split_mode": "ai", ...}]`。デフォルト設定はコンストラクタ引数で渡す |

md2map 自体は「事前重要指定」の概念を持たない。
バックエンドが「事前重要指定セクション」を md2map の `section_overrides` に変換し、結果に `pre_important` フラグを付与する。

### md2map の呼び出しイメージ

```python
# 見出し一覧取得
parser = MarkdownParser()
headings = parser.extract_headings(content, max_depth=2)

# 分割実行（通常設定をコンストラクタ引数、事前重要指定セクションを section_overrides で渡す）
parser = MarkdownParser(
    split_mode=normal_split_settings.split_mode,       # 通常セクションのデフォルト
    max_subsections=normal_split_settings.max_subsections,
    ai_prompt_extra_notes=normal_split_settings.split_instructions or "",
    section_overrides=[                                 # 事前重要指定セクションのみ上書き
        {
            "start_line": start_line,
            "split_mode": pre_important_split_settings.split_mode,
            "max_subsections": pre_important_split_settings.max_subsections,
            "ai_prompt_extra_notes": pre_important_split_settings.split_instructions or "",
        }
        for start_line in pre_important_sections
    ],
)
sections, warnings = parser.parse(file_path, max_depth=2)
```

---

## Step 2: バックエンド — API スキーマとエンドポイントの修正

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.2/backend/app/models/schemas.py` | `SplitMarkdownRequest` に `pre_important_sections` と分割設定を追加、`HeadingsRequest/Response` を追加 |
| `versions/v0.9.2/backend/app/routers/split.py` | 見出し一覧取得エンドポイント `POST /split/headings` を追加、`POST /split/markdown` で `pre_important_sections` を md2map の `section_overrides` に変換して渡す |
| `versions/v0.9.2/backend/tests/` | 新規・既存エンドポイントのテストを追加 |

### 新規エンドポイント: POST /split/headings

md2map の `extract_headings()` を呼び出し、結果をそのまま返す。

```
リクエスト: { markdown: string }
レスポンス: { headings: [{ title, level, start_line, end_line, estimated_chars }] }
```

### 既存エンドポイント修正: POST /split/markdown

リクエストに追加：

```
pre_important_sections: [79, 111]    // start_line のリスト
pre_important_split_settings: {
  split_mode: "heading" | "nlp" | "ai",
  heading_level: 2 | 3 | 4,
  split_instructions: string | null,
  max_subsections: number
}
normal_split_settings: {
  split_mode: "heading" | "nlp" | "ai",
  heading_level: 2 | 3 | 4,
  split_instructions: string | null,
  max_subsections: number
}
```

- `pre_important_sections`: 事前重要指定セクションの `start_line` リスト
- `pre_important_split_settings`: 事前重要指定セクション向けの分割設定
- `normal_split_settings`: 通常セクション向けの分割設定

### バックエンドの責務: section_overrides への変換

バックエンドが `pre_important_sections` + 2つの分割設定を md2map の API に変換する。
通常セクションの設定はコンストラクタ引数として渡し、事前重要指定セクションの設定は `section_overrides`（フラットなリスト）として渡す。

```python
# バックエンド側の変換ロジック
parser = MarkdownParser(
    # 通常セクションの設定 → コンストラクタ引数（= 全セクションのデフォルト）
    split_mode=normal_split_settings.split_mode,
    max_subsections=normal_split_settings.max_subsections,
    ai_prompt_extra_notes=normal_split_settings.split_instructions or "",
    # 事前重要指定セクションの設定 → section_overrides（特定セクションのみ上書き）
    section_overrides=[
        {
            "start_line": start_line,
            "split_mode": pre_important_split_settings.split_mode,
            "max_subsections": pre_important_split_settings.max_subsections,
            "ai_prompt_extra_notes": pre_important_split_settings.split_instructions or "",
        }
        for start_line in pre_important_sections
    ],
)
```

### バックエンドの責務: pre_important フラグの付与

md2map の結果には `pre_important` フラグは含まれない。
バックエンドが `pre_important_sections`（start_line リスト）と md2map の結果を照合し、該当セクションの DocumentPart に `pre_important: true` を付与する。

レスポンスの DocumentPart に `pre_important: bool` を追加。

---

## Step 3: フロントエンド — 事前重要指定 UI の追加

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.2/frontend/src/features/reviewer/types/index.ts` | `PreImportantSection` 型、`SplitSettings` 型、`DocumentPart` に `pre_important` フィールドを追加 |
| `versions/v0.9.2/frontend/src/features/reviewer/services/api.ts` | `fetchHeadings()` API 呼び出しを追加、`splitMarkdown()` に `pre_important_sections` と分割設定を追加 |
| `versions/v0.9.2/frontend/src/features/reviewer/components/PreImportantPanel.tsx` | **新規** — 事前重要指定パネル（セクション一覧 + チェックボックス） |
| `versions/v0.9.2/frontend/src/features/reviewer/components/SplitSettingsSection.tsx` | PreImportantPanel を組み込み、事前重要指定/通常の分割設定を個別に表示 |
| `versions/v0.9.2/frontend/src/features/reviewer/hooks/useSplitSettings.ts` | 事前重要指定の状態管理、事前重要指定/通常の分割設定の個別管理を追加 |
| `versions/v0.9.2/frontend/src/__tests__/` | 新規コンポーネント・フックのテストを追加 |

### UI 仕様

#### 1. 事前重要指定

- レビュー方式で「分割」を選択したタイミングで `POST /split/headings` を実行し、H2 見出し一覧を取得・表示
  - 取得結果はキャッシュし、一括↔分割を切り替えても再取得しない
  - 設計書のマークダウンが変更された場合はキャッシュをリセットし、次に「分割」を選んだ時に再取得する
- 各見出しにチェックボックスを配置
  - ☑ ON → 事前重要指定セクション
  - ☐ OFF（デフォルト）→ 通常セクション

#### 2. 分割プレビュー実行

- 事前重要指定セクションと通常セクションで**別々に**分割モードを指定
  - 分割モード: 見出し / NLP / AI（推奨）
  - 見出しレベル: H2(##)まで（推奨）/ H3(###)まで / H4(####)まで
  - 分割時の注意事項（AIへの指示・任意）
- 分割プレビューボタンで `pre_important_sections`（start_line リスト）、`pre_important_split_settings`、`normal_split_settings` を API に送信

#### 3. 「重要」「除外」を再設定

- 分割後のセクションも従来通り重要・要約・除外を選択可能

### 分割後の自動設定

事前重要指定セクションから生成された DocumentPart のうち、サブスプリットされていないパートのみ以下を自動セット（手動変更可能）：
- 重要パート: ON

---

## Step 4: フロントエンド — 分割後設定の自動反映

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.2/frontend/src/features/reviewer/components/SplitSettingsSection.tsx` | 分割結果の `pre_important` フラグに基づき、サブスプリットなしパートの重要チェック状態を自動セット |
| `versions/v0.9.2/frontend/src/features/reviewer/hooks/useSplitSettings.ts` | 分割結果受信時に自動設定ロジックを追加、見出し一覧のキャッシュ管理（MD変更時リセット）を追加 |

---

## Step 5: ドキュメント更新

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.2/spec.md` | 事前重要指定機能に関する仕様を追記 |
| `docs/split-review.md` | 事前重要指定機能の説明を追記 |

### spec.md の更新箇所

| セクション | 更新内容 |
|---|---|
| 2.7.2 レビュー方式 | 「分割」選択時に見出し一覧を取得する動作を追記 |
| 2.7.3 分割オプション | 事前重要指定パネルの説明を追加。設計書分割オプションを「事前重要指定セクション」「通常セクション」の2系統に分離した旨を追記 |
| 2.7.5 分割プレビュー | 事前重要指定セクションの `pre_important` フラグ付与と、サブスプリットなしパートの重要=ON 自動設定を追記 |
| 4.2 API詳細 | `POST /api/split/headings` エンドポイントを追加。`POST /api/split/markdown` に `pre_important_sections`、`pre_important_split_settings`、`normal_split_settings` パラメータを追記 |
| 3.1 メイン画面 | 分割設定エリアに事前重要指定パネルと2系統の分割設定UIを追記 |

### split-review.md の更新箇所

| セクション | 更新内容 |
|---|---|
| 3. 分割設定 | 「3.5 事前重要指定」セクションを追加。見出し一覧取得、セクション選択、分割設定の2系統化、`pre_important` フラグの自動設定について記載 |
| 8. エンドツーエンドの流れ | フロー図に事前重要指定のステップを追加 |

---

## 修正順序と依存関係

```
Step 0: v0.9.2 作成
  ↓
Step 1: md2map 見出し一覧取得 / セクション単位オーバーライド
         → 別計画書: md2map/docs/20260320-section-overrides-plan.md
  ↓
Step 2: バックエンド API 修正（md2map の機能を利用、pre_important の変換・付与）
  ↓
Step 3: フロントエンド 事前重要指定 UI（Step 2 の API を利用）
  ↓
Step 4: フロントエンド 分割後自動反映（Step 3 の UI 状態を利用）
  ↓
Step 5: ドキュメント更新（spec.md、split-review.md）
```

---

## 影響範囲

| 対象 | 影響 |
|---|---|
| md2map | 見出し一覧取得の追加、セクション単位オーバーライド追加（[別計画書](../md2map/docs/20260320-section-overrides-plan.md)） |
| バックエンド | 新規エンドポイント追加、既存エンドポイントのリクエスト/レスポンス拡張、`pre_important` の変換・付与 |
| フロントエンド | 新規 UI コンポーネント追加、分割設定フローの拡張 |
| ドキュメント | `spec.md` に事前重要指定の仕様追記、`split-review.md` に機能説明追記 |
| code2map | 変更なし |
| Phase 1〜3（構造マッチング・グループレビュー・統合） | MAP.json の `pre_important` をヒントとして活用可能（本計画では任意） |

---

## 完了チェックリスト

### Step 0: v0.9.2 作成

- [x] `versions/v0.9.1` を `versions/v0.9.2` にコピー
- [x] v0.9.2 の全バージョン番号を更新
- [x] インフラ設定（Docker/Nginx/PM2）に v0.9.2 を追加
- [x] `latest` シンボリックリンクを v0.9.2 に更新
- [x] 全バージョンの `useVersions.ts` に v0.9.2 を追加

### Step 1: md2map 見出し一覧取得 / セクション単位オーバーライド

- [x] md2map 側の計画書作成（[20260320-section-overrides-plan.md](../md2map/docs/20260320-section-overrides-plan.md)）
- [ ] md2map の `extract_headings()` 実装完了・テスト通過
- [ ] md2map の `section_overrides` 実装完了・テスト通過
- [ ] md2map が main にマージされ、subtree で取り込み済み
- [ ] `pyproject.toml` の md2map 参照を `branch = "main"` に戻す

### Step 2: バックエンド API 修正

- [ ] `HeadingsRequest` / `HeadingsResponse` スキーマの追加
- [ ] `POST /api/split/headings` エンドポイントの実装
- [ ] `SplitMarkdownRequest` に `pre_important_sections` / `pre_important_split_settings` / `normal_split_settings` を追加
- [ ] `POST /api/split/markdown` で `section_overrides` への変換ロジックを実装
- [ ] `POST /api/split/markdown` のレスポンスに `pre_important` フラグを付与するロジックを実装
- [ ] バックエンドテスト追加・全テスト通過

### Step 3: フロントエンド 事前重要指定 UI

- [ ] `PreImportantPanel.tsx` コンポーネントの実装
- [ ] `SplitSettingsSection.tsx` に事前重要指定パネルと2系統の分割設定を組み込み
- [ ] `useSplitSettings.ts` に事前重要指定の状態管理を追加
- [ ] `api.ts` に `fetchHeadings()` と分割設定パラメータを追加
- [ ] 型定義（`types/index.ts`）の更新
- [ ] フロントエンドテスト追加・全テスト通過

### Step 4: フロントエンド 分割後自動反映

- [ ] 分割結果受信時の `pre_important` フラグに基づく重要=ON 自動設定ロジック
- [ ] 見出し一覧のキャッシュ管理（MD変更時リセット）
- [ ] フロントエンドテスト追加・全テスト通過

### Step 5: ドキュメント更新

- [ ] `versions/v0.9.2/spec.md` に事前重要指定の仕様を追記
- [ ] `docs/split-review.md` に事前重要指定の説明を追記

### 最終確認

- [ ] 全バックエンドテスト通過
- [ ] 全フロントエンドテスト通過
- [ ] 手動動作確認（事前重要指定 → 分割プレビュー → 重要=ON 自動設定の一連のフロー）
