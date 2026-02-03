"""MarkItDown を用いた Markdown 変換ツール。"""

import tempfile
from pathlib import Path

from markitdown import MarkItDown

from .base import MarkdownTool


class MarkItDownTool(MarkdownTool):
    """MarkItDownライブラリを利用したExcel→Markdown変換。"""

    @property
    def name(self) -> str:
        """ツールの識別名。"""
        return "markitdown"

    @property
    def display_name(self) -> str:
        """ツールの表示名。"""
        return "MarkItDown"

    def convert(self, file_content: bytes, filename: str) -> str:
        """`file_content` と `filename` を受け取り Markdown 文字列を返す。"""
        ext = Path(filename).suffix.lower()

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(file_content)
            tmp_path = Path(tmp.name)

        try:
            md = MarkItDown()
            result = md.convert(str(tmp_path))
            return result.text_content
        finally:
            tmp_path.unlink(missing_ok=True)
