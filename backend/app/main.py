"""設計書-Javaプログラム突合 AIレビュアー バックエンド"""

import os
from importlib.metadata import version

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routers import convert, review, organize, split, summarize

# pyproject.tomlからバージョンを取得
APP_VERSION = version("spec-code-ai-reviewer-backend")

app = FastAPI(
    title="設計書-Javaプログラム突合 AIレビュアー API",
    description="設計書とプログラムコードを突合し、整合性を検証するAPI",
    version=APP_VERSION,
)

# CORS設定（環境変数 CORS_ORIGINS で制御）
# 既定はローカル開発用オリジンのみを許可する。この API は認証がないため、
# 既定を全許可にすると、任意のサイトがブラウザ経由でこの API を呼び出し、
# 応答（レビュー対象のコードや設計書）を読めてしまう。
# 本番環境では CORS_ORIGINS=https://example.com のように明示的に指定する。
#
# なお、このアプリのフロントエンドは常に同一オリジンから API を呼ぶため
# （開発時は Vite の proxy、本番は同じ FastAPI が StaticFiles で配信）、
# 既定の許可リストは、フロントエンドを別ホストで動かす構成向けの保険である。
DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",  # Vite 開発サーバー
    "http://127.0.0.1:5173",
    "http://localhost:4173",  # Vite プレビュー（npm run preview）
    "http://127.0.0.1:4173",
]

cors_origins_str = os.getenv("CORS_ORIGINS", "").strip()
if not cors_origins_str:
    cors_origins = DEFAULT_CORS_ORIGINS
elif cors_origins_str == "*":
    # 全許可は明示的に指定された場合のみ。下の allow_credentials で
    # 認証情報の許可を落とす。
    cors_origins = ["*"]
else:
    cors_origins = [o.strip() for o in cors_origins_str.split(",") if o.strip()]
# オリジンを限定していない状態で認証情報を許可すると、Starlette は
# Access-Control-Allow-Origin にリクエスト元の Origin をそのまま返す
# （ワイルドカードと認証情報は併用できない仕様のため）。結果として
# 任意のサイトがこの API へ資格情報付きで到達し、応答を読めてしまう。
# ローカル起動中に利用者が悪意あるページを開くと、レビュー対象の
# コードや設計書が読み取られうるため、全許可のときは認証情報を許可しない。
allow_credentials = cors_origins != ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(convert.router, prefix="/api/convert", tags=["convert"])
app.include_router(review.router, prefix="/api", tags=["review"])
app.include_router(organize.router, prefix="/api", tags=["organize"])
app.include_router(split.router, prefix="/api", tags=["split"])
app.include_router(summarize.router, prefix="/api", tags=["summarize"])

# ヘルスチェック（StaticFilesマウントより前に定義する必要がある）
async def _health_response():
    """ヘルスチェック共通ロジック"""
    return {"status": "healthy", "version": APP_VERSION}


@app.get("/health")
async def health_check():
    """ヘルスチェック（ルートレベル）- ALB用"""
    return await _health_response()


@app.get("/api/health")
async def api_health_check():
    """ヘルスチェック（API配下）- フロントエンド用"""
    return await _health_response()


# フロントエンドの静的ファイル配信
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"

# 静的ファイル（画像など）を配信
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
