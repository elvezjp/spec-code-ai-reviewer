# v0.9.2 OSS公開前リリースレビュー

※本バージョン（v0.9.2）は、複数レビュー（Claude Opus 4.6 + GPT-5.4 Nano）の結果、OSSとして公開して問題ないと判断済み（2026-03-20時点）

- レビュー実施日: 2026-03-20
- 対象バージョン: v0.9.2
- ブランチ: tominaga/20260318-add-pre-split-importance
- レビュー担当: Claude Opus 4.6（Claude Code）

## 1. 機密情報チェック

| チェック項目 | 結果 | 備考 |
|---|---|---|
| ハードコードされたAPIキー・シークレット | OK | Anthropic/OpenAI/Bedrockすべて設定経由。ソースコード内にキー埋め込みなし |
| `.env`ファイル | OK | `.env.example`（テンプレート）のみ。実ファイルはgit管理外 |
| `.venv` / `node_modules` | OK | gitトラッキング対象外 |
| `.pytest_cache` | OK | gitトラッキング対象外 |
| `.gitignore` | OK | 機密ファイル・ビルド成果物・IDE設定を網羅的に除外 |
| テストデータ内の機密情報 | OK | テスト用ダミー値のみ |

## 2. ドキュメント整備状況

| ドキュメント | 状態 | 備考 |
|---|---|---|
| README.md / README_ja.md | 整備済み | 日英バイリンガル。機能説明・セットアップ手順・ライセンス表記あり |
| CHANGELOG.md / CHANGELOG_ja.md | 整備済み | v0.9.2エントリ（2026-03-20）記載。Keep a Changelog準拠 |
| CONTRIBUTING.md / CONTRIBUTING_ja.md | 整備済み | 日英バイリンガル |
| SECURITY.md / SECURITY_ja.md | 整備済み | 日英バイリンガル。サポートバージョン v0.9.2 に更新済み |
| LICENSE | 整備済み | MIT License (2025 Elvez) |

## 3. バージョン整合性

| 箇所 | バージョン | 結果 |
|---|---|---|
| `latest`シンボリックリンク | → versions/v0.9.2 | OK |
| CHANGELOG.md | [0.9.2] - 2026-03-20 | OK |
| CHANGELOG_ja.md | [0.9.2] - 2026-03-20 | OK |
| SECURITY.md / SECURITY_ja.md | 0.9.2 サポート | OK |
| CONTRIBUTING.md / CONTRIBUTING_ja.md | v0.9.2 参照 | OK |

## 4. テスト実行結果

### バックエンド（pytest）

- 結果: **178 passed, 1 warning**
- 実行時間: 1.62s
- 警告内容: `test_review_split.py` で `RuntimeWarning: coroutine 'to_thread' was never awaited`（テスト結果に影響なし）

### フロントエンド（vitest）

- 結果: **140 passed (14 test files)**
- 実行時間: 2.27s
- 警告・エラー: なし

## 5. CI設定

| チェック項目 | 結果 | 備考 |
|---|---|---|
| `.github/workflows/ci.yml` バージョン | OK | working-directory が v0.9.2 を指すよう修正済み |
| CI内の機密情報 | OK | テスト実行のみで機密情報の直書きなし |

## 6. 文書間の整合性・改善提案

| 項目 | 状態 | 詳細 |
|---|---|---|
| CHANGELOG Version Comparisonテーブル | 要修正 | v0.9.2 の行が未記載 |
| CHANGELOG 比較リンク | 未整備 | Keep a Changelog推奨の `[0.9.2]: https://github.com/.../compare/...` がない |
| README API Endpointsテーブル | 要更新 | 分割レビュー系API（`/api/split/*`, `/api/summarize`）が未記載 |
| README → SECURITY/CONTRIBUTING リンク | 未整備 | README末尾に明示的リンクなし |
| CONTRIBUTING → CODE_OF_CONDUCT 参照 | 未整備 | 「行動規範に従うこと」と記載があるが、CODE_OF_CONDUCT.md が存在しない |
| LICENSE 著作権年 | 確認要 | `Copyright (c) 2025 Elvez` — 2026年公開なら `2025-2026` への更新を検討 |

## 7. 総合判定

**条件付き公開可**

主要文書（LICENSE, README, CHANGELOG, CONTRIBUTING, SECURITY）は日英とも揃っており、機密情報の混入もなし。以下の軽微な修正を推奨：

1. テスト実行による全パス確認（本レビュー内で未実施）
2. CHANGELOG の Version Comparison テーブルに v0.9.2 を追加
3. README の API Endpoints テーブルに分割レビュー系APIを追加
4. README 末尾に SECURITY.md / CONTRIBUTING.md へのリンクを追加

## 8. GPT-5.4 Nano によるレビュー

既存の静的チェック（主要公開文書の存在・READMEからの導線・参照の張りどころ）を中心に確認しました。

### セキュリティ/ライセンス/主要文書
- `LICENSE`：MITで本文あり（`README` のライセンス表記と整合）
- `SECURITY.md` / `SECURITY_ja.md`：責任ある開示手順・対応スケジュールが明記
- `CONTRIBUTING.md` / `CONTRIBUTING_ja.md`：Issue/PR手順、テスト実行コマンドが明記

### ドキュメント整合性（要修正）
| 項目 | 指摘 | 優先度 |
|---|---|---|
| `CONTRIBUTING*` が参照する `spec.md` | `spec.md` は `versions/v*/spec.md` や `latest/spec.md` に存在するが、直下の `spec.md` を前提に読めるため、参照パスの明確化が必要 | 高 |
| `CODE_OF_CONDUCT.md` | `CONTRIBUTING*` に「行動規範」があるが、リポジトリ直下の `CODE_OF_CONDUCT.md` が見当たらず、`markitdown/CODE_OF_CONDUCT.md` にある（直下に追加 or リンク先の明記が必要） | 高 |
| `CHANGELOG*` の運用補助 | `CHANGELOG*` に Keep a Changelog / SemVer は記載がある一方、Version Comparison や compareリンクの参照定義（推奨）を補強した方が運用しやすい | 中 |
| `README*` の入口導線 | 現状でもライセンス/各章への説明はあるが、`Contributing` / `Security` への“明示リンク”があると初見ユーザーに優しい | 中 |

### 総合判定
**条件付き公開可**。上記の「整合性」系の修正（パス明確化、行動規範リンク、CHANGELOG運用補助）を行った上で公開するのが安全です。

### 補足（本レビューで実施したこと）
- ファイルの存在確認と本文の静的確認（コード実行・実際のCI通過の検証は未実施）
