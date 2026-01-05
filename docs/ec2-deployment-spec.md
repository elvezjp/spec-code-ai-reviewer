# EC2デプロイ仕様書

本ドキュメントは、設計書-Javaプログラム突合 AIレビュアー（spec-code-ai-reviewer）のEC2デプロイに関する仕様を定義する。

**関連仕様書:**
- [spec.md](../latest/spec.md)

---

## 1. 構成概要

```
[ユーザー]
    │
    │ HTTPS (443)
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Route 53                                  │
│                 example.com                              │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│              Application Load Balancer (ALB)                 │
│                                                              │
│  - HTTPS (443) → ACM証明書                                   │
│  - ターゲットグループ → EC2:80                                │
└─────────────────────────────────────────────────────────────┘
    │
    │ HTTP (80)
    ▼
┌─────────────────────────────────────────────────────────────┐
│                      EC2 Instance                            │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    nginx (:80)                       │    │
│  │                                                      │    │
│  │  Cookie: app_version で振り分け（map方式）           │    │
│  │                                                      │    │
│  │  /              → $frontend_root (バージョン別)     │    │
│  │  /api/*         → http://127.0.0.1:$backend_port    │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                   │
│            ┌─────────────┼─────────────┐                    │
│            ▼             ▼             ▼                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ PM2: latest  │ │ PM2: v0.1.1  │ │ PM2: v0.x.x  │        │
│  │   :8025      │ │   :8011      │ │   :80xx      │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              IAM Role                                │    │
│  │              (Bedrock アクセス権限)                   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│              LLM プロバイダー（設定ファイルで切替）           │
│                                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ AWS Bedrock  │ │  Anthropic   │ │   OpenAI     │        │
│  │ (デフォルト) │ │     API      │ │     API      │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 2. AWS リソース構成

| リソース | 設定 |
|----------|------|
| ドメイン | example.com |
| Route 53 | ALBへのAレコード（エイリアス） |
| ACM | example.com の SSL/TLS 証明書 |
| ALB | HTTPS (443) リスナー、HTTP→HTTPS リダイレクト |
| ターゲットグループ | EC2インスタンス:80、ヘルスチェック: /health |
| EC2 | Ubuntu 24.04 LTS / t3.small以上 |
| セキュリティグループ (ALB) | インバウンド: 443 (0.0.0.0/0) |
| セキュリティグループ (EC2) | インバウンド: 80 (ALBのSGから), 22 (管理用) |
| IAM ロール | EC2用、Bedrock InvokeModel 権限 |

## 3. ディレクトリ構成

全バージョンを統一的に管理し、シンボリックリンクで最新版を参照する方式を採用。

```
/var/www/spec-code-ai-reviewer/
├── latest -> versions/v0.2.5       # シンボリックリンク（最新版を指す）
│
├── versions/                       # 全バージョン格納（統一構造）
│   ├── v0.2.5/                     # 最新版
│   │   ├── backend/
│   │   └── frontend/
│   └── v0.1.1/                     # 旧版
│       ├── backend/
│       └── frontend/
│
├── add-line-numbers/               # サブツリー（共通）
├── markitdown/                     # サブツリー（共通）
│
├── ecosystem.config.js             # PM2設定
└── nginx/
    ├── spec-code-ai-reviewer.conf     # nginx server設定
    └── version-map.conf            # バージョン切替map設定
```

## 4. ポート割り当て

### 4.1 ポート割り当てルール

セマンティックバージョニング（`vX.Y.Z`）に対応したポート割り当てルールを採用。

```
ポート番号 = 8000 + (マイナーバージョン × 10) + パッチバージョン
例: v0.2.5 → 8000 + (2 × 10) + 5 = 8025
```

### 4.2 現在のポート割り当て

| バージョン | ポート | 計算式 | PM2プロセス名 |
|-----------|-------|--------|--------------|
| v0.2.5 (latest) | 8025 | 8000 + 2×10 + 5 | spec-code-ai-reviewer |
| v0.1.1 | 8011 | 8000 + 1×10 + 1 | spec-code-ai-reviewer-v0.1.1 |

### 4.3 注意事項

- パッチバージョンが10以上になる場合は、次のマイナーバージョンのポート帯と重複するため、連番管理に切り替える
- 例: v0.2.10 は 8030 となり v0.3.0 と衝突 → この場合は設定ファイルで個別管理

## 5. EC2 セットアップ手順

### 5.1 前提条件

- Ubuntu 24.04 LTS AMI
- IAMロールがアタッチ済み（Bedrock アクセス権限）
- セキュリティグループ設定済み

### 5.2 初期セットアップ

```bash
# パッケージ更新
sudo apt update && sudo apt upgrade -y

