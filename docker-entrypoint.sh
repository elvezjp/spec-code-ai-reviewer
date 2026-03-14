#!/bin/bash
set -e

BASE_PATH="/var/www/spec-code-ai-reviewer"

# latestシンボリックリンクの作成（存在しない場合）
# 最新バージョンを自動検出（バージョン番号でソートして最後のものを使用）
if [ ! -L "$BASE_PATH/latest" ]; then
    LATEST_VERSION=$(ls -d "$BASE_PATH/versions"/v* 2>/dev/null | sort -V | tail -1 | xargs basename)
    if [ -n "$LATEST_VERSION" ]; then
        ln -sf "versions/$LATEST_VERSION" "$BASE_PATH/latest"
        echo "Created symlink: latest -> versions/$LATEST_VERSION"
    fi
fi

# versions/配下の各バージョンの依存関係をインストール
# v0.8.0以降のみ起動対象
MIN_VERSION="0.8.0"

for VERSION_DIR in "$BASE_PATH/versions"/v*/; do
    VERSION_NAME=$(basename "$VERSION_DIR")
    VERSION_NUM="${VERSION_NAME#v}"
    # v0.8.0未満はスキップ
    if [ "$(printf '%s\n%s' "$MIN_VERSION" "$VERSION_NUM" | sort -V | head -1)" != "$MIN_VERSION" ]; then
        echo "Skipping $VERSION_NAME (below v$MIN_VERSION)"
        continue
    fi
    if [ -d "$VERSION_DIR/backend" ]; then
        echo "Installing backend dependencies for $VERSION_NAME..."
        cd "$VERSION_DIR/backend"
        uv sync --frozen 2>/dev/null || uv sync
    fi
    # v0.6.0以降: フロントエンドのビルド（package.jsonが存在する場合）
    if [ -f "$VERSION_DIR/frontend/package.json" ]; then
        VERSION_NAME=$(basename "$VERSION_DIR")
        echo "Building frontend for $VERSION_NAME..."
        cd "$VERSION_DIR/frontend"
        npm ci --prefer-offline 2>/dev/null || npm install
        npm run build
    fi
done

# 作業ディレクトリに戻る
cd "$BASE_PATH"

# 引数で渡されたコマンドを実行
exec "$@"
