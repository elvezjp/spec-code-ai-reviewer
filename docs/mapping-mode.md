# マッピングモード機能の詳細

## 全体像

v0.9.0 で追加された「マッピングモード」は、設計書の各項目がソースコードのどこで実装されているかを特定し、**トレーサビリティ** として可視化する機能です。

既存の「突合モード」が **整合性検証**（差異・問題点の発見）に焦点を当てるのに対し、マッピングモードは **対応付け**（設計項目 → 実装箇所の特定）に焦点を当てます。

| 観点 | 突合モード | マッピングモード |
|------|-----------|----------------|
| 目的 | 設計書とコードの整合性検証 | 設計項目と実装箇所の対応付け |
| 出力形式 | Markdown レポート | JSON（構造化データ） |
| 簡易判定 | 不整合キーワード検索（ng/warning/ok） | カバレッジ率による判定 |
| 構造マップ | 使用しない（`useStructureMap=false`） | 使用する（`useStructureMap=true`） |
| プリセット | 突合用 8種 | マッピング用 3種 |

---

## 1. モード切り替え

**ファイル**: [ModeSelector.tsx](../versions/v0.9.0/frontend/src/features/reviewer/components/ModeSelector.tsx)

画面上部のタブUIでモードを切り替えます。選択中のモードは `localStorage` に保存され、次回アクセス時に復元されます。

```
┌─────────────────────┬─────────────────────┐
│    突合モード        │   マッピングモード    │
│ 設計書とコードの     │ 設計項目と実装箇所   │
│ 整合性を検証        │ を対応付け          │
└─────────────────────┴─────────────────────┘
```

モード切り替え時に連動して変わるもの:

| 項目 | 切り替え内容 |
|------|-------------|
| プリセット一覧 | 突合用 8種 ↔ マッピング用 3種 |
| デフォルトプリセット | `standard-review` ↔ `standard-mapping` |
| `useStructureMap` | `false` ↔ `true` |
| ZIPファイル名 | `review-result.md` ↔ `mapping-result.md` |

---

## 2. 構造マップ（MAP.json）の活用

**ファイル**: [useStructureMap.ts](../versions/v0.9.0/frontend/src/features/reviewer/hooks/useStructureMap.ts)

マッピングモードでは `useStructureMap=true` がデフォルトとなり、AIに構造情報（MAP.json）を提供します。

### MAP.json の内容

| 種類 | ツール | ID形式 | 含まれる情報 |
|------|--------|--------|-------------|
| 設計書 MAP.json | md2map | MD1, MD2, ... | セクション名、階層パス、行範囲、ワード数 |
| コード MAP.json | code2map | CD1, CD2, ... | シンボル名、種別（class/method/function）、行範囲 |

### 生成タイミング

構造マップは **レビュー実行開始時** に前処理として生成されます。分割プレビューで既に生成済みの側はスキップします。

```
レビュー実行ボタン押下
    ↓
useStructureMap = true ?
    ├─ YES → 構造マップ生成ステップ
    │         ├─ 設計書 MAP.json（未生成なら /api/split/markdown で生成）
    │         └─ コード MAP.json（未生成なら /api/split/code で生成）
    │         → StructureMapInfo として保持
    └─ NO  → スキップ（突合モードのデフォルト動作）
    ↓
AI呼び出し（StructureMapInfo をリクエストに含める）
```

### useStructureMap フラグの制御範囲

| 制御対象 | true | false |
|----------|------|-------|
| 構造マップ生成 | 生成する（既存分はスキップ） | 生成しない |
| プロンプトへの組み込み | 構造マップセクションを含める | 含めない |
| APIリクエストの structureMap | MAP.json を送信 | 送信しない |

---

## 3. マッピング用プリセット

**ファイル**: [presetCatalog.ts](../versions/v0.9.0/frontend/src/core/data/presetCatalog.ts)

マッピングモードでは専用のプリセット 3種が表示されます。

