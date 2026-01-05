#!/bin/bash
set -e

BASE_PATH="/var/www/spec-code-verifier"

# latestシンボリックリンクの作成（存在しない場合）
if [ ! -L "$BASE_PATH/latest" ]; then
    ln -sf versions/v0.3.0 "$BASE_PATH/latest"
fi

# 各バージョンの依存関係をインストール
echo "Installing dependencies for latest version..."
cd "$BASE_PATH/latest/backend"
uv sync --frozen 2>/dev/null || uv sync

echo "Installing dependencies for v0.3.0..."
cd "$BASE_PATH/versions/v0.3.0/backend"
uv sync --frozen 2>/dev/null || uv sync

echo "Installing dependencies for v0.1.1..."
cd "$BASE_PATH/versions/v0.1.1/backend"
uv sync --frozen 2>/dev/null || uv sync

# 作業ディレクトリに戻る
cd "$BASE_PATH"

# 引数で渡されたコマンドを実行
exec "$@"
