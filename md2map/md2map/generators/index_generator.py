"""INDEX.md 生成モジュール"""

from typing import List

from md2map.models.section import Section
from md2map.utils.file_utils import write_file
from md2map.utils.logger import get_logger


def generate_index(
    sections: List[Section],
    warnings: List[str],
    output_path: str,
    input_file: str,
) -> bool:
    """INDEX.md を生成する

    Args:
        sections: セクションのリスト
        warnings: 警告メッセージのリスト
        output_path: 出力ファイルパス
        input_file: 入力ファイル名

    Returns:
        成功時True、失敗時False
    """
    logger = get_logger()
    lines: List[str] = []

    # ヘッダ
    lines.append(f"# Index: {input_file}\n\n")

    # 警告セクション
    if warnings:
        lines.append("## Warnings\n\n")
        for warning in warnings:
            lines.append(f"- [WARNING] {warning}\n")
        lines.append("\n")

    # 構造ツリー
    lines.append("## 構造ツリー\n\n")
    for section in sections:
        indent = "  " * (section.level - 1)
        id_label = f"[{section.id}] " if section.id else ""
        if section.part_file:
            link = f"[{section.part_file}]({section.part_file})"
        else:
            link = ""
        lines.append(f"{indent}- {id_label}{section.title} ({section.line_range()}) → {link}\n")
    lines.append("\n")

    # セクション詳細
    lines.append("## セクション詳細\n\n")
    for section in sections:
        id_label = f"[{section.id}] " if section.id else ""
        lines.append(f"### {id_label}{section.title} (H{section.level})\n")
        lines.append(f"- lines: {section.line_range()}\n")

        if section.summary:
            lines.append(f"- summary: {section.summary}\n")

        if section.keywords:
            lines.append(f"- keywords: {', '.join(section.keywords)}\n")

        if section.links:
            links_str = ", ".join([f"[{text}]({url})" for text, url in section.links])
            lines.append(f"- references: {links_str}\n")

        lines.append("\n")

    # ファイル書き込み
    content = "".join(lines)
    if write_file(output_path, content):
        logger.debug(f"Generated: {output_path}")
        return True
    else:
        logger.error(f"Failed to write: {output_path}")
        return False
