# v0.9.4 OSS公開前リリースレビュー

- レビュー実施日: 2026-03-25
- 対象バージョン: v0.9.4
- ブランチ: tominaga/20260325-add-summary-mode-options
- PR: #72
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
| 内部URL・IPアドレス | OK | ハードコードなし。`ecosystem.config.js` の `CORS_ORIGINS` は `example.com` プレースホルダー |

## 2. ドキュメント整備状況

| ドキュメント | 状態 | 備考 |
|---|---|---|
| README.md / README_ja.md | 整備済み | 日英バイリンガル。v0.9.4 のポート・ディレクトリ情報を反映済み |
| CHANGELOG.md / CHANGELOG_ja.md | 整備済み | v0.9.4エントリ（2026-03-25）記載。Keep a Changelog準拠。日英対称 |
| CONTRIBUTING.md / CONTRIBUTING_ja.md | 整備済み | 日英バイリンガル。テストコマンド等 v0.9.4 に更新済み |
| SECURITY.md / SECURITY_ja.md | 整備済み | サポートバージョン v0.9.4 に更新済み |
| LICENSE | 整備済み | MIT License (2025 Elvez)。READMEバッジと一致 |
| md2map CHANGELOG.md / CHANGELOG_ja.md | 整備済み | v0.4.0エントリ（2026-03-25）記載。日英対称 |

## 3. バージョン整合性

| 箇所 | バージョン | 結果 |
|---|---|---|
| `latest`シンボリックリンク | → versions/v0.9.4 | OK |
| `backend/pyproject.toml` version | 0.9.4 | OK |
| CHANGELOG.md | [0.9.4] - 2026-03-25 | OK |
| CHANGELOG_ja.md | [0.9.4] - 2026-03-25 | OK |
| SECURITY.md / SECURITY_ja.md | 0.9.4 サポート | OK |
| CONTRIBUTING.md / CONTRIBUTING_ja.md | v0.9.4 参照 | OK |
| README.md ディレクトリ構造 | v0.9.4 (latest) | OK |
| README.md ポートテーブル | v0.9.4 = 8094 | OK |
| `.github/workflows/ci.yml` | working-directory: versions/v0.9.4 | OK |
| md2map バージョン | v0.4.0 | OK |

## 4. テスト実行結果

### バックエンド（pytest）

- 結果: **186 passed, 1 warning**
- 実行時間: 2.05s
- Python: 3.13.3
- 警告内容: `test_organize.py` で `RuntimeWarning: coroutine 'to_thread' was never awaited`（テスト結果に影響なし）

### フロントエンド（vitest）

- 結果: **180 passed (17 test files)**
- 実行時間: 3.57s
- Node.js: v23.11.1
- 警告・エラー: なし

## 5. CI設定

| チェック項目 | 結果 | 備考 |
|---|---|---|
| `.github/workflows/ci.yml` バージョン | OK | backend/frontend ともに v0.9.4 を指定 |
| CI内の機密情報 | OK | テスト実行のみで機密情報の直書きなし |
| テストマトリクス | OK | Python 3.10/3.13 × 3 OS、Node 20/23 × 3 OS |

## 6. コード品質・セキュリティレビュー

### 6.1 指摘事項

