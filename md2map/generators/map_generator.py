"""MAP.json 生成モジュール"""

import hashlib
import json
import os
from typing import Any, Dict, List

from md2map.models.section import Section
from md2map.utils.file_utils import write_file
from md2map.utils.logger import get_logger


def calculate_checksum(file_path: str) -> str:
    """ファイルの SHA-256 チェックサムを計算する

    Args:
        file_path: ファイルパス

    Returns:
        SHA-256 ハッシュ値（16進数64文字、小文字）
    """
    try:
        with open(file_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except IOError:
        return ""


def generate_map(
    sections: List[Section],
    out_dir: str,
    output_path: str,
) -> bool:
    """MAP.json を生成する

    Args:
        sections: セクションのリスト
        out_dir: 出力ディレクトリ（parts/ファイルの基準パス）
        output_path: 出力ファイルパス

    Returns:
        成功時True、失敗時False
    """
    logger = get_logger()
    entries: List[Dict[str, Any]] = []

    for section in sections:
        if not section.part_file:
            continue

        # パートファイルのパス
        part_path = os.path.join(out_dir, section.part_file)
        checksum = calculate_checksum(part_path)

        entry: Dict[str, Any] = {}
        if section.id:
            entry["id"] = section.id
        entry.update({
            "section": section.title,
            "level": section.level,
            "path": section.path,
            "original_file": section.original_file,
            "original_start_line": section.start_line,
            "original_end_line": section.end_line,
            "word_count": section.word_count,
            "part_file": section.part_file,
            "checksum": checksum,
        })
        entries.append(entry)

    # JSON書き込み
    content = json.dumps(entries, ensure_ascii=False, indent=2)
    if write_file(output_path, content + "\n"):
        logger.debug(f"Generated: {output_path}")
        return True
    else:
        logger.error(f"Failed to write: {output_path}")
        return False
