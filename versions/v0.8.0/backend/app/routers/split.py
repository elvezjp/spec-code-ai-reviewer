"""分割API (v0.8.0)

セマンティック分割機能のAPIエンドポイント。
md2map / code2map ライブラリを使用してファイルを分割する。
"""

import os
import tempfile

from fastapi import APIRouter

from app.models.schemas import (
    SplitMarkdownRequest,
    SplitMarkdownResponse,
    SplitCodeRequest,
    SplitCodeResponse,
    DocumentPart,
    CodePart,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# ユーティリティ
# ---------------------------------------------------------------------------


def _estimate_tokens(text: str) -> int:
    """簡易トークン数推定（日本語考慮）"""
    # 日本語は1文字あたり約1.5トークン、英数字は約0.25トークン
    japanese_chars = sum(1 for c in text if ord(c) > 0x3000)
    other_chars = len(text) - japanese_chars
    return int(japanese_chars * 1.5 + other_chars * 0.25)


# ---------------------------------------------------------------------------
# 分割API
# ---------------------------------------------------------------------------


@router.post("/split/markdown", response_model=SplitMarkdownResponse)
async def split_markdown(request: SplitMarkdownRequest):
    """
    Markdownをセクション単位で分割する（md2map使用）

    - 見出し（H1-H6）を基準に分割
    - maxDepthで分割の見出しレベルを指定（デフォルト: H2まで）
    """
    try:
        from md2map.generators.index_generator import (
            generate_index as md2map_generate_index,
        )
        from md2map.generators.parts_generator import (
            generate_parts as md2map_generate_parts,
        )
        from md2map.parsers.markdown_parser import MarkdownParser
        from md2map.utils.file_utils import read_file as md2map_read_file

        with tempfile.TemporaryDirectory() as tmpdir:
            # 入力ファイルを書き込み
            input_path = os.path.join(tmpdir, request.filename or "input.md")
            with open(input_path, "w", encoding="utf-8") as f:
                f.write(request.content)

            # パース
            parser = MarkdownParser()
            sections, warnings = parser.parse(input_path, request.maxDepth)

            if not sections:
                return SplitMarkdownResponse(
                    success=True,
                    parts=[],
                    indexContent="# No sections found\n",
                )

            # 行を読み込み（md2mapはkeepends=Trueの行リストを返す）
            lines, _ = md2map_read_file(input_path)
            if lines is None:
                return SplitMarkdownResponse(
                    success=False,
                    error="ファイルの読み込みに失敗しました",
                )

            # セクションIDの割り当て（md2mapのCLIと同様）
            for i, section in enumerate(sections, start=1):
                section.id = f"MD{i}"

            # パーツ生成（section.part_fileを設定するために必要）
            out_dir = os.path.join(tmpdir, "output")
            md2map_generate_parts(sections, lines, out_dir)

            # INDEX.md生成
            index_path = os.path.join(out_dir, "INDEX.md")
            md2map_generate_index(
                sections, warnings, index_path, request.filename
            )

            # INDEX.md読み取り
            with open(index_path, "r", encoding="utf-8") as f:
                index_content = f.read()

            # DocumentPartリスト構築
            parts = []
            for section in sections:
                content = "".join(
                    lines[section.start_line - 1 : section.end_line]
                )
                parts.append(
                    DocumentPart(
                        id=section.id,
                        section=section.title,
                        level=section.level,
                        path=section.path,
                        startLine=section.start_line,
                        endLine=section.end_line,
                        content=content,
                        estimatedTokens=_estimate_tokens(content),
                    )
                )

        return SplitMarkdownResponse(
            success=True,
            parts=parts,
            indexContent=index_content,
        )

    except Exception as e:
        return SplitMarkdownResponse(
            success=False,
            error=f"Markdown分割中にエラーが発生しました: {str(e)}",
        )


@router.post("/split/code", response_model=SplitCodeResponse)
async def split_code(request: SplitCodeRequest):
    """
    コードをクラス・メソッド・関数単位で分割する（code2map使用）

    - ファイル拡張子から言語を自動判定
    - 対応言語: Python (.py), Java (.java)
    """
    # 言語判定
    ext = (
        request.filename.lower().split(".")[-1]
        if "." in request.filename
        else ""
    )
    language = {"py": "python", "java": "java"}.get(ext)

    if not language:
        return SplitCodeResponse(
            success=False,
            error=f"未対応の言語です: .{ext} (対応: .py, .java)",
        )

    try:
        from code2map.generators.index_generator import (
            generate_index as code2map_generate_index,
        )
        from code2map.generators.parts_generator import (
            generate_parts as code2map_generate_parts,
        )
        from code2map.utils.file_utils import (
            read_lines as code2map_read_lines,
            slice_lines,
        )

        if language == "python":
            from code2map.parsers.python_parser import PythonParser

            code_parser = PythonParser()
        else:
            from code2map.parsers.java_parser import JavaParser

            code_parser = JavaParser()

        with tempfile.TemporaryDirectory() as tmpdir:
            # 入力ファイルを書き込み
            input_path = os.path.join(tmpdir, request.filename)
            with open(input_path, "w", encoding="utf-8") as f:
                f.write(request.content)

            # パース
            symbols, warnings = code_parser.parse(input_path)

            if not symbols:
                return SplitCodeResponse(
                    success=True,
                    parts=[],
                    indexContent="# No symbols found\n",
                    language=language,
                )

            # 行を読み込み（code2mapはsplitlines()の行リストを返す）
            c2m_lines = code2map_read_lines(input_path)

            # シンボルIDの割り当て（code2mapのCLIと同様）
            for i, symbol in enumerate(symbols, start=1):
                symbol.id = f"CD{i}"

            # パーツ生成（symbol.part_fileを設定するために必要）
            out_dir = os.path.join(tmpdir, "output")
            code2map_generate_parts(symbols, c2m_lines, out_dir)

            # INDEX.md生成
            index_path = os.path.join(out_dir, "INDEX.md")
            code2map_generate_index(
                symbols, warnings, c2m_lines, index_path, request.filename
            )

            # INDEX.md読み取り
            with open(index_path, "r", encoding="utf-8") as f:
                index_content = f.read()

            # CodePartリスト構築
            parts = []
            for symbol in symbols:
                content = slice_lines(
                    c2m_lines, symbol.start_line, symbol.end_line
                )
                parts.append(
                    CodePart(
                        id=symbol.id,
                        symbol=symbol.name,
                        symbolType=symbol.kind,
                        parentSymbol=symbol.parent,
                        startLine=symbol.start_line,
                        endLine=symbol.end_line,
                        content=content,
                        estimatedTokens=_estimate_tokens(content),
                    )
                )

        return SplitCodeResponse(
            success=True,
            parts=parts,
            indexContent=index_content,
            language=language,
        )

    except Exception as e:
        return SplitCodeResponse(
            success=False,
            error=f"コード分割中にエラーが発生しました: {str(e)}",
        )
