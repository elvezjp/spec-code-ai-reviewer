"""段階的要約API"""

import asyncio
import os

from fastapi import APIRouter

from app.models.schemas import (
    ProgressiveSummaryRequest,
    ProgressiveSummaryResponse,
)
from app.services.llm_service import get_llm_provider
from app.services.progressive_summary import build_progressive_summary_prompt

router = APIRouter()

_TIMEOUT_SECONDS = int(os.environ.get("PROGRESSIVE_SUMMARY_TIMEOUT_SECONDS", "180"))
_MAX_RETRIES = int(os.environ.get("PROGRESSIVE_SUMMARY_MAX_RETRIES", "2"))


@router.post("/progressive-summary", response_model=ProgressiveSummaryResponse)
async def progressive_summary_api(request: ProgressiveSummaryRequest):
    """段階的要約API

    1つのチャンクを要約し、累積サマリーに統合して返す。
    """
    if not request.chunk.text.strip():
        return ProgressiveSummaryResponse(
            success=False,
            error="チャンクが空です。",
        )

    if not request.policy.strip():
        return ProgressiveSummaryResponse(
            success=False,
            error="要約方針が空です。",
        )

    # プロンプトを構築
    system_prompt, user_message = build_progressive_summary_prompt(
        type=request.type,
        chunk={
            "id": request.chunk.id,
            "title": request.chunk.title,
            "text": request.chunk.text,
        },
        chunk_outline=request.chunkOutline,
        current_summary=request.currentSummary,
        policy=request.policy,
    )

    provider = get_llm_provider(request.llmConfig)

    async def run_with_retry() -> tuple[bool, str | None, str | None]:
        last_error: str | None = None
        total_attempts = 0

        for attempt in range(_MAX_RETRIES):
            total_attempts = attempt + 1
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        provider.progressive_summary, system_prompt, user_message
                    ),
                    timeout=_TIMEOUT_SECONDS,
                )
                return True, result, None
            except asyncio.TimeoutError:
                last_error = f"タイムアウトしました（{total_attempts}回実行）。再試行してください。"
                if attempt == _MAX_RETRIES - 1:
                    return False, None, last_error
            except Exception as e:
                last_error = f"{str(e)}（{total_attempts}回実行）"
                if attempt == _MAX_RETRIES - 1:
                    return False, None, last_error

        return False, None, last_error

    ok, updated_summary, error_message = await run_with_retry()

    if not ok or updated_summary is None:
        return ProgressiveSummaryResponse(
            success=False,
            error=error_message or "要約に失敗しました。",
        )

    if not updated_summary.strip():
        return ProgressiveSummaryResponse(
            success=False,
            error="出力が空です。再試行してください。",
        )

    return ProgressiveSummaryResponse(
        success=True,
        chunkSummary=None,  # 個別チャンクのサマリーは出力しない（統合後のみ）
        updatedSummary=updated_summary.strip(),
    )
