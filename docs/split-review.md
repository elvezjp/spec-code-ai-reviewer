# 分割レビュー機能の詳細

![AIによる大規模設計書・コード分割レビューの仕組みのフローチャート](assets/split-review-flow.png)

## 全体像

この機能は大きく **2つのツール** と **3フェーズのAIレビュー** で構成されています。

---

## 1. md2map（設計書の分割）

**ディレクトリ**: [md2map/](../md2map/)

マークダウン変換済みの設計書を、3つの分割モードからユーザーが選択してセクション分割します。

### 1.1 分割モード

| モード | 説明 | LLM |
|---|---|---|
| 見出し（heading） | 見出し（H1〜H6）の階層構造に基づいて分割する。デフォルト | 不要 |
| NLP | 自然言語処理（形態素解析）を用いて意味的な区切りで分割する | 不要 |
| AI | LLM（大規模言語モデル）を用いて意味的な区切りで分割する | 必要 |

- **見出しモード**: 高速で安定。見出しが適切に構造化された文書に最適
- **NLPモード**: 見出しによる基本分割に加え、見出しのない長大なセクションもサブスプリット（subsplit）として細分化
- **AIモード**: NLPモードと同様にサブスプリットを生成するが、LLMを使用するため最も高精度。レビュー実行用のLLM設定を流用する

### 1.2 コンポーネント

| コンポーネント | ファイル | 役割 |
|---|---|---|
| パーサー | [markdown_parser.py](../md2map/md2map/parsers/markdown_parser.py) | ATXスタイルの見出しを正規表現で解析。split_mode に応じて NLP/AI サブスプリットを実行 |
| Parts生成 | [parts_generator.py](../md2map/md2map/generators/parts_generator.py) | 各セクションを個別ファイルに出力（`<H1>_<H2>_<H3>.md`形式） |
| Index生成 | [index_generator.py](../md2map/md2map/generators/index_generator.py) | 階層ツリー構造の `INDEX.md` を作成 |
| Map生成 | [map_generator.py](../md2map/md2map/generators/map_generator.py) | `MAP.json` を生成（id, section, level, path, 行範囲, word count, SHA-256チェックサム） |

各セクションには `MD1`, `MD2`, ... のIDが付与され、デフォルトの分割深度は **H2** です。

---

## 2. code2map（ソースコードの分割）

**ディレクトリ**: [code2map/](../code2map/)

ソースコードをAST（抽象構文木）解析し、クラス・メソッド・関数単位で分割します。

| パーサー | ファイル | 方式 |
|---|---|---|
| Python | [python_parser.py](../code2map/parsers/python_parser.py) | Python標準の`ast`モジュールで解析。クラス、メソッド、トップレベル関数を抽出 |
| Java | [java_parser.py](../code2map/parsers/java_parser.py) | `javalang`ライブラリで解析。クラス、インターフェース、メソッド、コンストラクタを抽出 |

各シンボルには `CD1`, `CD2`, ... のIDが付与されます。ネストされた関数は親に含められます。

---

## 3. 3フェーズAIレビュー

バックエンドのAPIは [versions/v0.8.2/backend/app/routers/](../versions/v0.8.2/backend/app/routers/) に実装されています。

### フェーズ1: 構造マッチング (`POST /api/review/structure-matching`)

**ファイル**: [review.py](../versions/v0.8.2/backend/app/routers/review.py)

- **入力**: 設計書とコードそれぞれの `INDEX.md` + `MAP.json`
- **処理**: LLMが両方の構造を分析し、関連性の高いセクションとコードシンボルを **多対多** のグループにまとめる
- **出力**: `MatchedGroup[]` — 各グループにdocSectionsとcodeSymbolsが含まれる

```
例: group1「ユーザー管理」
  - 設計書: MD1(概要), MD3(ユーザー登録)
  - コード: CD1(UserService), CD4(UserRepository)
  - 理由: "Both handle user operations"
```

ポイントは **1:1マッピングではなく多対多** であること。1つの設計セクションが複数のコード部分に、またその逆も関連づけられます。

### フェーズ2: グループレビュー (`POST /api/review/group`)

- **入力**: グループに含まれる設計書の実コンテンツ + コードの実コンテンツ
- **処理**: 各グループごとにLLMが設計書とコードの突合レビューを実施
- **出力**: Markdownフォーマットのレビューレポート
- フロントエンドが各グループを並列管理し、一時停止・再開も可能

### フェーズ3: 結果統合 (`POST /api/review/integrate`)

- **入力**: フェーズ1の構造情報 + フェーズ2の全グループレビュー結果
- **処理**: LLMが全結果を統合し、重複を除去、グループ横断の問題を検出
- **出力**: 最終的な統一レビューレポート（Markdown）

---

## 4. フロントエンド実装

**ディレクトリ**: [versions/v0.8.2/frontend/src/features/reviewer/](../versions/v0.8.2/frontend/src/features/reviewer/)

| コンポーネント | ファイル | 役割 |
|---|---|---|
| 分割設定UI | [SplitSettingsSection.tsx](../versions/v0.8.2/frontend/src/features/reviewer/components/SplitSettingsSection.tsx) | batch/splitモード選択、分割モード選択（見出し/NLP/AI）、分割深度設定、プレビュー |
| 実行画面 | [SplitExecutingScreen.tsx](../versions/v0.8.2/frontend/src/features/reviewer/components/SplitExecutingScreen.tsx) | 3フェーズの進捗表示（✓/⏳/○）、一時停止・再開 |
| 分割ロジック | [useSplitSettings.ts](../versions/v0.8.2/frontend/src/features/reviewer/hooks/useSplitSettings.ts) | 状態管理、API呼び出し、分割モード管理 |
| APIサービス | [api.ts](../versions/v0.8.2/frontend/src/features/reviewer/services/api.ts) | 各エンドポイントへのリクエスト |

---

## 5. 設計上のポイント

- **ステートレスなバックエンド**: サーバー側にセッション状態を持たず、各APIコールが必要なデータを全て含む。失敗時のリトライが容易
- **トークン推定**: 日本語 ≈ 1.5トークン/文字、英語 ≈ 0.25トークン/文字 で概算し、分割の必要性判断に利用
- **フェーズ1の効率性**: 実コンテンツではなくINDEX.md + MAP.json（メタデータ）だけをLLMに渡すため、トークン消費を抑えて構造分析を実施
- **フェーズ2で初めて実コンテンツ**: グループ化された関連部分のみを渡すため、1回あたりのトークン量を抑制
- **設計書・コード両方分割が必須**: 片側だけの分割は構造マッチングの精度が低下するため、分割モード選択時は両方を分割する
- **分割モードの柔軟性**: 見出し/NLP/AIの3モードにより、文書の特性やLLM利用可否に応じた最適な分割が可能

---

## 6. エンドツーエンドの流れ

```
ユーザー: 大規模な設計書.xlsx + UserService.java をアップロード
    ↓
[Excel→Markdown変換、コードに行番号付与]（既存機能）
    ↓ ユーザーが「分割」モードを選択
    ↓ 分割モード（見出し/NLP/AI）を選択
    ↓
[md2map] 設計書 → セクション分割（選択モードで実行） → INDEX.md + MAP.json
[code2map] コード → シンボル分割 → INDEX.md + MAP.json
    ↓
[Phase 1] INDEX + MAP をLLMに送信 → グループ化結果
    ↓
[Phase 2] 各グループの実コンテンツをLLMに送信 → 個別レビュー結果
    ↓
[Phase 3] 全レビュー結果をLLMに送信 → 最終統合レポート
    ↓
ユーザーに表示（通常レビューと同じフォーマット）
```
