"""チャンク分割サービス

設計書・コードのMarkdownをチャンク単位で分割する。
"""

from __future__ import annotations

import os
import re
from typing import Literal

from app.services.markdown_organizer import estimate_tokens

# 定数
MAX_CHUNK_LINES = int(os.environ.get("MAX_CHUNK_LINES", "500"))

# ファイル境界検出用の正規表現
# フロントエンドの出力形式: "# 設計書: xxx" または "# プログラム: xxx"
_FILE_BOUNDARY_RE = re.compile(r"^#\s+(設計書:|プログラム:)\s*(.+)$", re.MULTILINE)

# 見出し検出用の正規表現
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_HEADING_34_RE = re.compile(r"^(#{3,4})\s+(.*)$")  # ### or ####

# コードシンボル検出用の正規表現
_PYTHON_CLASS_RE = re.compile(r"^\s*class\s+(\w+)")
_PYTHON_FUNC_RE = re.compile(r"^\s*def\s+(\w+)")
_TS_CLASS_RE = re.compile(r"^\s*export\s+class\s+(\w+)")
_TS_FUNC_RE = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)")
_TS_ARROW_FUNC_RE = re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(")
_JAVA_CLASS_RE = re.compile(r"^\s*(?:public\s+)?(?:class|interface|enum)\s+(\w+)")
_JAVA_METHOD_RE = re.compile(
    r"^\s*(?:public|private|protected)?\s*(?:static\s+)?(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\("
)
_GO_STRUCT_RE = re.compile(r"^\s*type\s+(\w+)\s+struct")
_GO_FUNC_RE = re.compile(r"^\s*func\s+(?:\([^)]+\)\s+)?(\w+)")


def split_chunks(
    type: Literal["spec", "code"],
    markdown: str,
    source_filenames: list[str],
) -> tuple[list[dict], int]:
    """
    Markdownをチャンク単位で分割する。

    Step 1: ファイル単位で分割（## file: or ## プログラム:）
    Step 2: 大きいチャンク（500行超）をさらに分割
      - 設計書: 見出しレベル（###, ####）で分割
      - コード: クラス/関数検出で分割、検出できなければ行数で分割

    Returns:
        (chunks_list, total_token_count)
    """
    if not markdown.strip():
        return [], 0

    # Step 1: ファイル単位で分割
    file_chunks = _split_by_file_boundary(markdown)

    # Step 2: 大きいチャンクをさらに分割
    final_chunks: list[tuple[str, str]] = []
    for title, text in file_chunks:
        lines = text.split("\n")
        if len(lines) <= MAX_CHUNK_LINES:
            final_chunks.append((title, text))
        else:
            # 分割が必要
            if type == "spec":
                sub_chunks = _split_spec_by_heading(text, title)
            else:
                sub_chunks = _split_code_by_symbols(text, title)

            # それでも大きいチャンクがあれば行数で分割
            for sub_title, sub_text in sub_chunks:
                sub_lines = sub_text.split("\n")
                if len(sub_lines) <= MAX_CHUNK_LINES:
                    final_chunks.append((sub_title, sub_text))
                else:
                    # 行数で機械的に分割
                    line_chunks = _split_by_line_count(sub_text, sub_title, MAX_CHUNK_LINES)
                    final_chunks.extend(line_chunks)

    # チャンクをデータ構造に変換
    chunks: list[dict] = []
    total_tokens = 0
    for i, (title, text) in enumerate(final_chunks):
        if not text.strip():
            continue
        token_count = estimate_tokens(text)
        total_tokens += token_count
        chunks.append(
            {
                "id": f"chunk-{i + 1:04d}",
                "title": title,
                "text": text,
                "tokenCount": token_count,
            }
        )

    return chunks, total_tokens


def _split_by_file_boundary(markdown: str) -> list[tuple[str, str]]:
    """
    ファイル単位で分割する。

    ## file: <path> または ## プログラム: <path> を境界として分割。

    Returns:
        [(title, text), ...]
    """
    lines = markdown.split("\n")
    chunks: list[tuple[str, str]] = []
    current_title = "(先頭)"
    current_lines: list[str] = []

    for line in lines:
        match = _FILE_BOUNDARY_RE.match(line)
        if match:
            # 前のチャンクを保存
            if current_lines:
                chunks.append((current_title, "\n".join(current_lines)))
            # 新しいチャンクを開始
            prefix = match.group(1)
            path = match.group(2).strip()
            current_title = f"{prefix} {path}"
            current_lines = [line]
        else:
            current_lines.append(line)

    # 最後のチャンクを保存
    if current_lines:
        chunks.append((current_title, "\n".join(current_lines)))

    return chunks


def _split_spec_by_heading(text: str, base_title: str) -> list[tuple[str, str]]:
    """
    設計書のチャンクを見出しレベル（###, ####）で分割する。

    コードブロック内の見出しは無視する。

    Returns:
        [(title, text), ...]
    """
    lines = text.split("\n")
    chunks: list[tuple[str, str]] = []
    current_title = base_title
    current_lines: list[str] = []
    in_code_block = False

    for line in lines:
        # コードブロックの開始/終了を追跡
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            current_lines.append(line)
            continue

        if in_code_block:
            current_lines.append(line)
            continue

        # ### or #### の見出しを検出
        match = _HEADING_34_RE.match(line)
        if match:
            # 前のチャンクを保存
            if current_lines:
                chunks.append((current_title, "\n".join(current_lines)))
            # 新しいチャンクを開始
            heading_text = match.group(2).strip()
            current_title = f"{base_title} / {heading_text}"
            current_lines = [line]
        else:
            current_lines.append(line)

    # 最後のチャンクを保存
    if current_lines:
        chunks.append((current_title, "\n".join(current_lines)))

    # 空のチャンクを除外
    return [(t, c) for t, c in chunks if c.strip()]


def _split_code_by_symbols(text: str, base_title: str) -> list[tuple[str, str]]:
    """
    コードのチャンクをクラス/関数で分割する。

    シンボルが検出できない場合は元のチャンクをそのまま返す。

    Returns:
        [(title, text), ...]
    """
    lines = text.split("\n")
    chunks: list[tuple[str, str]] = []
    current_title = base_title
    current_lines: list[str] = []
    in_code_block = False

    for line in lines:
        # コードブロックの開始/終了を追跡
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            # シンボル検出はコードブロック内で行う
            if in_code_block:
                current_lines.append(line)
                continue

        if not in_code_block:
            current_lines.append(line)
            continue

        # コードブロック内でシンボルを検出
        symbol = _detect_code_symbol(line)
        if symbol:
            # 前のチャンクを保存（内容があれば）
            if current_lines and any(l.strip() for l in current_lines):
                chunks.append((current_title, "\n".join(current_lines)))
            # 新しいチャンクを開始
            current_title = f"{base_title} / {symbol}"
            current_lines = [line]
        else:
            current_lines.append(line)

    # 最後のチャンクを保存
    if current_lines:
        chunks.append((current_title, "\n".join(current_lines)))

    # シンボルが見つからなかった場合は元のテキストを返す
    if len(chunks) <= 1:
        return [(base_title, text)]

    # 空のチャンクを除外
    return [(t, c) for t, c in chunks if c.strip()]


def _detect_code_symbol(line: str) -> str | None:
    """
    行からクラス/関数シンボルを検出する。

    Returns:
        シンボル名（例: "class MyClass", "def my_function"）、見つからなければ None
    """
    # Python
    match = _PYTHON_CLASS_RE.match(line)
    if match:
        return f"class {match.group(1)}"
    match = _PYTHON_FUNC_RE.match(line)
    if match:
        return f"def {match.group(1)}"

    # TypeScript/JavaScript
    match = _TS_CLASS_RE.match(line)
    if match:
        return f"class {match.group(1)}"
    match = _TS_FUNC_RE.match(line)
    if match:
        return f"function {match.group(1)}"
    match = _TS_ARROW_FUNC_RE.match(line)
    if match:
        return f"const {match.group(1)}"

    # Java
    match = _JAVA_CLASS_RE.match(line)
    if match:
        return f"class {match.group(1)}"
    match = _JAVA_METHOD_RE.match(line)
    if match:
        return f"method {match.group(1)}"

    # Go
    match = _GO_STRUCT_RE.match(line)
    if match:
        return f"type {match.group(1)}"
    match = _GO_FUNC_RE.match(line)
    if match:
        return f"func {match.group(1)}"

    return None


def _split_by_line_count(
    text: str, base_title: str, max_lines: int = 500
) -> list[tuple[str, str]]:
    """
    テキストを行数で機械的に分割する（フォールバック）。

    コードブロックの途中で分割しないように注意する。

    Returns:
        [(title, text), ...]
    """
    lines = text.split("\n")
    if len(lines) <= max_lines:
        return [(base_title, text)]

    chunks: list[tuple[str, str]] = []
    current_lines: list[str] = []
    part_num = 0
    in_code_block = False

    for line in lines:
        current_lines.append(line)

        # コードブロックの追跡
        if line.strip().startswith("```"):
            in_code_block = not in_code_block

        # 分割条件: max_lines を超え、コードブロック外
        if len(current_lines) >= max_lines and not in_code_block:
            part_num += 1
            title = f"{base_title} (part {part_num})"
            chunks.append((title, "\n".join(current_lines)))
            current_lines = []

    # 残りを保存
    if current_lines:
        part_num += 1
        title = f"{base_title} (part {part_num})" if part_num > 1 else base_title
        chunks.append((title, "\n".join(current_lines)))

    return chunks