# 必要なパッケージのインストール
sudo apt install -y git nginx python3-venv

# uv のインストール
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# SSH鍵の登録（事前にEC2に秘密鍵を配置しておく）
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519  # または id_rsa など、使用する鍵ファイル

# GitHub への接続確認
ssh -T git@github.com

# アプリケーションディレクトリの作成
sudo mkdir -p /var/www
cd /var/www

# リポジトリのクローン（SSH URL）
sudo -E git clone git@github.com:elvezjp/spec-code-ai-reviewer.git
sudo chown -R ubuntu:ubuntu spec-code-ai-reviewer
```

### 5.3 バックエンドのセットアップ

```bash
cd /var/www/spec-code-ai-reviewer

# 各バージョンの依存関係をインストール
cd versions/v0.2.5/backend
uv sync

cd /var/www/spec-code-ai-reviewer/versions/v0.1.1/backend
uv sync

# 動作確認（最新版）
cd /var/www/spec-code-ai-reviewer/latest/backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8025
```

### 5.4 PM2 によるプロセス管理

```bash
# Node.js と PM2 のインストール
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2

# ログディレクトリの作成
sudo mkdir -p /var/log/pm2
sudo chown ubuntu:ubuntu /var/log/pm2

# PM2 でバックエンドを起動（設定ファイルを使用）
cd /var/www/spec-code-ai-reviewer
pm2 start ecosystem.config.js

# PM2 の自動起動設定
pm2 startup
# 表示されたコマンドを実行（例）
sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u ubuntu --hp /home/ubuntu
pm2 save

# ステータス確認
pm2 status
pm2 logs
```

**PM2 設定ファイル（ecosystem.config.js）:**

```javascript
// バージョン定義
// 新バージョン追加時はここに1行追加するだけ
// workers: 複数リクエスト同時処理に必要なワーカー数（省略時は1）
const VERSIONS = [
  { name: 'spec-code-ai-reviewer-v0.5.0', cwd: 'versions/v0.5.0', port: 8050, workers: 1 },
  { name: 'spec-code-ai-reviewer-v0.4.0', cwd: 'versions/v0.4.0', port: 8040, workers: 1 },
  { name: 'spec-code-ai-reviewer-v0.3.0', cwd: 'versions/v0.3.0', port: 8030, workers: 1 },
  { name: 'spec-code-ai-reviewer-v0.2.5', cwd: 'versions/v0.2.5', port: 8025, workers: 1 },
  { name: 'spec-code-ai-reviewer-v0.1.1', cwd: 'versions/v0.1.1', port: 8011, workers: 1 },
];

// 共通設定
const BASE_PATH = '/var/www/spec-code-ai-reviewer';
const commonConfig = {
  script: 'uv',
  interpreter: 'none',
  env: {
    AWS_REGION: 'ap-northeast-1',
    CORS_ORIGINS: 'https://example.com',
    PYTHONPATH: `${BASE_PATH}/add-line-numbers`,
  },
  // ログ設定
  log_date_format: 'YYYY-MM-DD HH:mm:ss',
  merge_logs: true,
  // 再起動設定
  autorestart: true,
  max_restarts: 10,
  restart_delay: 3000,
  // 監視設定（開発時のみ有効化）
  watch: false,
  ignore_watch: ['node_modules', '.git', '__pycache__', '.venv'],
};

module.exports = {
  apps: VERSIONS.map(v => ({
    ...commonConfig,
    name: v.name,
    cwd: `${BASE_PATH}/${v.cwd}/backend`,
    args: `run uvicorn app.main:app --host 127.0.0.1 --port ${v.port} --workers ${v.workers || 1}`,
    error_file: `/var/log/pm2/${v.name}-error.log`,
    out_file: `/var/log/pm2/${v.name}-out.log`,
  })),
};
```

**ワーカー数について:**

Uvicornはデフォルトで1ワーカーで起動するため、同期的なブロッキング処理（LLM API呼び出し等）が含まれる場合、リクエストは直列処理されます。複数のリクエストを同時に処理するには、`--workers`オプションで複数ワーカーを起動する必要があります。

| ワーカー数 | 用途 |
|-----------|------|
| 1 | 単一リクエスト処理（旧バージョン向け） |
| 4 | 複数ユーザーのリクエストを同時に処理 |

※ ワーカー数を増やすとメモリ消費も増加します（1ワーカーあたり約50〜100MB）

**PM2 コマンド一覧:**

| コマンド | 説明 |
|----------|------|
| `pm2 start ecosystem.config.js` | 設定ファイルで起動 |
| `pm2 stop all` | 全プロセス停止 |
| `pm2 restart all` | 全プロセス再起動 |
| `pm2 reload ecosystem.config.js` | ダウンタイムなし再起動 |
| `pm2 logs` | 全プロセスのログ表示 |
| `pm2 logs spec-code-ai-reviewer` | 特定プロセスのログ表示 |
| `pm2 status` | ステータス確認 |
| `pm2 monit` | モニタリング |

### 5.5 nginx 設定

```bash
# デフォルトサイトの無効化
sudo rm /etc/nginx/sites-enabled/default

