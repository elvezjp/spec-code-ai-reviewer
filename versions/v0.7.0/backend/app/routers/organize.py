"""Markdown整理API"""

import asyncio
import os

from fastapi import APIRouter

from app.models.schemas import (
    OrganizeMarkdownRequest,
    OrganizeMarkdownResponse,
)
from app.services.llm_service import get_llm_provider
from app.services.markdown_organizer import (
    assign_reference_ids,
    detect_warnings,
    estimate_tokens,
    split_markdown_by_section,
)

router = APIRouter()

_MAX_INPUT_TOKENS = int(os.environ.get("ORGANIZE_MAX_INPUT_TOKENS", "20000"))
_TIMEOUT_SECONDS = int(os.environ.get("ORGANIZE_TIMEOUT_SECONDS", "60"))
_MAX_RETRIES = int(os.environ.get("ORGANIZE_MAX_RETRIES", "3"))


@router.post("/organize-markdown", response_model=OrganizeMarkdownResponse)
async def organize_markdown_api(request: OrganizeMarkdownRequest):
    """Markdown整理API"""

    if not request.markdown.strip():
        return OrganizeMarkdownResponse(
            success=False,
            error="Markdownが空です。",
            errorCode="input_empty",
        )

    if not request.policy.strip():
        return OrganizeMarkdownResponse(
            success=False,
            error="整理方針が空です。",
            errorCode="policy_empty",
        )

    provider = get_llm_provider(request.llmConfig)

    async def run_with_retry(markdown: str) -> tuple[bool, str | None, str | None, str | None]:
        last_error: str | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(provider.organize_markdown, markdown, request.policy),
                    timeout=_TIMEOUT_SECONDS,
                )
                return True, result, None, None
            except asyncio.TimeoutError:
                last_error = "タイムアウトしました。再試行してください。"
                if attempt == _MAX_RETRIES - 1:
                    return False, None, "timeout", last_error
            except Exception as e:
                last_error = str(e)
                if attempt == _MAX_RETRIES - 1:
                    return False, None, "api_error", last_error
        return False, None, "api_error", last_error

    estimated_tokens = estimate_tokens(request.markdown + "\n" + request.policy)
    if estimated_tokens > _MAX_INPUT_TOKENS:
        sections = split_markdown_by_section(request.markdown)
        if len(sections) <= 1:
            return OrganizeMarkdownResponse(
                success=False,
                error="入力が長すぎます。章単位で分割してください。",
                errorCode="token_limit",
            )

        organized_sections: list[str] = []
        for section in sections:
            section_tokens = estimate_tokens(section + "\n" + request.policy)
            if section_tokens > _MAX_INPUT_TOKENS:
                return OrganizeMarkdownResponse(
                    success=False,
                    error="入力が長すぎます。章単位で分割してください。",
                    errorCode="token_limit",
                )

            ok, organized, error_code, error_message = await run_with_retry(section)
            if not ok or organized is None:
                return OrganizeMarkdownResponse(
                    success=False,
                    error=error_message or "Markdown整理に失敗しました。",
                    errorCode=error_code or "api_error",
                )
            organized_sections.append(organized.strip())

        organized = "\n\n".join([section for section in organized_sections if section])
    else:
        ok, organized, error_code, error_message = await run_with_retry(request.markdown)
        if not ok or organized is None:
            return OrganizeMarkdownResponse(
                success=False,
                error=error_message or "Markdown整理に失敗しました。",
                errorCode=error_code or "api_error",
            )

    if not organized.strip():
        return OrganizeMarkdownResponse(
            success=False,
            error="出力形式が不正です。再試行してください。",
            errorCode="format_invalid",
        )

    organized_with_refs = assign_reference_ids(organized)
    warnings = detect_warnings(request.markdown, organized_with_refs)

    return OrganizeMarkdownResponse(
        success=True,
        organizedMarkdown=organized_with_refs,
        warnings=warnings,
    )
