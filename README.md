# 設計書-Javaプログラム突合 AIレビュアー

設計書（Excel形式）とプログラムコードをAIで突合し、整合性を検証するWebアプリケーション。

## 機能

- **設計書変換**: Excel (.xlsx, .xls) → Markdown形式に変換（MarkItDown、excel2md使用）
- **プログラム変換**: 任意のテキストファイルに行番号を付与（add-line-numbers準拠）
- **突合レビュー**: LLM（Bedrock / Anthropic / OpenAI）を使用して設計書とコードの整合性を検証
- **レポート出力**: マークダウン形式のレビューレポートを生成

機能仕様の詳細については[latest/spec.md](latest/spec.md)を参照してください。

## システム構成

- **フロントエンド**: 単一HTMLファイル + Tailwind CSS (CDN)
- **バックエンド**: Python / FastAPI
  - MarkItDown / excel2md (Excel→Markdown変換)
  - add-line-numbers準拠 (行番号付与)
  - マルチLLMプロバイダー対応 (Bedrock / Anthropic / OpenAI)

## 使い方

1. **設計書をアップロード**: Excel (.xlsx, .xls) ファイルを選択（複数可）
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

1. 画面右上の「設定」ボタンから設定モーダルを開く
2. [設定ファイルジェネレーター](/config-file-generator/)画面でLLMプロバイダー（Bedrock / Anthropic API / OpenAI API）を選択し、APIキーなど必要な情報を入力して設定ファイルを作成
3. 設定モーダルに戻って設定ファイルをアップロード
4. 使用するLLMモデルを選択（複数指定した場合）

## セットアップ

ローカル環境では以下の2通りの起動方法があります。

- **単一バージョン起動**: uvicornで直接起動（開発向け）
- **Docker Compose起動**: 本番環境と同等のマルチバージョン環境（動作確認向け）

本番環境（EC2）へのデプロイについては [EC2デプロイ仕様書](docs/ec2-deployment-spec.md) を参照してください。

### 前提条件

