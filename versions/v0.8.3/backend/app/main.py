"""設計書-Javaプログラム突合 AIレビュアー バックエンド"""

import os
from importlib.metadata import version

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routers import convert, review, organize, split

# pyproject.tomlからバージョンを取得
APP_VERSION = version("spec-code-ai-reviewer-backend")

app = FastAPI(
    title="設計書-Javaプログラム突合 AIレビュアー API",
    description="設計書とプログラムコードを突合し、整合性を検証するAPI",
    version=APP_VERSION,
)

# CORS設定（環境変数で制御）
# 本番環境では CORS_ORIGINS=https://example.com を設定
# 未設定時はローカル開発用オリジンのみ許可（v0.8.3で全許可デフォルトを廃止）
_DEV_ORIGINS = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:8000,http://127.0.0.1:8000"
)
cors_origins_str = os.getenv("CORS_ORIGINS", _DEV_ORIGINS)
if cors_origins_str == "*":
    # ワイルドカード指定時は credentials を無効化する（ブラウザ仕様上も併用不可）
    cors_origins = ["*"]
    cors_allow_credentials = False
else:
    cors_origins = [o.strip() for o in cors_origins_str.split(",")]
    cors_allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_allow_credentials,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(convert.router, prefix="/api/convert", tags=["convert"])
app.include_router(review.router, prefix="/api", tags=["review"])
app.include_router(organize.router, prefix="/api", tags=["organize"])
app.include_router(split.router, prefix="/api", tags=["split"])

# フロントエンドの静的ファイル配信
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"

# 静的ファイル（画像など）を配信
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")


@app.get("/health")
async def health_check():
    """ヘルスチェック（ルートレベル）- ALB用"""
    return {"status": "healthy", "version": APP_VERSION}