| プリセットID | 名前 | 用途 |
|-------------|------|------|
| `standard-mapping` | 標準マッピングプリセット | 汎用的な設計項目 ↔ 実装箇所の対応付け |
| `api-mapping` | API エンドポイントマッピング | API仕様 ↔ コントローラー/ルーター実装 |
| `database-mapping` | データベーススキーママッピング | テーブル定義 ↔ モデル/エンティティ実装 |

各プリセットは **JSON 出力形式** を `systemPrompt.format` で指定しており、AIの応答を構造化データとして受け取ります。モードに応じたプリセット一覧の取得やデフォルトプリセットIDの取得はヘルパー関数で行います。

---

## 4. プロンプトの差異

**ファイル**:
- [prompt_builder.py](../versions/v0.9.0/backend/app/services/prompt_builder.py) — 一括レビュー時のユーザーメッセージ構築、構造マップセクション生成
- [review.py](../versions/v0.9.0/backend/app/routers/review.py) — 分割レビュー時のシステムプロンプト定数、各フェーズのプロンプト構築

### 4.1 一括レビュー時（`/api/review`）

ユーザーメッセージがモードに応じて変わります。

**変わる部分**:

| 要素 | 突合モード | マッピングモード |
|------|-----------|----------------|
| 冒頭の一文 | 「以下の設計書とプログラムを突合レビューしてください。」 | 「以下の設計書とソースコードについて、設計書の各項目がどこで実装されているかマッピングしてください。」 |
| 構造マップセクション | 付加しない | JSONコードブロックを末尾に付加（後述） |

**変わらない部分**:

- レビュー対象一覧（設計書・プログラムのファイルリスト）
- 設計書詳細（種別・役割・本文）
- プログラム詳細（ファイル名・行番号付きコード）

出力形式の指定（Markdown / JSON）はユーザーメッセージではなく、**プリセットのシステムプロンプト**（`format` フィールド）で制御されます。

**構造マップセクションの形式**:

`useStructureMap=true` かつ `structureMap` がある場合、ユーザーメッセージの末尾に以下の形式で付加されます。設計書の各セクション（ID・セクション名・階層パス・行範囲）とコードの各シンボル（ID・シンボル名・種別・行範囲）をJSON形式でまとめたものです。

```json
{
  "documentMap": [
    { "id": "MD1", "section": "概要", "path": "概要", "lines": "L1-L50" },
    { "id": "MD2", "section": "ユーザー管理", "path": "機能要件 > ユーザー管理", "lines": "L51-L200" }
  ],
  "codeMaps": [
    {
      "filename": "UserService.java",
      "entries": [
        { "id": "CD1", "symbol": "UserService", "type": "class", "lines": "L1-L250" },
        { "id": "CD2", "symbol": "UserService#createUser", "type": "method", "lines": "L45-L80" }
      ]
    }
  ]
}
```

### 4.2 分割レビュー時（3フェーズ）

分割レビューのシステムプロンプトは `role` / `purpose` / `format` / `notes` の4要素で構成されます。`role` / `purpose` / `format` がモード別に切り替わります。

#### フェーズ1: 構造マッチング（`POST /api/review/structure-matching`）

| 要素 | 突合モード | マッピングモード |
|------|-----------|----------------|
| role | 「設計書とソースコードの構造を分析する専門家」 | 「設計書とソースコードのマッピングを行う専門家」 |
| purpose | 「関連性の高い設計書セクションとコードシンボルをグループにまとめる」 | 「設計書の各項目がどのコード要素で実装されているかを推定してグループにまとめる」 |
| format | （共通）JSON形式でグループを出力 | （共通） |
| notes | （共通）JSON形式のみで応答、MAP.jsonのIDをそのまま使用 | （共通） |

ユーザーメッセージには設計書・コードの INDEX.md + MAP.json を渡します（モード共通）。

#### フェーズ2: グループレビュー（`POST /api/review/group`）

| 要素 | 突合モード | マッピングモード |
|------|-----------|----------------|
| role | 「設計書とソースコードの整合性をレビューする専門家」 | 「設計書とソースコードのマッピングを行う専門家」 |
| purpose | 「設計書の記述とコード実装の整合性を確認し、指摘事項を報告する」 | 「設計書の各項目がコードのどこで実装されているかを特定する」 |
| format | 「サマリー、突合結果一覧（テーブル）、詳細」 | 「マッピングサマリー、マッピング一覧（テーブル）、未マッピング項目」 |

