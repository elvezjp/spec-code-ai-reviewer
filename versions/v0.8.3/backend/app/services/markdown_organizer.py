"""Markdown整理用の共通ロジック"""

from __future__ import annotations

import math
import re


_HEADING_RE = re.compile(r"^(#{1,3})\s+(.*)$")
_LIST_RE = re.compile(r"^(\s*)([-*+]|\d+\.)\s+(.*)$")


def estimate_tokens(text: str) -> int:
    """文字数から概算トークン数を推定する（簡易推定）"""

    return max(1, math.ceil(len(text) / 4))


def build_markdown_organize_system_prompt(policy: str) -> str:
    """Markdown整理用のシステムプロンプトを組み立てる"""

    return (
        "あなたは設計書Markdownの構造化を行うアシスタントです。\n"
        "要約や推測は禁止し、原文の意味を変えずに構造化してください。\n"
        "出力はMarkdown本文のみで、説明文は不要です。\n\n"
        "## 整理方針\n"
        f"{policy}"
    )


def build_markdown_organize_user_message(markdown: str) -> str:
    """Markdown整理用のユーザーメッセージを組み立てる"""

    return f"""以下のMarkdownを整理してください。\n\n# 原文Markdown\n{markdown}"""


def split_markdown_by_section(markdown: str) -> list[str]:
    """章単位でMarkdownを分割する（見出しなしはそのまままとめる）"""

    lines = markdown.split("\n")
    sections: list[list[str]] = []
    current: list[str] = []

    def flush():
        nonlocal current
        if current:
            sections.append(current)
            current = []

    for line in lines:
        if _HEADING_RE.match(line):
            flush()
            current.append(line)
        else:
            current.append(line)

    flush()
    return ["\n".join(chunk).strip() for chunk in sections if "\n".join(chunk).strip()]


def assign_reference_ids(markdown: str) -> str:
    """参照IDを付与する（段落/表行単位）"""

    lines = markdown.split("\n")
    output: list[str] = []
    in_code_block = False
    in_paragraph = False

    section_index = 0
    subsection_index = 0
    paragraph_index = 0
    list_branch_index = 0
    table_index = 0

    current_section = "S0"
    last_paragraph_ref: str | None = None

    def next_paragraph_ref() -> str:
        nonlocal paragraph_index
        paragraph_index += 1
        return f"{current_section}-P{paragraph_index}"

    def next_list_branch() -> str:
        nonlocal list_branch_index
        list_branch_index += 1
        return chr(ord("A") + list_branch_index - 1)

    def is_table_row(line: str) -> bool:
        return line.strip().startswith("|") and "|" in line.strip()[1:]

    def is_table_separator(line: str) -> bool:
        stripped = line.strip()
        if not stripped.startswith("|"):
            return False
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        return all(re.match(r"^:?-{3,}:?$", c) for c in cells)

    def normalize_table_row(cells: list[str], expected_cols: int) -> str:
        if len(cells) < expected_cols:
            cells = cells + [""] * (expected_cols - len(cells))
        return "| " + " | ".join(cells) + " |"

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            output.append(line)
            i += 1
            continue

        if in_code_block:
            output.append(line)
            i += 1
            continue

        heading_match = _HEADING_RE.match(line)
        if heading_match:
            hashes = heading_match.group(1)
            level = len(hashes)
            if level <= 2:
                section_index += 1
                subsection_index = 0
                current_section = f"S{section_index}"
            else:
                subsection_index += 1
                current_section = f"S{section_index}-{subsection_index}"
            paragraph_index = 0
            list_branch_index = 0
            last_paragraph_ref = None
            in_paragraph = False
            output.append(line)
            i += 1
            continue

        if is_table_row(line) and i + 1 < len(lines) and is_table_separator(lines[i + 1]):
            table_index += 1
            table_row_index = 0
            header_cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if "参照ID" not in header_cells:
                header_cells.append("参照ID")

            separator_cells = [c.strip() for c in lines[i + 1].strip().strip("|").split("|")]
            i += 2

            table_rows: list[list[str]] = []
            max_cols = max(len(header_cells), len(separator_cells))

            while i < len(lines) and is_table_row(lines[i]) and not is_table_separator(lines[i]):
                table_row_index += 1
                row_cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                has_ref = any("[ref:" in c for c in row_cells)
                if not has_ref:
                    row_cells.append(f"[ref:T{table_index}-R{table_row_index}]")
                table_rows.append(row_cells)
                max_cols = max(max_cols, len(row_cells))
                i += 1

            if len(header_cells) < max_cols:
                header_cells += [""] * (max_cols - len(header_cells))
            if len(separator_cells) < max_cols:
                separator_cells += ["---"] * (max_cols - len(separator_cells))

            output.append(normalize_table_row(header_cells, max_cols))
            output.append(normalize_table_row(separator_cells, max_cols))
            for row_cells in table_rows:
                output.append(normalize_table_row(row_cells, max_cols))
            continue

        list_match = _LIST_RE.match(line)
        if list_match:
            indent, marker, content = list_match.groups()
            if last_paragraph_ref is None:
                last_paragraph_ref = next_paragraph_ref()
                list_branch_index = 0
            branch = next_list_branch()
            ref = f"{last_paragraph_ref}-{branch}"
            if "[ref:" not in content:
                content = f"[ref:{ref}] {content}"
            output.append(f"{indent}{marker} {content}")
            in_paragraph = False
            i += 1
            continue

        if stripped == "":
            list_branch_index = 0
            in_paragraph = False
            output.append(line)
            i += 1
            continue

        if not in_paragraph:
            paragraph_ref = next_paragraph_ref()
            last_paragraph_ref = paragraph_ref
            list_branch_index = 0
            if "[ref:" not in line:
                output.append(f"[ref:{paragraph_ref}] {line}")
            else:
                output.append(line)
            in_paragraph = True
        else:
            output.append(line)
        i += 1

    return "\n".join(output)


