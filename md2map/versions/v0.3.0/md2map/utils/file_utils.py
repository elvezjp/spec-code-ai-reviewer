"""ファイル操作ユーティリティ"""

import os
from pathlib import Path
from typing import List, Optional, Tuple

from md2map.utils.logger import get_logger


def read_file(file_path: str) -> Tuple[Optional[List[str]], List[str]]:
    """ファイルを読み込む

    UTF-8エンコーディングで読み込み、デコードエラーは置換文字で処理する。

    Args:
        file_path: 読み込むファイルのパス

    Returns:
        Tuple[Optional[List[str]], List[str]]: (行リスト, 警告リスト)
        読み込み失敗時は (None, [エラーメッセージ])
    """
    logger = get_logger()
    warnings: List[str] = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # 置換文字が含まれている場合は警告
        if "\ufffd" in content:
            warnings.append(f"File contains invalid UTF-8 characters: {file_path}")
            logger.warning(warnings[-1])

        lines = content.splitlines(keepends=True)
        return lines, warnings

    except FileNotFoundError:
        error_msg = f"File not found: {file_path}"
        logger.error(error_msg)
        return None, [error_msg]

    except IOError as e:
        error_msg = f"Failed to read file: {file_path} ({e})"
        logger.error(error_msg)
        return None, [error_msg]


def write_file(file_path: str, content: str) -> bool:
    """ファイルを書き込む

    Args:
        file_path: 書き込むファイルのパス
        content: 書き込む内容

    Returns:
        成功時True、失敗時False
    """
    logger = get_logger()

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True

    except IOError as e:
        logger.error(f"Failed to write file: {file_path} ({e})")
        return False


def ensure_dir(dir_path: str) -> bool:
    """ディレクトリが存在することを保証する

    存在しない場合は作成する。

    Args:
        dir_path: ディレクトリパス

    Returns:
        成功時True、失敗時False
    """
    logger = get_logger()

    try:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        return True

    except OSError as e:
        logger.error(f"Failed to create directory: {dir_path} ({e})")
        return False
