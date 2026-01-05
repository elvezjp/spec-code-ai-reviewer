// 開発環境用 PM2 設定
// 本番環境と同じパス構成を使用

// バージョン定義
const VERSIONS = [
  // latestはシンボリックリンクのため、実体バージョンのみ起動
  // workers: 複数リクエスト同時処理用（LLM API呼び出しは同期ブロッキングのため複数ワーカーが必要）
  { name: 'spec-code-ai-reviewer-v0.5.0', cwd: 'versions/v0.5.0', port: 8050, workers: 1 },
];

// 共通設定
const BASE_PATH = '/var/www/spec-code-ai-reviewer';
const commonConfig = {
  script: 'uv',
  interpreter: 'none',
  env: {
    AWS_REGION: process.env.AWS_REGION || 'ap-northeast-1',
    AWS_ACCESS_KEY_ID: process.env.AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY: process.env.AWS_SECRET_ACCESS_KEY,
    PYTHONPATH: `${BASE_PATH}/add-line-numbers`,
  },
  // ログ設定（Docker内では標準出力に出力）
  log_date_format: 'YYYY-MM-DD HH:mm:ss',
  merge_logs: true,
  // 再起動設定
  autorestart: true,
  max_restarts: 10,
  restart_delay: 3000,
  // 開発時はファイル監視を有効化
  watch: true,
  watch_delay: 1000,
  ignore_watch: ['node_modules', '.git', '__pycache__', '.venv', '*.log', '*.pyc', /\/__pycache__\//],
};

module.exports = {
  apps: VERSIONS.map(v => ({
    ...commonConfig,
    name: v.name,
    cwd: `${BASE_PATH}/${v.cwd}/backend`,
    args: `run uvicorn app.main:app --host 0.0.0.0 --port ${v.port} --workers ${v.workers || 1}`,
  })),
};
