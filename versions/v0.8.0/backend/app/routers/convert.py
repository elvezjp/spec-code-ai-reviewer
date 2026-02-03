"""変換API"""

from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile, HTTPException

from app.models.schemas import ConvertResponse, AvailableToolsResponse, ToolInfo
from app.services.markitdown_service import convert_excel_to_markdown
from app.services.line_numbers_service import add_line_numbers
from app.markdown_tools import get_available_tools

router = APIRouter()

# ファイルサイズ制限
MAX_EXCEL_SIZE = 10 * 1024 * 1024  # 10MB
MAX_CODE_SIZE = 5 * 1024 * 1024  # 5MB


@router.get("/available-tools", response_model=AvailableToolsResponse)
async def get_available_tools_api():
    """
    利用可能なMarkdown変換ツールの一覧を取得する
    """
    tools = get_available_tools()
    return AvailableToolsResponse(
        tools=[ToolInfo(name=t["name"], display_name=t["display_name"]) for t in tools]
    )


@router.post("/excel-to-markdown", response_model=ConvertResponse)
async def convert_excel_to_markdown_api(
    file: UploadFile = File(...),
    tool: Optional[str] = Form(None),
):
    """
    ExcelファイルをMarkdown形式に変換する

    - 対応形式: .xlsx, .xls
    - 最大サイズ: 10MB
    - tool: 使用するツール名（省略時はmarkitdown）
    """
    # ファイル形式チェック
    if not file.filename:
        raise HTTPException(status_code=400, detail="ファイル名が取得できません")

    filename = file.filename
    ext = filename.lower().split(".")[-1] if "." in filename else ""

    if ext not in ["xlsx", "xls"]:
        return ConvertResponse(
            success=False,
            filename=filename,
            error="対応していないファイル形式です。Excel (.xlsx, .xls) ファイルを選択してください。",
        )

    # ファイル読み込み
    content = await file.read()

    # サイズチェック
    if len(content) > MAX_EXCEL_SIZE:
        return ConvertResponse(
            success=False,
            filename=filename,
            error=f"ファイルサイズが上限（{MAX_EXCEL_SIZE // (1024*1024)}MB）を超えています。",
        )

    try:
        markdown = convert_excel_to_markdown(content, filename, tool)
        return ConvertResponse(
            success=True,
            markdown=markdown,
            filename=filename,
        )
    except ValueError as e:
        return ConvertResponse(
            success=False,
            filename=filename,
            error=str(e),
        )
    except Exception as e:
        return ConvertResponse(
            success=False,
            filename=filename,
            error=f"変換中にエラーが発生しました: {str(e)}",
        )


@router.post("/add-line-numbers", response_model=ConvertResponse)
async def add_line_numbers_api(file: UploadFile = File(...)):
    """
    テキストファイルに行番号を付与する

    - 対応形式: 任意のテキストファイル
    - 最大サイズ: 5MB
    - 行番号形式: 右揃え4桁 + コロン + スペース
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="ファイル名が取得できません")

    filename = file.filename

    # ファイル読み込み
    content_bytes = await file.read()

    # サイズチェック
    if len(content_bytes) > MAX_CODE_SIZE:
        return ConvertResponse(
            success=False,
            filename=filename,
            error=f"ファイルサイズが上限（{MAX_CODE_SIZE // (1024*1024)}MB）を超えています。",
        )

    # テキストとしてデコード
    try:
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            content = content_bytes.decode("shift_jis")
        except UnicodeDecodeError:
            return ConvertResponse(
                success=False,
                filename=filename,
                error="ファイルのエンコーディングを認識できませんでした。UTF-8またはShift_JISで保存してください。",
            )

    try:
        numbered_content, line_count = add_line_numbers(content)
        return ConvertResponse(
            success=True,
            content=numbered_content,
            filename=filename,
            line_count=line_count,
        )
    except Exception as e:
        return ConvertResponse(
            success=False,
            filename=filename,
            error=f"変換中にエラーが発生しました: {str(e)}",
        )