- Python 3.10以上
- [uv](https://docs.astral.sh/uv/) (Python パッケージマネージャー)

### インストール

```bash
# uv をインストール（未インストールの場合）
# 詳細: https://docs.astral.sh/uv/getting-started/installation/
curl -LsSf https://astral.sh/uv/install.sh | sh

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

# 方法2: AWS CLI でプロファイル設定
aws configure
```

### 単一バージョンで起動する場合

```bash
cd versions/v0.5.0/backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

ブラウザで http://localhost:8000 にアクセス

### Docker Composeで起動する場合（マルチバージョン対応）

本番環境と同等のバージョン切替機能を含む開発環境を起動できます。

```bash
# AWS認証情報を設定（システムLLMを使用する場合）
cp .env.example .env
# .env ファイルを編集してAWS認証情報を設定

# 起動
docker-compose up -d --build

# ブラウザでアクセス
open http://localhost:8000

# ログ確認
docker-compose logs -f

# 停止
docker-compose down
```

**注意**: AWS環境がない場合は `.env` ファイルの作成は不要です。Web画面から設定ファイルをアップロードすることで、Anthropic APIやOpenAI APIを使用できます。

画面左上のバルーンでバージョン切替が可能です（Cookie + Nginx mapによるルーティング）。

### テスト実行

各バージョンのバックエンドディレクトリでテストを実行します。

```bash
# v0.5.0 のテスト
cd versions/v0.5.0/backend
uv run pytest tests/ -v
```

### バージョン同期

バージョン番号は `backend/pyproject.toml` で一元管理しています。
フロントエンドのバージョン表記を同期するには：

```bash
python3 scripts/sync_version.py
```

このスクリプトは以下を行います：

1. **バージョン番号の同期**: 各 `backend/pyproject.toml` のバージョンを読み取り、対応する `frontend/index.html` の表示を更新
2. **VERSIONS配列の更新**: 全フロントエンドのバージョン切替UI用 `VERSIONS` 配列を、利用可能な全バージョンで更新

#### オプション

```bash
# 全バージョンを同期 + VERSIONS配列更新（デフォルト）
python3 scripts/sync_version.py

# 指定バージョンのみ同期（VERSIONS配列更新なし）
python3 scripts/sync_version.py v0.5.0

# VERSIONS配列の更新をスキップ
python3 scripts/sync_version.py --no-versions-array
```

## 環境変数（システムLLM用）

システムLLM（AWS Bedrock）の実行に利用される環境変数です。

**注意**: Web画面から設定ファイルをアップロードして実行した場合、そちらの設定が優先されます。（「[使い方](#使い方)」セクション参照）。

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `AWS_ACCESS_KEY_ID` | AWSアクセスキー | - |
| `AWS_SECRET_ACCESS_KEY` | AWSシークレットキー | - |
| `AWS_REGION` | AWSリージョン | `ap-northeast-1` |
| `BEDROCK_MODEL_ID` | 使用するモデルID | `global.anthropic.claude-haiku-4-5-20251001-v1:0` |
| `BEDROCK_MAX_TOKENS` | レスポンスの最大トークン数 | `16384` |

## API エンドポイント

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/` | フロントエンド配信 |
| GET | `/api/health` | ヘルスチェック |
| POST | `/api/convert/excel-to-markdown` | Excel→Markdown変換 |
| POST | `/api/convert/add-line-numbers` | 行番号付与 |
| GET | `/api/convert/available-tools` | 利用可能な変換ツール一覧取得 |
| POST | `/api/review` | レビュー実行 |

## ディレクトリ構成

```
spec-code-ai-reviewer/
├── docker-compose.yml           # Docker Compose設定（マルチバージョン開発用）
├── Dockerfile.dev               # 開発用Dockerfile（Ubuntu）
├── docker-entrypoint.sh         # Docker起動スクリプト
├── ecosystem.config.js          # PM2設定（本番用）
├── dev.ecosystem.config.js      # PM2設定（開発用）
├── nginx/
│   ├── dev.conf                 # 開発用Nginx設定
│   ├── spec-code-ai-reviewer.conf  # 本番用Nginx設定
│   └── version-map.conf         # バージョン切替map（共通）
├── latest -> versions/v0.5.0    # シンボリックリンク（最新版を指す）
│
├── versions/                    # 全バージョン格納
│   ├── README.md                # バージョン管理説明
│   └── v0.5.0/                  # 最新版
│       ├── backend/
│       ├── frontend/
│       ├── config-file-generator-spec.md
│       └── spec.md
│
├── docs/                        # ドキュメント
│   └── ec2-deployment-spec.md   # EC2デプロイ仕様書
│
├── scripts/                     # ユーティリティスクリプト
│   └── sync_version.py          # バージョン同期スクリプト
│
├── tests/                       # 試験項目表
│   └── README.md
│
├── add-line-numbers/            # サブツリー（elvezjp）
├── excel2md/                    # サブツリー（elvezjp）
├── markitdown/                  # サブツリー（Microsoft）
└── README.md                    # 本ファイル
```

## Git Subtrees

このリポジトリには以下の外部リポジトリを git subtree で追加しています。

| ディレクトリ | リポジトリ | 説明 |
|-------------|-----------|------|
| `add-line-numbers/` | https://github.com/elvezjp/add-line-numbers | ファイルに行番号を追加するツール |
| `excel2md/` | https://github.com/elvezjp/excel2md | Excel→CSVマークダウン変換ツール |
| `markitdown/` | https://github.com/microsoft/markitdown | 各種ファイル形式をMarkdownに変換するツール |

### Subtree の更新方法

```bash
# add-line-numbers を更新
git subtree pull --prefix=add-line-numbers https://github.com/elvezjp/add-line-numbers.git main --squash

# excel2md を更新
git subtree pull --prefix=excel2md https://github.com/elvezjp/excel2md.git main --squash

# markitdown を更新
git subtree pull --prefix=markitdown https://github.com/microsoft/markitdown.git main --squash
```

## バージョン管理

### ポート割り当てルール

セマンティックバージョニング（`vX.Y.Z`）に対応したポート割り当てルールを採用しています。

```
ポート番号 = 8000 + (マイナーバージョン × 10) + パッチバージョン
例: v0.2.5 → 8000 + (2 × 10) + 5 = 8025
```

| バージョン | ポート |
|-----------|-------|
| v0.5.0 (latest) | 8050 |

### 新しいバージョンを追加する際の変更箇所

新バージョン（例: v0.6.0）を追加する場合、以下のファイルを修正します。

| ファイル | 変更内容 |
|---------|---------|
| `versions/v0.6.0/` | 新バージョンのコードを配置 |
| `docker-compose.yml` | backendのexposeに新ポートを追加、nginxのvolumesに新フロントエンドを追加 |
| `nginx/version-map.conf` | mapに新バージョンのルーティングを追加（dev/本番共通） |
| `versions/v0.5.0/frontend/index.html` | VERSIONS配列に新バージョンを追加 |
| `docs/20251218version-switching-design.md` | ポート割り当て表を更新 |
| `ecosystem.config.js` | VERSIONS配列に新バージョンを追加（下記参照） |
| `dev.ecosystem.config.js` | VERSIONS配列に新バージョンを追加 |

最新版を切り替える場合は追加で以下も変更：

| ファイル | 変更内容 |
|---------|---------|
| `latest` シンボリックリンク | 新バージョンを指すように更新（`rm latest && ln -s versions/v0.6.0 latest`） |
| `nginx/version-map.conf` | defaultのポートを新バージョンに変更 |

#### ecosystem.config.js への追加例

VERSIONS配列に新バージョンを追加します。`latest`はシンボリックリンクのため、実体バージョンのみ起動します：

```javascript
const VERSIONS = [
  // latestはシンボリックリンクのため、実体バージョンのみ起動
  { name: 'spec-code-ai-reviewer-v0.6.0', cwd: 'versions/v0.6.0', port: 8060 },  // 追加
  { name: 'spec-code-ai-reviewer-v0.5.0', cwd: 'versions/v0.5.0', port: 8050 },
];
```

**注意**: `latest`用のプロセスは不要です。Nginxの`version-map.conf`で`default`ポートが最新版を指すため、Cookie未設定時も最新版にルーティングされます。

**注意**: `PYTHONPATH` に `add-line-numbers` サブツリーのパスが設定されており、`add_line_numbers` モジュールをインポート可能にしています。

#### nginx/version-map.conf への追加例

```nginx
# Cookie値に応じてバックエンドポートを振り分け
map $cookie_app_version $backend_port {
    "v0.6.0"  8060;  # 追加
    "v0.5.0"  8050;
    default   8060;  # latest (v0.6.0)
}

# Cookie値に応じてフロントエンドを振り分け
map $cookie_app_version $frontend_root {
    "v0.6.0"  /var/www/spec-code-ai-reviewer/versions/v0.6.0/frontend;  # 追加
    "v0.5.0"  /var/www/spec-code-ai-reviewer/versions/v0.5.0/frontend;
    default   /var/www/spec-code-ai-reviewer/latest/frontend;
}
```

### 本番環境での更新手順

```bash
# （ローカルPCで実行）GitHubに登録済みの公開鍵に対応する「秘密鍵」をssh-agentへ追加
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa   # 鍵ファイル名が異なる場合は適宜変更

# サーバーにSSH接続（ssh-agent転送でGitHubアクセス可能にする）
ssh -A user@example.com

# 新バージョンをデプロイ
cd /var/www/spec-code-ai-reviewer
git pull origin main

# 依存関係をインストール
cd versions/v0.5.0/backend
uv sync

# PM2でプロセスを再構成（新バージョンのプロセスを追加）
cd /var/www/spec-code-ai-reviewer
pm2 delete all
pm2 start ecosystem.config.js
pm2 save

# Nginx設定を反映（version-map.confの変更を反映）
sudo cp nginx/version-map.conf /etc/nginx/conf.d/
sudo nginx -t
sudo nginx -s reload
```

**補足:**
- `latest` シンボリックリンクは `git pull` で自動更新される（Gitがシンボリックリンクを追跡）
- `pm2 reload` は既存プロセスの再起動のみ。新バージョン追加時は `pm2 delete all && pm2 start` で再構成が必要
- `spec-code-ai-reviewer.conf` は `$backend_port` 変数を使用するため、`version-map.conf` の更新のみでOK

## 開発の背景

本ツールは、日本語の開発文書・仕様書を対象とした開発支援AI **IXV（イクシブ）** の開発過程で生まれた小さな実用品です。

IXVでは、システム開発における日本語の文書について、理解・構造化・活用という課題に取り組んでおり、本リポジトリでは、その一部を切り出して公開しています。

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照してください。

## 問い合わせ先

- **メールアドレス**: info@elvez.co.jp
- **宛先**: 株式会社エルブズ
