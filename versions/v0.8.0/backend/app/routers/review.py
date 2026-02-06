"""レビューAPI"""

from importlib.metadata import version

from fastapi import APIRouter

from app.models.schemas import (
    LLMConfig,
    ReviewRequest,
    ReviewResponse,
    TestConnectionRequest,
    TestConnectionResponse,
)
from app.services.llm_service import get_llm_provider

# pyproject.tomlからバージョンを取得
APP_VERSION = version("spec-code-ai-reviewer-backend")

router = APIRouter()

# ファイルサイズ制限（変換済みテキストベース）
MAX_DESIGN_SIZE = 10 * 1024 * 1024  # 10MB
MAX_CODE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/review", response_model=ReviewResponse)
async def review_api(request: ReviewRequest):
    """
    設計書とプログラムの突合レビューを実行する

    LLMを使用してレビューを実行し、マークダウン形式のレポートを返却する。
    リクエストにllmConfigが含まれる場合は指定されたプロバイダーを使用し、
    含まれない場合はシステムLLM（Bedrock）を使用する。
    """
    try:
        codes = request.get_code_blocks()
        designs = request.get_design_blocks()

        for design in designs:
            content = design.get("content", "")
            if len(content.encode("utf-8")) > MAX_DESIGN_SIZE:
                return ReviewResponse(
                    success=False,
                    error=(
                        f"設計書 '{design.get('filename', 'design')}' のサイズが上限"
                        f"（{MAX_DESIGN_SIZE // (1024 * 1024)}MB）を超えています。"
                    ),
                )

        for code in codes:
            content = code.get("contentWithLineNumbers", "")
            if len(content.encode("utf-8")) > MAX_CODE_SIZE:
                return ReviewResponse(
                    success=False,
                    error=(
                        f"プログラム '{code.get('filename', 'code')}' のサイズが上限"
                        f"（{MAX_CODE_SIZE // (1024 * 1024)}MB）を超えています。"
                    ),
                )

        # LLMプロバイダーを取得
        provider = get_llm_provider(request.llmConfig)

        # レビュー実行
        return provider.execute_review(
            request=request,
            version=f"v{APP_VERSION}",
        )

    except ValueError as e:
        return ReviewResponse(
            success=False,
            error=str(e),
        )
    except Exception as e:
        return ReviewResponse(
            success=False,
            error=f"AI処理中にエラーが発生しました。しばらく待ってから再試行してください。({str(e)})",
        )


@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_llm_connection(request: TestConnectionRequest):
    """
    LLM接続テスト

    設定モーダルの「接続テスト」ボタンから呼び出される。
    ユーザー指定のLLM設定で接続テストを実行する。
    provider/modelが未指定の場合はシステムLLM（Bedrock）をテストする。
    """
    # provider/modelが未指定の場合はシステムLLM（Bedrock）をテスト
    if request.provider is None:
        llm_config = None
    else:
        llm_config = LLMConfig(
            provider=request.provider,
            model=request.model or "",
            apiKey=request.apiKey,
            accessKeyId=request.accessKeyId,
            secretAccessKey=request.secretAccessKey,
            region=request.region,
        )

    try:
        provider = get_llm_provider(llm_config)
        result = provider.test_connection()

        return TestConnectionResponse(
            status="connected" if result["status"] == "connected" else "error",
            provider=provider.provider_name,
            model=provider.model_id,
            error=result.get("error"),
        )
    except ValueError as e:
        # プロバイダー設定エラー（APIキー未指定など）
        return TestConnectionResponse(
            status="error",
            provider=request.provider or "bedrock",
            model=request.model,
            error=str(e),
        )
    except Exception as e:
        # その他のエラー
        return TestConnectionResponse(
            status="error",
            provider=request.provider or "bedrock",
            model=request.model,
            error=str(e),
        )
