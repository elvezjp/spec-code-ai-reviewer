# spec-code-ai-reviewer

[English](./README.md) | [日本語](./README_ja.md)

[![Elvez](https://img.shields.io/badge/Elvez-Product-3F61A7?style=flat-square)](https://elvez.co.jp/)
[![IXV Ecosystem](https://img.shields.io/badge/IXV-Ecosystem-3F61A7?style=flat-square)](https://elvez.co.jp/ixv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Stars](https://img.shields.io/github/stars/elvezjp/spec-code-ai-reviewer?style=social)](https://github.com/elvezjp/spec-code-ai-reviewer/stargazers)

設計書（Excel / Word形式）とプログラムコードをAIで突合し、整合性を検証するWebアプリケーション。

https://github.com/user-attachments/assets/8c72f49b-35c5-43af-b1f2-29b6b6b71e30

## 機能

- **設計書変換**: Excel (.xlsx, .xls) / Word (.docx) → Markdown形式に変換（MarkItDown、excel2md使用。Wordは MarkItDown のみ対応）
- **プログラム変換**: 任意のテキストファイルに行番号を付与（add-line-numbers準拠）
- **突合レビュー**: LLM（Bedrock / Anthropic / OpenAI）を使用して設計書とコードの整合性を検証
- **分割レビュー**: トークン上限を超える設計書・コードをセマンティック分割してレビュー（md2map / code2map使用）
- **レポート出力**: マークダウン形式のレビューレポートを生成

### 大規模ファイルの分割レビュー（[詳細](docs/split-review.md)）

LLMには入力トークンの上限があるため、大規模な設計書や数千行のコードはそのままではレビューできない場合があります。
単純な行数での分割ではセクションやクラス・関数の途中で切れてしまい、文脈が失われレビュー精度が低下します。

このアプリケーションでは、マークダウン変換した設計書とソースコードを意味のある単位に分割し、関連する部分をグループ化して突合レビューすることが可能です。

**設計書・コード分割**:
- [md2map](https://github.com/elvezjp/md2map): マークダウン変換した設計書をセクション単位でファイル分割し、JSONマップを作成します。
- [code2map](https://github.com/elvezjp/code2map): ソースコードをクラス・関数単位でファイル分割し、JSONマップを作成します。

**AIによる分割レビュー**（3ステップで実行）:
1. **構造マッチング**: 設計書とコードのJSONマップをAIが分析し、関連性の高い設計書セクションとコードをグループにまとめます。
2. **グループレビュー**: 各グループに対して、分割した設計書とコードを組み合わせて、AIが突合レビューを行います。
3. **結果統合**: 全グループのレビュー結果をAIが統合し、最終的なレビューレポートを生成します。

## システム構成

- **フロントエンド**: Vite + React + TypeScript + Tailwind CSS
- **バックエンド**: Python / FastAPI
  - MarkItDown / excel2md (Excel→Markdown変換)
  - add-line-numbers準拠 (行番号付与)
  - マルチLLMプロバイダー対応 (Bedrock / Anthropic / OpenAI)

## 使い方

AIレビューをすぐに試せるサンプルファイル（Excel設計書とJavaコード）を [docs/sample](docs/sample/) に用意しています。使い方や仕込んである不整合の一覧は [docs/sample/README.md](docs/sample/README.md) を参照してください。

1. **設計書をアップロード**: Excel (.xlsx, .xls) または Word (.docx) ファイルを選択（複数可）
   - **役割**: メイン設計書を1つ選択（それ以外は参照資料として扱われる）
   - **種別**: 設計書/要件定義書/コーディング規約など9種類から選択
   - **変換ツール**: MarkItDown / excel2md (CSV) / excel2md (CSV+Mermaid) から選択
2. **「マークダウンに変換」をクリック**: Markdown形式に変換されプレビュー表示
3. **プログラムをアップロード**: 任意のソースコードファイルを選択（複数可）
4. **「add-line-numbersで変換」をクリック**: 行番号が付与されプレビュー表示
5. **「レビュー実行」をクリック**: AIが同じ設定で2回レビューを実行
6. **結果を確認**: タブ切替で1回目・2回目の結果を個別に確認、コピーまたはダウンロード

### LLMプロバイダー・認証情報の切り替え

デフォルトではシステムLLM（サーバー側で設定されたAWS Bedrock）が使用されます。利用者自身のLLM認証情報を使用する場合は、以下の手順で設定ファイルをアップロードしてください。

1. 画面右上の「設定」アイコンから設定モーダルを開く
2. [設定ファイルジェネレーター](/config-file-generator/)画面でLLMプロバイダー（Bedrock / Anthropic API / OpenAI API）を選択し、APIキーなど必要な情報を入力して設定ファイルを作成
3. 設定モーダルに戻って設定ファイルをアップロード
4. 使用するLLMモデルを選択（複数指定した場合）

## セットアップ

### 前提条件

#### Python バージョン

- **必須バージョン**: Python 3.11以上
- **推奨バージョン**: Python 3.11 または 3.13
- **確認方法**: `python --version` または `python3 --version` で確認してください

uvが自動的に適切なPythonバージョンを使用します。システムにインストールされているPython 3.11以上のバージョンがそのまま利用されます。

#### Node.js バージョン

- **必須バージョン**: Node.js 20以上
- **推奨バージョン**: Node.js 22 LTS
- **確認方法**: `node --version` で確認してください

フロントエンド（Vite + React + TypeScript）の開発・ビルドに必要です。

#### その他

- [uv](https://docs.astral.sh/uv/) (Python パッケージマネージャー)
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### インストール

```bash
# uv をインストール（未インストールの場合）
# 詳細: https://docs.astral.sh/uv/getting-started/installation/

# Node.js をインストール（未インストールの場合）
# 詳細: https://nodejs.org/
# macOS (Homebrew): brew install node
# Windows: https://nodejs.org/ からインストーラをダウンロード

# リポジトリをクローン
git clone git@github.com:elvezjp/spec-code-ai-reviewer.git
cd spec-code-ai-reviewer
```

### システムLLM認証設定（AWS Bedrock）

**注意**: AWS環境がない場合、この設定は不要です。Web画面から設定ファイルをアップロードすることで、利用者自身がLLM認証情報を設定して使用できます（「[使い方](#使い方)」セクション参照）。

```bash
# 方法1: 環境変数
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_REGION=ap-northeast-1

# 方法2: .env ファイル
cp .env.example .env
# .env ファイルを編集してAWS認証情報を設定

# 方法3: AWS CLI でプロファイル設定
aws configure
```

### 起動

フロントエンドとバックエンドを別々に起動します。

**ターミナル1: バックエンド起動**

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

**ターミナル2: フロントエンド起動**

```bash
cd frontend
npm install
npm run dev
```

ブラウザで http://localhost:5173 にアクセス（Vite開発サーバー）

**注意**: フロントエンドはViteの開発サーバー（ポート5173）で起動し、APIリクエストはバックエンド（ポート8000）にプロキシされます。

### テスト実行

```bash
# バックエンドのテスト
cd backend
uv run pytest tests/ -v

# フロントエンドのテスト
cd frontend
npm test
```

## 環境変数

### システムLLM用（AWS Bedrock）

システムLLM（AWS Bedrock）の実行に利用される環境変数です。

**注意**: Web画面から設定ファイルをアップロードして実行した場合、そちらの設定が優先されます。（「[使い方](#使い方)」セクション参照）。

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `AWS_ACCESS_KEY_ID` | AWSアクセスキー | - |
| `AWS_SECRET_ACCESS_KEY` | AWSシークレットキー | - |
| `AWS_REGION` | AWSリージョン | `ap-northeast-1` |
| `BEDROCK_MODEL_ID` | 使用するモデルID | `global.anthropic.claude-haiku-4-5-20251001-v1:0` |
| `BEDROCK_MAX_TOKENS` | レスポンスの最大トークン数 | `16384` |

### ローカルLLM接続用

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `LLM_ALLOW_PRIVATE_BASE_URL` | `baseUrl` に内部ネットワーク宛のアドレス（`127.0.0.1` や `192.168.x.x` 等）を指定できるようにする | `false` |

OpenAI互換APIの接続先（`baseUrl`）は、既定では内部ネットワーク宛を拒否
します。この API は認証なしで公開されるため、検証しないとサーバーを
踏み台にして内部ネットワークやクラウドのメタデータエンドポイントへ到達
できてしまうためです。

**ローカルで動かしている LLM に接続する場合**は、この変数を有効にして
ください。

```bash
LLM_ALLOW_PRIVATE_BASE_URL=1
```

信頼できない相手がこの API を呼べる環境では、有効にしないでください。

---

## よくある質問と回答/トラブルシューティング

### 1. LLMモデルを複数登録できますが、これは何に使われますか？
設定ファイルでモデルを複数登録しておくことで、設定画面からレビュー実行に利用するモデルを選択して使用することができます。

### 2. OpenAI API使用時に「Connection error.」と表示される

ネットワークの問題が原因で発生することが多いエラーです。

**考えられる原因:**
- インターネット接続が不安定
- プロキシ環境でプロキシ設定がされていない
- ファイアウォールによるAPI通信のブロック
- VPN接続の問題

**対処方法:**
1. インターネット接続を確認する
2. プロキシ環境の設定を確認する
3. ファイアウォールで LLMプロバイダのAPI（`api.openai.com`等）への通信が許可されているか確認する

### 3. Bedrock使用時に「on-demand throughput isn't supported.」というエラーが表示される

```
ValidationException: Invocation of model ID amazon.nova-pro-v1:0 with on-demand throughput isn't supported.
Retry your request with the ID or ARN of an inference profile that contains this model.
```

**原因:**
- リージョンプレフィックス（`us.`や`apac.`）が付いていない
- モデルID名が間違っている

**対処方法:**
- AWSのBedrockモデルIDを確認する
- クロスリージョン推論の「推論プロファイルID」を指定する
  - エラーになる例: `amazon.nova-pro-v1:0`
  - 正しい例: `us.amazon.nova-pro-v1:0` または `apac.amazon.nova-pro-v1:0`

### 4. Bedrock使用時に「maximum tokens you requested exceeds the model limit」と表示される

出力トークン数の設定がモデルの上限を超えている場合に発生するエラーです。

```
The maximum tokens you requested exceeds the model limit of 10000.
Try again with a maximum tokens value that is lower than 10000.
```

**原因:**
- 設定ファイルの `max_tokens` がモデルの設定可能上限を超えている
  - Amazon Nova Lite / Micro / Pro: 10,000
  - Anthropic Claude Haiku 4.5: 16,384

**対処方法:**
- 設定ファイルジェネレータで設定ファイルを再作成する
- 設定ファイルで `max_tokens` をモデルの上限以下に設定する

---

## API エンドポイント

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/` | フロントエンド配信 |
| GET | `/api/health` | ヘルスチェック |
| POST | `/api/convert/excel-to-markdown` | Excel→Markdown変換 |
| POST | `/api/convert/word-to-markdown` | Word→Markdown変換 |
| POST | `/api/convert/add-line-numbers` | 行番号付与 |
| GET | `/api/convert/available-tools` | 利用可能な変換ツール一覧取得 |
| POST | `/api/review` | レビュー実行 |
| POST | `/api/test-connection` | LLM接続テスト |
| POST | `/api/review/structure-matching` | 構造マッチング（分割レビュー） |
| POST | `/api/review/group` | グループレビュー（分割レビュー） |
| POST | `/api/review/integrate` | 結果統合（分割レビュー） |
| POST | `/api/organize-markdown` | AIマークダウン整理 |
| POST | `/api/split/headings` | H2見出し一覧取得 |
| POST | `/api/split/markdown` | 設計書分割 |
| POST | `/api/split/code` | コード分割 |
| POST | `/api/summarize` | サマリー生成 |

## ディレクトリ構成

```
spec-code-ai-reviewer/
├── backend/                     # バックエンド（Python / FastAPI）
│   ├── app/
│   ├── tests/
│   ├── pyproject.toml           # バージョンはここで管理
│   └── uv.lock
├── frontend/                    # フロントエンド（Vite + React + TypeScript）
│   ├── src/
│   └── package.json
├── docs/                        # ドキュメント
│   ├── spec.md                  # アプリケーション仕様書
│   ├── config-file-generator-spec.md  # 設定ファイルジェネレーター仕様書
│   ├── split-review.md          # 分割レビュー機能の詳細
│   ├── ec2-deployment-spec.md   # （OLD）マルチバージョン構成時代のEC2デプロイ仕様書
│   └── tests/                   # 試験項目表
│       └── README.md
├── .env.example                 # 環境変数テンプレート（AWS Bedrock）
└── README.md                    # 本ファイル
```

## 関連プロジェクト

以下の外部ツールを依存関係として使用しています（uv により PyPI または git ソースからインストール。`backend/pyproject.toml` 参照）。

| パッケージ | リポジトリ | 説明 |
|-------------|-----------|------|
| add-line-numbers | https://github.com/elvezjp/add-line-numbers | ファイルに行番号を追加するツール |
| code2map | https://github.com/elvezjp/code2map | ソースコード→マインドマップ変換ツール |
| excel2md | https://github.com/elvezjp/excel2md | Excel→CSVマークダウン変換ツール |
| markitdown | https://github.com/microsoft/markitdown | 各種ファイル形式をMarkdownに変換するツール |
| md2map | https://github.com/elvezjp/md2map | Markdown→マインドマップ変換ツール |

ソースを参照したい場合は、各上流リポジトリを直接 clone してください（例: `git clone https://github.com/elvezjp/excel2md.git`）。これらのリポジトリは以前 git subtree として取り込まれており、その構成は `v0.9.9` タグに保存されています。

## バージョン管理

リポジトリのルートでは最新のコードのみを保持し、バージョン管理は git tag で行います。

- `main` ブランチには次バージョンの変更を [CHANGELOG_ja.md](CHANGELOG_ja.md) の `## [X.Y.Z] - Unreleased` 見出しの下に蓄積します
- リリース時に見出しの日付を確定し、`backend/pyproject.toml` のバージョン（およびフロントエンドのバージョン表記）を確認のうえ、`vX.Y.Z` タグを作成します

### 旧バージョンを利用する場合

旧バージョン（v0.5.0〜v0.9.9）は、以前は `versions/` ディレクトリ配下にスナップショットとして保持していました。この構成（マルチバージョン用インフラの nginx / PM2 / Docker 設定、subtree を含む）は `v0.9.9` タグに保存されています。

```bash
git checkout v0.9.9
# 旧バージョンは versions/v0.5.0 〜 versions/v0.9.9 配下にあります
```

**注意**: `v0.9.9` タグは旧構成のアーカイブ参照点のため、削除・付け替えを行わないでください。

## 更新履歴

詳細な変更履歴は [CHANGELOG_ja.md](CHANGELOG_ja.md) を参照してください。

## 貢献

貢献を歓迎します！ガイドラインは [CONTRIBUTING_ja.md](CONTRIBUTING_ja.md) を参照してください。

## セキュリティ

脆弱性の報告については [SECURITY_ja.md](SECURITY_ja.md) を参照してください。Dependabot アラートの運用方針も同ファイルに記載しています。

## 開発の背景

本ツールは、日本の開発現場でAIを活かすためのAI開発エコシステム **IXV（イクシブ）** の開発過程で生まれた小さな実用品です。

IXVでは、開発方法論とOSSを提供することで、AI活用を現場に根付かせる取り組みを進めており、本リポジトリでは、その一部を切り出して公開しています。

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照してください。

## 問い合わせ先

- **メールアドレス**: info@elvez.co.jp
- **宛先**: 株式会社エルブズ