ユーザーメッセージにはグループ名・ID + 設計書内容 + コード内容を渡します。`useStructureMap=true` かつ `structureMap` がある場合は「構造マップ（参考情報）」セクションをJSONコードブロックで挿入します。

#### フェーズ3: 結果統合（`POST /api/review/integrate`）

| 要素 | 突合モード | マッピングモード |
|------|-----------|----------------|
| role | 「レビュー結果を統合するエキスパート」 | 「マッピング結果を統合するエキスパート」 |
| purpose | 「最終的なレビューレポートをMarkdown形式で生成する」 | 「最終的なマッピングレポートをMarkdown形式で生成する」 |
| format | 「Markdown形式のレビューレポートを出力」 | 「Markdown形式のマッピングレポートを出力。全体のカバレッジ率を含める」 |
| 結果ラベル | 「グループレビュー結果」 | 「グループマッピング結果」 |

ユーザーメッセージには構造マッチング結果 + 全グループのレビュー結果を渡します。`useStructureMap=true` かつ `structureMap` がある場合は「全体構造マップ（参考情報）」セクションを先頭に挿入します。

### 4.3 ユーザー指定プロンプトとの合成

各フェーズで、ユーザーがプリセットやカスタム編集で `systemPrompt` を指定している場合の優先ルール:

| 要素 | ユーザー指定あり | ユーザー指定なし |
|------|----------------|----------------|
| role | ユーザー指定を採用 | モード別のフォールバック定数を使用 |
| purpose | ユーザー指定をコードブロックで引用し、フェーズ固有の指示を付加 | モード別のフォールバック定数を使用 |
| format | ユーザー指定を採用 | モード別のフォールバック定数を使用 |
| notes | フェーズ固有の注意事項 + ユーザー指定を追記 | フェーズ固有の注意事項のみ |

---

## 5. JSON 出力形式

**ファイル**: [types/index.ts](../versions/v0.9.0/frontend/src/features/reviewer/types/index.ts)

マッピングモードではAIの応答を JSON 形式で受け取り、フロントエンドで構造化表示します。

### レスポンス構造

AIは設計書ファイルごとにマッピング項目の配列を返します。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `files` | 配列 | 設計書ファイルごとのマッピング結果 |
| `files[].designFile` | 文字列 | 設計書ファイル名 |
| `files[].items` | 配列 | マッピング項目一覧（マッピング済み + 未マッピング混在） |
| `files[].items[].designItem` | 文字列 | 設計書項目（見出し番号・項目名） |
| `files[].items[].implementationElement` | 文字列 | 実装要素（クラス名、関数名等）。未マッピング時は `"-"` |
| `files[].items[].implementationLocation` | 文字列 | 実装箇所（ファイル:行番号範囲）。未マッピング時は `"-"` |
| `files[].items[].confidence` | `高` / `中` / `低` / `-` | 確信度。未マッピング時は `"-"` |
| `files[].items[].note` | 文字列 | 備考 |
| `details` | 文字列（任意） | マッピング根拠の補足説明 |

### サマリー（フロントエンドで集計）

`files` 内の全 `items` から以下を集計します:

| 指標 | 集計方法 |
|------|---------|
| 設計書項目数 | 全 items 数 |
| マッピング済み件数 | `confidence` が `"-"` でない件数 |
| 未マッピング件数 | `confidence` が `"-"` の件数 |
| カバレッジ率 | マッピング済み / 設計書項目数 * 100 |

### フォールバック

AIがJSON形式で応答しない場合は、マッピング結果一覧セクションを非表示にし、詳細レポート（`report` の Markdown 表示）のみ表示します。

---

## 6. バックエンド実装

### スキーマ

**ファイル**: [schemas.py](../versions/v0.9.0/backend/app/models/schemas.py)

モードは `ReviewMode` enum（`review` / `mapping`）で定義されています。

各リクエストモデルに追加されたフィールド:

