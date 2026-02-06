"""ログ設定モジュール"""

import logging
import sys
from typing import Optional

_logger: Optional[logging.Logger] = None


def setup_logger(verbose: bool = False) -> logging.Logger:
    """ロガーを設定して返す

    Args:
        verbose: Trueの場合、DEBUGレベルのログを出力

    Returns:
        設定済みのロガー
    """
    global _logger

    _logger = logging.getLogger("md2map")
    _logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # 既存のハンドラをクリア
    _logger.handlers.clear()

    # コンソールハンドラ
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG if verbose else logging.INFO)

    # フォーマット設定
    if verbose:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S"
        )
    else:
        formatter = logging.Formatter("[%(levelname)s] %(message)s")

    handler.setFormatter(formatter)
    _logger.addHandler(handler)

    return _logger


def get_logger() -> logging.Logger:
    """現在のロガーを取得する

    Returns:
        ロガー（未設定の場合はデフォルト設定で作成）
    """
    global _logger

    if _logger is None:
        _logger = setup_logger()

    return _logger
