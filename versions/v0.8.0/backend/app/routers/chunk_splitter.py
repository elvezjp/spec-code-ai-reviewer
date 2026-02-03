"""チャンク分割API"""

from fastapi import APIRouter

from app.models.schemas import (
    SplitChunksRequest,
    SplitChunksResponse,
)
from app.services.chunk_splitter import split_chunks

router = APIRouter()


@router.post("/split-chunks", response_model=SplitChunksResponse)
async def split_chunks_api(request: SplitChunksRequest):
    """チャンク分割API

    設計書・コードのMarkdownをチャンク単位で分割する。
    """
    if not request.markdown.strip():
        return SplitChunksResponse(
            success=False,
            error="Markdownが空です。",
        )

    try:
        chunks, total_token_count = split_chunks(
            type=request.type,
            markdown=request.markdown,
            source_filenames=request.sourceFilenames,
        )

        return SplitChunksResponse(
            success=True,
            chunks=chunks,
            totalTokenCount=total_token_count,
        )
    except Exception as e:
        return SplitChunksResponse(
            success=False,
            error=f"チャンク分割に失敗しました: {str(e)}",
        )