| モデル | 追加フィールド |
|--------|--------------|
| `ReviewRequest` | `mode`, `useStructureMap`, `structureMap` |
| `GroupReviewRequest` | `mode`, `useStructureMap`, `structureMap` |
| `IntegrateRequest` | `mode`, `useStructureMap`, `structureMap` |
| `StructureMatchingRequest` | `mode` |

レスポンスモデルには `rawOutput` フィールドが追加され、メタ情報ヘッダーを含まないAIの生応答を保持します。マッピングモードではこの `rawOutput` をJSONパースして構造化表示に使用します。

| モデル | 追加フィールド |
|--------|--------------|
| `ReviewResponse` | `rawOutput` |
| `IntegrateResponse` | `rawOutput` |

### API エンドポイント

**ファイル**: [review.py](../versions/v0.9.0/backend/app/routers/review.py)

| Method | Path | モード対応 |
|--------|------|-----------|
| POST | `/api/review` | `mode` に応じたユーザーメッセージ構築。`useStructureMap` + `structureMap` で構造マップをプロンプトに組み込み |
| POST | `/api/review/structure-matching` | `mode` に応じたシステムプロンプト切り替え |
| POST | `/api/review/group` | `mode` に応じたシステムプロンプト切り替え + 構造マップ挿入 |
| POST | `/api/review/integrate` | `mode` に応じたシステムプロンプト切り替え + 構造マップ挿入 + 結果ラベル切り替え |

### 分割API

**ファイル**: [split.py](../versions/v0.9.0/backend/app/routers/split.py)

分割 API 自体はモード共通です。マッピングモードでは構造マップ生成のために呼び出されます。

| Method | Path | 用途 |
|--------|------|------|
| POST | `/api/split/markdown` | md2map で設計書を分割、MAP.json を生成 |
| POST | `/api/split/code` | code2map でコードを分割、MAP.json を生成 |

---

## 7. フロントエンド実装

**ディレクトリ**: [versions/v0.9.0/frontend/src/features/reviewer/](../versions/v0.9.0/frontend/src/features/reviewer/)

| 役割 | ファイル | 説明 |
|------|---------|------|
| モード切り替えUI | [ModeSelector.tsx](../versions/v0.9.0/frontend/src/features/reviewer/components/ModeSelector.tsx) | 突合/マッピングのタブ切り替え |
| 構造マップ生成 | [useStructureMap.ts](../versions/v0.9.0/frontend/src/features/reviewer/hooks/useStructureMap.ts) | レビュー実行前の MAP.json 生成、分割プレビュー済みはスキップ |
| プリセット管理 | [presetCatalog.ts](../versions/v0.9.0/frontend/src/core/data/presetCatalog.ts) | モード別プリセット一覧、デフォルトプリセット取得 |
| 状態管理 | [useReviewerSettings.ts](../versions/v0.9.0/frontend/src/features/reviewer/hooks/useReviewerSettings.ts) | モード切り替え時のプリセット自動切り替え |
| レビュー実行 | [useReviewExecution.ts](../versions/v0.9.0/frontend/src/features/reviewer/hooks/useReviewExecution.ts) | マッピングJSON パース、サマリー集計 |
| 結果表示 | [ReviewResult.tsx](../versions/v0.9.0/frontend/src/features/reviewer/components/ReviewResult.tsx) | マッピング結果テーブル表示、フォールバック処理 |
| 分割実行画面 | [SplitExecutingScreen.tsx](../versions/v0.9.0/frontend/src/features/reviewer/components/SplitExecutingScreen.tsx) | 分割レビュー時のモード・構造マップ対応 |
| APIサービス | [api.ts](../versions/v0.9.0/frontend/src/features/reviewer/services/api.ts) | 各エンドポイントへのリクエスト（mode + structureMap 付き） |

---

## 8. 結果表示

### マッピングモード

マッピング結果一覧テーブル + 詳細レポートの 2段構成で表示します。

