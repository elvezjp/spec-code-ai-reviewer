# v0.9.1 OSS公開前リリースレビュー

※本バージョン（v0.9.1）は、複数レビューの結果、OSSとして公開して問題ないと判断済み（2026-03-13時点）

- レビュー実施日: 2026-03-13
- 対象バージョン: v0.9.1
- ブランチ: tominaga/20260313-release-v0.9.1

## 1. 機密情報チェック

| チェック項目 | 結果 | 備考 |
|---|---|---|
| ハードコードされたAPIキー・シークレット | OK | Anthropic/OpenAI/Bedrockすべて設定経由。ソースコード内にキー埋め込みなし |
| `.env`ファイル | OK | `.env.example`（テンプレート）のみ。実ファイルはgit管理外 |
| `.venv` / `node_modules` | OK | gitトラッキング対象外（0ファイル） |
| `.pytest_cache` | OK | gitトラッキング対象外 |
| `.gitignore` | OK | 機密ファイル・ビルド成果物・IDE設定を網羅的に除外 |
| テストデータ内の機密情報 | OK | テスト用ダミー値（`test-secret-key`等）のみ |

## 2. ドキュメント整備状況

| ドキュメント | 状態 | 備考 |
|---|---|---|
| README.md / README_ja.md | 整備済み | 日英バイリンガル。機能説明・セットアップ手順・ライセンス表記あり |
| CHANGELOG.md / CHANGELOG_ja.md | 整備済み | v0.9.1エントリ（2026-03-13）記載。Keep a Changelog準拠 |
| CONTRIBUTING.md / CONTRIBUTING_ja.md | 整備済み | 日英バイリンガル |
| SECURITY.md / SECURITY_ja.md | 整備済み | 日英バイリンガル |
| LICENSE | 整備済み | MIT License (2025 Elvez) |

## 3. バージョン整合性

| 箇所 | バージョン | 結果 |
|---|---|---|
| `backend/pyproject.toml` | 0.9.1 | OK |
| `frontend/package.json` | 0.9.1 | OK |
| `latest`シンボリックリンク | → versions/v0.9.1 | OK |
| CHANGELOG.md | [0.9.1] - 2026-03-13 | OK |
| CHANGELOG_ja.md | [0.9.1] - 2026-03-13 | OK |

## 4. テスト実行結果

### バックエンド（pytest）

- 結果: **173 passed, 1 warning**
- 実行時間: 1.43s
- 警告内容: `test_organize.py` で `RuntimeWarning: coroutine 'to_thread' was never awaited`（テスト結果に影響なし）

### フロントエンド（vitest）

- 結果: **140 passed (14 test files)**
- 実行時間: 2.82s
- 警告・エラー: なし

## 5. 依存関係

### バックエンド主要依存

| パッケージ | バージョン要件 | 用途 |
|---|---|---|
| fastapi | >=0.115.0 | Webフレームワーク |
| uvicorn | >=0.32.0 | ASGIサーバー |
| anthropic | >=0.40.0 | Anthropic API連携 |
| openai | >=2.14.0 | OpenAI API連携 |
| boto3 | >=1.35.0 | AWS Bedrock連携 |
| markitdown | >=0.0.1a3 | ドキュメント変換 |
| add-line-numbers | ローカル | 行番号付与（リポジトリ内モジュール） |
| md2map | ローカル | Markdown分割（リポジトリ内モジュール） |
| code2map | ローカル | コード分割（リポジトリ内モジュール） |

### フロントエンド主要依存

| パッケージ | バージョン要件 | 用途 |
|---|---|---|
| react | ^19.2.0 | UIフレームワーク |
| react-router-dom | ^7.12.0 | ルーティング |
| vite | ^7.2.4 | ビルドツール |
| tailwindcss | ^4.1.18 | CSSフレームワーク |
| vitest | ^3.2.4 | テストフレームワーク |

## 6. 注意事項

