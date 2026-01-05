"""設計書-Javaプログラム突合 AIレビュアー バックエンド"""

import os
from importlib.metadata import version

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routers import convert, review

# pyproject.tomlからバージョンを取得
APP_VERSION = version("spec-code-verifier-backend")

app = FastAPI(
    title="設計書-Javaプログラム突合 AIレビュアー API",
    description="設計書とプログラムコードを突合し、整合性を検証するAPI",
    version=APP_VERSION,
)

# CORS設定（環境変数で制御、デフォルトは全許可）
# 本番環境では CORS_ORIGINS=https://example.com を設定
cors_origins_str = os.getenv("CORS_ORIGINS", "*")
cors_origins = ["*"] if cors_origins_str == "*" else [o.strip() for o in cors_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(convert.router, prefix="/api/convert", tags=["convert"])
app.include_router(review.router, prefix="/api", tags=["review"])

# フロントエンドの静的ファイル配信
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"

# 静的ファイル（画像など）を配信
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")


@app.get("/health")
async def health_check():
    """ヘルスチェック（ルートレベル）- ALB用"""
    return {"status": "healthy", "version": APP_VERSION}
