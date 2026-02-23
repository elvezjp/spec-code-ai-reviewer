"""parts/ ディレクトリ生成モジュール"""

import os
import re
from typing import List, Set, Tuple

from md2map.models.section import Section
from md2map.utils.file_utils import ensure_dir, write_file
from md2map.utils.logger import get_logger


def sanitize_filename(name: str) -> str:
    """ファイル名として使用可能な文字列に変換する

    Args:
        name: 元の名前

    Returns:
        サニタイズされた名前
    """
    # スペースをアンダースコアに置換
    name = name.replace(" ", "_")
    # 特殊文字を削除
    name = re.sub(r'[/\\:*?"<>|]', "", name)
    # 連続するアンダースコアを1つに
    name = re.sub(r"_+", "_", name)
    # 先頭・末尾のアンダースコアを削除
    name = name.strip("_")
    return name


def build_filename(section: Section, existing: Set[str]) -> str:
    """セクションのファイル名を生成する

    Args:
        section: セクション
        existing: 既存のファイル名セット

    Returns:
        ファイル名
    """
    # 階層パスからファイル名を構築
    hierarchy: List[str] = []
    current: Section | None = section

    while current:
        hierarchy.insert(0, sanitize_filename(current.display_name()))
        current = current.parent

    base_name = "_".join(hierarchy) + ".md"

    # 衝突回避
    if base_name in existing:
        counter = 1
        while f"{base_name[:-3]}_{counter}.md" in existing:
            counter += 1
        base_name = f"{base_name[:-3]}_{counter}.md"

    return base_name


def generate_header(section: Section) -> str:
    """パートファイルのヘッダを生成する

    Args:
        section: セクション

    Returns:
        HTMLコメント形式のヘッダ
    """
    id_line = f"id: {section.id}\n" if section.id else ""
    # サブスプリットの場合のみ追加フィールドを出力（heading モードの後方互換性を維持）
    subsplit_lines = ""
    if section.is_subsplit:
        subsplit_lines += "is_subsplit: true\n"
        if section.note:
            subsplit_lines += f"note: {section.note}\n"
        if section.subsplit_title:
            subsplit_lines += f"subsplit_title: {section.subsplit_title}\n"
    return f"""<!--
md2map fragment
{id_line}original: {section.original_file}
lines: {section.start_line}-{section.end_line}
section: {section.title}
level: {section.level}
{subsplit_lines}-->

"""


def generate_parts(
    sections: List[Section],
    lines: List[str],
    out_dir: str,
    dry_run: bool = False,
) -> List[Tuple[Section, str]]:
    """parts/ ディレクトリにセクションファイルを生成する

    Args:
        sections: セクションのリスト
        lines: 元ファイルの行リスト
        out_dir: 出力ディレクトリ
        dry_run: Trueの場合、ファイルを生成せずプレビューのみ

    Returns:
        (セクション, 生成ファイルパス) のリスト
    """
    logger = get_logger()
    parts_dir = os.path.join(out_dir, "parts")

    if not dry_run:
        if not ensure_dir(parts_dir):
            logger.error(f"Failed to create parts directory: {parts_dir}")
            return []

    results: List[Tuple[Section, str]] = []
    existing_files: Set[str] = set()

    for section in sections:
        # ファイル名決定
        filename = build_filename(section, existing_files)
        existing_files.add(filename)

        file_path = os.path.join(parts_dir, filename)
        section.part_file = f"parts/{filename}"

        if dry_run:
            results.append((section, file_path))
            continue

        # ヘッダ生成
        header = generate_header(section)

        # コンテンツ抽出
        content = "".join(lines[section.start_line - 1 : section.end_line])

        # ファイル書き込み
        if write_file(file_path, header + content):
            logger.debug(f"Generated: {file_path}")
            results.append((section, file_path))
        else:
            logger.error(f"Failed to write: {file_path}")

    return results