1. **ローカルパッケージの相対パス参照**: `pyproject.toml`の`[tool.uv.sources]`で`add-line-numbers`, `md2map`, `code2map`が`../../../`の相対パスで参照されている。リポジトリルートからのセットアップであれば問題なし
2. **spec.md内のプレースホルダー**: `YOUR_SECRET_ACCESS_KEY`等はドキュメントのサンプル値として適切
3. **CORSデフォルト設定**: `main.py`の`CORS_ORIGINS`デフォルトが`"*"`。本番環境では環境変数で制限する想定

## 7. 総合判定

**公開可**

機密情報の混入なし、ドキュメント日英整備済み、バージョン番号整合、全テストパス。OSS公開に問題なし。

---

## 8. 追加レビュー（AIコードレビューアー）

- レビュー担当: GPT-5.1（Cursor 内部エージェント）
- レビュー実施日: 2026-03-13
- 対象範囲:
  - ルートドキュメント: `README.md`, `README_ja.md`, `CHANGELOG*.md`, `CONTRIBUTING*.md`, `SECURITY*.md`, `LICENSE`
  - バージョン管理ドキュメント: `versions/README.md`, `versions/v0.9.1/spec.md`, `versions/v0.9.1/config-file-generator-spec.md`
  - CI/設定ファイル: `.github/workflows/ci.yml`, `docker-compose.yml`, `ecosystem.config.js`, `dev.ecosystem.config.js`, `nginx/version-map.conf`
  - 秘密情報スキャン対象: リポジトリ全体（AWSキー形式・OpenAIキー形式等のパターン検索）

### 8.1 機密情報・設定ファイルチェック

| チェック項目 | 結果 | 備考 |
|---|---|---|
| ハードコードされたAPIキー/シークレット | OK | `AKIA...`/`sk-...` パターン検索いずれもヒットなし |
| `.env` 関連 | OK | `.env.example` のみ。実運用用 `.env` は非管理前提 |
| Bedrock/Anthropic/OpenAI 設定 | OK | すべて環境変数またはアップロード設定ファイル経由で参照 |
| CI 設定内のシークレット | OK | `.github/workflows/ci.yml` はテスト実行のみで機密情報の直書きなし |

### 8.2 ドキュメント・バージョン整合性

| 箇所 | v0.9.1 反映 | 備考 |
|---|---|---|
| `README.md` / `README_ja.md` | OK | `latest -> versions/v0.9.1`、ポート表 `v0.9.1 (latest) | 8091` を明示 |
| `CHANGELOG.md` / `CHANGELOG_ja.md` | OK | `## [0.9.1] - 2026-03-13` に新機能と設定ファイル更新を記載 |
| `versions/README.md` | OK | バージョン比較表・更新履歴に v0.9.1 を追加済み |
| `SECURITY*.md` | OK | サポートバージョン表が `0.9.1 のみサポート` に更新済み |
| `versions/v0.9.1/spec.md` 系 | OK | 仕様・サンプル出力内のバージョン表記が `v0.9.1` で統一 |

### 8.3 軽微な改善提案（任意対応）

1. **README_ja.md のテストセクションのコメント表記揺れ**
   - 該当: バージョン別テスト実行コマンド付近の日本語コメント
   - 内容: コマンド自体は `versions/v0.9.1/backend` / `frontend` を指しているが、コメントに旧バージョン名が残っている箇所がある
   - 提案: コメント中のバージョン名を `v0.9.1` に統一すると読者にとって分かりやすい

### 8.4 総合所見

- ライセンス、日英ドキュメント、セキュリティポリシー、CHANGELOG、バージョン管理（`latest` シンボリックリンク・ポート割り当て・サポートバージョン表）に一貫性があり、OSS公開の前提条件を満たしている。
- リポジトリ内に実運用の認証情報や機密データは見当たらず、`.env.example` などもテンプレート値のみで安全。

**判定: 公開可（軽微なコメント表記の修正のみ任意で対応推奨）**
