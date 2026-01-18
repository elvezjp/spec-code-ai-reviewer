// バージョン定義
// 新バージョン追加時はここに1行追加するだけ
// latestはシンボリックリンクのため、実体バージョンのみ起動
const VERSIONS = [
  // workers: 複数リクエスト同時処理用（LLM API呼び出しは同期ブロッキングのため複数ワーカーが必要）
  { name: 'spec-code-ai-reviewer-v0.6.0', cwd: 'versions/v0.6.0', port: 8060, workers: 1 },
  { name: 'spec-code-ai-reviewer-v0.5.2', cwd: 'versions/v0.5.2', port: 8052, workers: 1 },
  { name: 'spec-code-ai-reviewer-v0.5.1', cwd: 'versions/v0.5.1', port: 8051, workers: 1 },
  { name: 'spec-code-ai-reviewer-v0.5.0', cwd: 'versions/v0.5.0', port: 8050, workers: 1 },
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