| 項目 | 状態 | 優先度 | 詳細 |
|---|---|---|---|
| `summaryMode` / `summaryMaxChars` の通常ケース反映漏れ | 対応済み | 高 | `事前重要指定なし` の場合、フロントエンドが `summaryMode/summaryMaxChars` をバックエンドに送らずデフォルト `text/100` になる可能性があった。`versions/v0.9.4/frontend/src/features/reviewer/hooks/useSplitSettings.ts` で通常ケースでも送信するよう修正済み（加えて `maxSubsections` も通常セクション設定を送信）。 |
| パストラバーサル（`request.filename` をパス結合に使用） | 要修正 | 高 | `versions/v0.9.4/backend/app/routers/split.py` で `os.path.join(tmpdir, request.filename ...)` を使用しており、`../` 等により `tmpdir` 外へ書き込み可能になり得る（`/split/markdown` と `/split/code`）。`Path(filename).name` でベース名に丸める、または固定名を使う等の対策を推奨。 |
| 文字列切り詰めバグ | 要修正 | 高 | `markdown_parser.py` L525-526: `summary_max_chars` が3以下の場合、切り詰め結果が `max_chars` を超える。`max_chars <= 3` のガード追加を推奨 |
| `summaryMaxChars` バックエンドバリデーション | 要修正 | 高 | `schemas.py`: `summaryMaxChars` に `Field(ge=1, le=10000)` 等の制約がない。`maxDepth` は `Field(ge=1, le=6)` で制約済みなのに対し不整合 |
| エラーメッセージでの例外情報漏洩 | 要修正 | 高 | `split.py` L94-98: `str(e)` をクライアントに返しており、ファイルパス・API情報が漏洩する可能性あり |
| `aiPromptExtraNotes` プロンプトインジェクション | 要確認 | 中 | `markdown_parser.py` L861-864: ユーザー入力がLLMシステムプロンプトに直接連結される。意図的であればコメントで明記し、文字数制限を検討 |
| `content` フィールドのサイズ制限 | 要修正 | 中 | `schemas.py` の `SplitMarkdownRequest.content` にサイズ上限がなく、DoS攻撃のリスクあり |
| フロントエンド定数ハードコード | 改善推奨 | 低 | `summaryMaxChars` のmin/max/fallback値がコンポーネント内にハードコード。定数抽出を推奨 |

### 6.2 良好な点

- XSS脆弱性なし（フロントエンドは全てJSXテキストレンダリング）
- 型安全性が高い（Pydantic/TypeScript型定義が充実）
- テストカバレッジ良好（バックエンド+4件、フロントエンド+10件が新規追加）
- 認証情報の取り扱いが適切（環境変数・APIパラメータ経由）

## 7. 文書間の整合性・改善提案

| 項目 | 状態 | 優先度 | 詳細 |
|---|---|---|---|
| pyproject.toml description | 要修正 | 中 | 日本語のみ。OSS公開時は英語が望ましい（前回レビューから継続） |
| pyproject.toml license フィールド | 未定義 | 中 | `license = "MIT"` を追加すると PyPI 等でのメタデータ表示が改善される（前回レビューから継続） |
| CHANGELOG 比較リンク | 未整備 | 低 | Keep a Changelog 推奨の比較リンクがない（前回レビューから継続） |
| CODE_OF_CONDUCT.md | 未整備 | 低 | CONTRIBUTING に「行動規範に従うこと」と記載があるが CODE_OF_CONDUCT.md が存在しない（前回レビューから継続） |

## 8. 前回レビュー（v0.9.3）からの改善状況

| 前回指摘 | 対応状況 |
|---|---|
| pyproject.toml description 英語化 | 未対応（継続） |
| pyproject.toml license フィールド追加 | 未対応（継続） |
| CHANGELOG 比較リンク | 未対応（継続） |
| CODE_OF_CONDUCT.md 追加 | 未対応（継続） |
| READMEのアプリ内相対リンク（GPT指摘） | 未対応（継続） |
| SECURITYの報告導線の表現ゆれ（GPT指摘） | 未対応（継続） |

## 9. 総合判定

**公開可（コード品質の指摘事項は早期対応推奨）**

主要文書（LICENSE, README, CHANGELOG, CONTRIBUTING, SECURITY）は日英とも揃っており、バージョン整合性も確認済み。機密情報の混入なし。テストは全パス（バックエンド 186件、フロントエンド 180件）。

コード品質面では、`summaryMaxChars` のバックエンドバリデーション不足、エラーメッセージでの例外情報漏洩、文字列切り詰めの境界値バグの3点が優先度高の指摘事項。これらはOSS公開自体をブロックするものではないが、本番運用前に対応することを強く推奨する。

---

## 10. 追記（GPT-5.2 レビュー）

- 追記日: 2026-03-25
- 追記担当: GPT-5.2（Cursor）

### 10.1 追記内容（対応状況）

- `summaryMode/summaryMaxChars` が **事前重要指定なし** の場合に反映されない可能性について、フロントエンド側で **通常ケースでもAPIへ送信** する修正を実施。
  - 対象: `versions/v0.9.4/frontend/src/features/reviewer/hooks/useSplitSettings.ts`
  - 影響: UI上の「設計書 — 通常セクション」で選択したサマリー設定が、事前重要指定なしでもバックエンドに反映される。

### 10.2 テスト

- フロントエンド（vitest）: **180 passed**（v0.9.4）