def detect_warnings(original: str, organized: str) -> list[dict]:
    """整理結果の警告を検出する"""

    warnings: list[dict] = []
    original_length = len(original)
    organized_length = len(organized)

    if organized_length < max(10, int(original_length * 0.5)):
        warnings.append(
            {
                "code": "content_modified",
                "message": "AIが原文を大きく改変した可能性があります。内容を確認してください。",
            }
        )

    missing_refs = 0
    total_targets = 0
    lines = organized.split("\n")
    in_code_block = False
    i = 0

    def is_table_row(line: str) -> bool:
        return line.strip().startswith("|") and "|" in line.strip()[1:]

    def is_table_separator(line: str) -> bool:
        stripped = line.strip()
        if not stripped.startswith("|"):
            return False
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        return all(re.match(r"^:?-{3,}:?$", c) for c in cells)

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            i += 1
            continue

        if in_code_block:
            i += 1
            continue

        if stripped == "":
            i += 1
            continue

        if _HEADING_RE.match(line):
            i += 1
            continue

        if is_table_row(line) and i + 1 < len(lines) and is_table_separator(lines[i + 1]):
            i += 2
            while i < len(lines) and is_table_row(lines[i]) and not is_table_separator(lines[i]):
                total_targets += 1
                if "[ref:" not in lines[i]:
                    missing_refs += 1
                i += 1
            continue

        list_match = _LIST_RE.match(line)
        if list_match:
            total_targets += 1
            if "[ref:" not in line:
                missing_refs += 1
            i += 1
            continue

        paragraph_lines: list[str] = []
        while i < len(lines):
            candidate = lines[i]
            candidate_stripped = candidate.strip()
            if (
                candidate_stripped == ""
                or _HEADING_RE.match(candidate)
                or _LIST_RE.match(candidate)
                or (is_table_row(candidate) and i + 1 < len(lines) and is_table_separator(lines[i + 1]))
                or candidate_stripped.startswith("```")
            ):
                break
            paragraph_lines.append(candidate)
            i += 1

        if paragraph_lines:
            total_targets += 1
            if not any("[ref:" in l for l in paragraph_lines):
                missing_refs += 1
        else:
            i += 1

    if total_targets > 0 and missing_refs > 0:
        warnings.append(
            {
                "code": "ref_missing",
                "message": "一部の項目に参照IDが付与されていない可能性があります。",
            }
        )

    return warnings
