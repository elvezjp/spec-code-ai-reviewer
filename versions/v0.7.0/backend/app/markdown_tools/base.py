"""Markdown変換ツールの抽象インターフェース。"""

from abc import ABC, abstractmethod
from typing import Protocol


class MarkdownTool(ABC):
    """ExcelファイルをMarkdownへ変換するための共通インターフェース。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """ツールの識別名（APIパラメータで使用）。"""
        raise NotImplementedError

    @property
    @abstractmethod
    def display_name(self) -> str:
        """ツールの表示名（UI表示用）。"""
        raise NotImplementedError

    @abstractmethod
    def convert(self, file_content: bytes, filename: str) -> str:
        """バイナリのExcelファイルをMarkdown文字列に変換する。"""
        raise NotImplementedError

    def preprocess_for_organize(self, markdown: str) -> str:
        """Markdown整理前の前処理を行う。

        ツール固有の説明文やメタ情報を除去し、
        設計書内容のみを抽出するための前処理。
        デフォルトではそのまま返す。
        """
        return markdown


class SupportsMarkdownTool(Protocol):
    """型補完用のプロトコル。"""

    @property
    def name(self) -> str: ...

    @property
    def display_name(self) -> str: ...

    def convert(self, file_content: bytes, filename: str) -> str: ...