# Basic認証用ツールのインストール
sudo apt install -y apache2-utils

# 認証ファイルの作成（初回）
sudo htpasswd -c /etc/nginx/.htpasswd <ユーザー名>
# パスワードを入力

# ユーザー追加（2人目以降）
sudo htpasswd /etc/nginx/.htpasswd <ユーザー名>

# 設定ファイルのコピー
sudo cp /var/www/spec-code-ai-reviewer/nginx/version-map.conf /etc/nginx/conf.d/
sudo cp /var/www/spec-code-ai-reviewer/nginx/spec-code-ai-reviewer.conf /etc/nginx/sites-available/

# シンボリックリンク作成
sudo ln -s /etc/nginx/sites-available/spec-code-ai-reviewer.conf /etc/nginx/sites-enabled/

# 設定テスト
sudo nginx -t

# nginx の有効化と起動
sudo systemctl enable nginx
sudo systemctl start nginx
```

**バージョン切替map設定（nginx/version-map.conf）:**

```nginx
# バージョン切替用 map 設定
# 新バージョン追加時はここを更新

# Cookie値に応じてバックエンドポートを振り分け
map $cookie_app_version $backend_port {
    "v0.1.1"  8011;
    default   8025;  # latest (v0.2.5)
}

# Cookie値に応じてフロントエンドを振り分け
map $cookie_app_version $frontend_root {
    "v0.1.1"  /var/www/spec-code-ai-reviewer/versions/v0.1.1/frontend;
    default   /var/www/spec-code-ai-reviewer/latest/frontend;
}
```

**server設定（nginx/spec-code-ai-reviewer.conf）:**

```nginx
server {
    listen 80;
    server_name example.com;

    # Basic認証
    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;

    # ファイルアップロード制限
    client_max_body_size 15M;

    # フロントエンド（静的ファイル）
    location / {
        root $frontend_root;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API プロキシ
    location /api/ {
        proxy_pass http://127.0.0.1:$backend_port;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # タイムアウト設定（レビュー処理用）
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # ALBヘルスチェック用（認証除外、LLM接続テストなし）
    location /health {
        auth_basic off;
        set $health_backend 127.0.0.1:$backend_port;
        proxy_pass http://$health_backend/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

**認証ユーザーの管理:**

| コマンド | 説明 |
|----------|------|
| `sudo htpasswd /etc/nginx/.htpasswd user` | ユーザー追加 |
| `sudo htpasswd -D /etc/nginx/.htpasswd user` | ユーザー削除 |
| `sudo cat /etc/nginx/.htpasswd` | ユーザー一覧確認 |

## 6. IAM ロール設定（Bedrock使用時）

EC2インスタンスにIAMロールをアタッチすることで、アクセスキーを使用せずにBedrockにアクセスできる。

**注意**: 本設定はAWS Bedrockを使用する場合に必要です。設定ファイル（`reviewer-config.md`）でプロバイダーを指定しない場合、デフォルトでBedrockが使用されるため、この設定が必須となります。Anthropic APIまたはOpenAI APIのみを使用する場合は、環境変数でAPIキーを設定するだけで動作します。

### 6.1 なぜIAMロールを使うのか

| 方式 | リスク | 管理負担 |
|------|--------|----------|
| アクセスキー | 漏洩リスク高、ハードコードの危険性 | ローテーション管理が必要 |
| **IAMロール** | 一時認証情報のため漏洩リスクほぼゼロ | 自動ローテーション、管理不要 |

### 6.2 仕組み

1. EC2インスタンスにIAMロールをアタッチ
2. boto3が自動的にインスタンスメタデータサービスから一時認証情報を取得
3. アプリケーションコードに認証情報を記述する必要がない

### 6.3 IAMロールの作成手順

1. **IAMロールを作成**
   - 信頼されたエンティティ: AWS サービス → EC2
   - ロール名: `[日付]spec-code-ai-reviewer-ec2`

2. **カスタムポリシーをアタッチ**
   - ポリシー名: `[日付]spec-code-ai-reviewer-ec2-allow-bedrock-invoke-model`

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": [
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
                "arn:aws:bedrock:*:[your-account-id]:inference-profile/*"
            ]
        }
    ]
}
```

3. **EC2インスタンスにロールをアタッチ**
   - EC2コンソール → インスタンス → アクション → セキュリティ → IAMロールを変更
   - 作成したロールを選択

### 6.4 動作確認

```bash
# EC2インスタンス上で実行
# IAMロールが正しく設定されていれば、認証情報なしでAWS CLIが動作する
aws sts get-caller-identity

