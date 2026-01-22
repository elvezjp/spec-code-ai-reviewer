"""Markdown変換サービス。"""

from pathlib import Path
from typing import Optional

from app.markdown_tools import get_markdown_tool


SUPPORTED_EXTENSIONS = {".xlsx", ".xls"}


def convert_excel_to_markdown(
    file_content: bytes,
    filename: str,
    tool: Optional[str] = None,
) -> str:
    """ExcelファイルをMarkdown形式に変換する。

    Args:
        file_content: Excelファイルのバイナリコンテンツ
        filename: ファイル名
        tool: 使用するツール名（省略時はデフォルト）

    Returns:
        変換されたMarkdown文字列
    """
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"対応していないファイル形式です: {ext}")

    markdown_tool = get_markdown_tool(tool)
    return markdown_tool.convert(file_content, filename)