```
┌─────────────────────────────────────────────────────────┐
│ マッピング結果一覧                                        │
│                                                         │
│  サマリー: 設計書項目 20件 / マッピング 17件 / 未マッピング 3件│
│  カバレッジ: 85%                                         │
│                                                         │
│  ■ 基本設計書.xlsx                                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 設計書項目   │ 実装要素  │ 実装箇所       │確信度│備考│
│  │ 1.1 ログイン │ AuthCtrl  │ auth.ts:10-25  │ 高  │    │
│  │ 1.2 ログアウト│ AuthCtrl  │ auth.ts:30-45  │ 中  │    │
│  │ 1.3 セッション│ -         │ -              │ -   │未実装│
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 突合モードとの表示差異

| セクション | 突合モード | マッピングモード |
|-----------|-----------|----------------|
| 簡易判定 | 表示（キーワード検索） | 非表示 |
| マッピング結果一覧 | 非表示 | 表示（JSON パース成功時） |
| 実行情報 | 表示 | 表示 |
| 詳細レポート | 表示 | 表示（フォールバック兼用） |
| 実行データ一式DL | 表示 | 表示 |

---

## 9. 設計上のポイント

- **コード共通化**: UIフロー・コンポーネント構造を突合モードと完全に共通化し、プリセット・プロンプト・判定ロジック・出力ファイル名のみモード別に差し替え
- **フラグベース設計**: `useStructureMap` フラグが構造マップに関するすべての動作を制御。モードはフラグのデフォルト値を決定するだけで、実際の動作はすべてフラグで判定。将来的に突合モードでも有効化可能
- **分割レビューの再利用**: v0.8.0 の 3フェーズ分割レビュー（構造マッチング → グループレビュー → 統合）をそのまま活用し、プロンプトのみモード別に切り替え
- **JSON応答 + フォールバック**: マッピング結果を JSON で受け取り構造化表示。パース失敗時は Markdown レポートにフォールバック
- **rawOutput**: レスポンスにメタ情報ヘッダーを含まない AI の生応答を保持するフィールドを追加。マッピング JSON パースに使用

---

## 10. エンドツーエンドの流れ

### 一括実行

```
ユーザー: 設計書.xlsx + UserService.java をアップロード
    ↓
[Excel→Markdown変換、コードに行番号付与]（既存機能）
    ↓ ユーザーが「マッピングモード」を選択
    ↓ プリセット: standard-mapping（JSON出力指定）
    ↓
[構造マップ生成]  ← useStructureMap=true のため自動実行
    ├─ md2map → 設計書 MAP.json [MD1, MD2, ...]
    └─ code2map → コード MAP.json [CD1, CD2, ...]
    ↓
[/api/review]
    mode=mapping, useStructureMap=true, structureMap={...}
    ・マッピング用プロンプト + 構造マップ情報
    ↓
AIがJSON形式でマッピング結果を返却
    ↓
フロントエンドで rawOutput をパース → マッピング結果
    ↓
マッピング結果一覧テーブルとして表示
    ├─ サマリー（カバレッジ率）
    ├─ 設計書ファイルごとのマッピングテーブル
    └─ 詳細レポート（Markdown）
```

### 分割実行

```
ユーザー: 大規模な設計書.xlsx + 複数のソースファイルをアップロード
    ↓
[Excel→Markdown変換、コードに行番号付与]（既存機能）
    ↓ ユーザーが「マッピングモード」+「分割」を選択
    ↓
[分割プレビュー]
    ├─ md2map → 設計書の INDEX.md + parts/ + MAP.json
    └─ code2map（ファイルごと） → コードの INDEX.md + parts/ + MAP.json
    ↓
[構造マップ生成] ← 分割プレビューで生成済みの MAP.json はスキップ
    ↓
[Phase 1] 構造マッチング
    INDEX.md + MAP.json をLLMに送信
    → マッピング観点でグループ化（設計項目↔コード要素の対応推定）
    ↓
[Phase 2] グループマッピング × N
    各グループの実コンテンツ + 該当グループの構造マップ
    → 各グループのマッピング結果
    ↓
[Phase 3] 統合
    全マッピング結果 + 全体の構造マップ
    → 統合マッピングレポート
    ↓
フロントエンドで表示（一括実行と同じUI）
```