# 出力例
{
    "UserId": "AROA...:i-0123456789abcdef0",
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/[日付]spec-code-ai-reviewer-ec2/i-0123456789abcdef0"
}
```

※ boto3は自動的にIAMロールの認証情報を使用するため、アプリケーションコードの変更は不要

## 7. ALB 設定

### 7.1 リスナールール

| プロトコル | ポート | アクション |
|-----------|--------|-----------|
| HTTPS | 443 | ターゲットグループへ転送 |
| HTTP | 80 | HTTPS へリダイレクト |

### 7.2 ターゲットグループ

| 項目 | 設定 |
|------|------|
| ターゲットタイプ | インスタンス |
| プロトコル | HTTP |
| ポート | 80 |
| ヘルスチェックパス | /api/health |
| ヘルスチェック間隔 | 30秒 |
| 正常しきい値 | 2 |
| 異常しきい値 | 3 |

## 8. CORS 設定

CORS設定は環境変数 `CORS_ORIGINS` で制御する。

| 環境 | CORS_ORIGINS | 説明 |
|------|--------------|------|
| ローカル開発 | 未設定（デフォルト: `*`） | 全オリジン許可 |
| 本番（EC2） | `https://example.com` | 本番ドメインのみ許可 |

**実装（backend/app/main.py）:**

```python
cors_origins_str = os.getenv("CORS_ORIGINS", "*")
cors_origins = ["*"] if cors_origins_str == "*" else [o.strip() for o in cors_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

※ EC2ではnginxが同一オリジンで配信するため、実際にはCORSは発生しないが、セキュリティポリシーとして明示的に制限している

## 9. デプロイ・更新手順

### 9.1 通常の更新

```bash
# EC2 にSSH接続後
cd /var/www/spec-code-ai-reviewer

# 最新コードの取得
git pull origin main

# バックエンドの依存関係更新（必要な場合）
cd versions/v0.2.5/backend
uv sync

# バックエンドの再起動
cd /var/www/spec-code-ai-reviewer
pm2 reload ecosystem.config.js

# nginx の再読み込み（設定変更時）
sudo cp nginx/version-map.conf /etc/nginx/conf.d/
sudo nginx -t
sudo nginx -s reload
```

### 9.2 新バージョン追加時

新バージョン（例: v0.3.0）を追加する場合の手順：

```bash
# 1. 新バージョンのコードを配置
cd /var/www/spec-code-ai-reviewer
git pull origin main

# 2. 依存関係をインストール
cd versions/v0.3.0/backend
uv sync

# 3. PM2でプロセス再起動（VERSIONS配列の変更を反映）
cd /var/www/spec-code-ai-reviewer
pm2 reload ecosystem.config.js
pm2 save

# 4. Nginx設定を反映（version-map.confの変更を反映）
sudo cp nginx/version-map.conf /etc/nginx/conf.d/
sudo nginx -t
sudo nginx -s reload
```

### 9.3 最新版の切り替え

```bash
# シンボリックリンクを新バージョンに切り替え
cd /var/www/spec-code-ai-reviewer
rm latest
ln -s versions/v0.3.0 latest

# PM2を再起動
pm2 reload ecosystem.config.js
```

## 10. ログ確認

```bash
# PM2の全プロセスのログ
pm2 logs

# 特定プロセスのログ
pm2 logs spec-code-ai-reviewer
pm2 logs spec-code-ai-reviewer-v0.1.1

# ログファイル直接参照
tail -f /var/log/pm2/spec-code-ai-reviewer-out.log
tail -f /var/log/pm2/spec-code-ai-reviewer-error.log

# nginx のアクセスログ
sudo tail -f /var/log/nginx/access.log

# nginx のエラーログ
sudo tail -f /var/log/nginx/error.log
```

## 11. バージョン追加時の変更箇所一覧

新バージョン追加時に変更が必要なファイル：

| ファイル | 変更内容 |
|---------|---------|
| `versions/vX.Y.Z/` | 新バージョンのコードを配置 |
| `nginx/version-map.conf` | mapに新バージョンのルーティングを追加 |
| `ecosystem.config.js` | VERSIONS配列に新バージョンを追加 |
| `versions/*/frontend/index.html` | VERSIONS配列に新バージョンを追加（sync_version.pyで自動化可） |

最新版を切り替える場合は追加で以下も変更：

| ファイル | 変更内容 |
|---------|---------|
| `latest` シンボリックリンク | 新バージョンを指すように更新 |
| `nginx/version-map.conf` | defaultのポートを新バージョンに変更 |
