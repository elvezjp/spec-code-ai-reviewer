"""Markdown変換ツールのレジストリ。"""

import logging
from typing import Optional

from .base import MarkdownTool

logger = logging.getLogger(__name__)

# ツールレジストリ: ツール名 -> ツールクラス
_TOOL_REGISTRY: dict[str, type[MarkdownTool]] = {}

# デフォルトツール名
DEFAULT_TOOL = "markitdown"


def register_tool(tool_class: type[MarkdownTool]) -> type[MarkdownTool]:
    """ツールをレジストリに登録するデコレータ。"""
    instance = tool_class()
    _TOOL_REGISTRY[instance.name] = tool_class
    return tool_class


def get_available_tools() -> list[dict[str, str]]:
    """利用可能なツールのリストを返す。"""
    tools = []
    for tool_class in _TOOL_REGISTRY.values():
        instance = tool_class()
        tools.append({
            "name": instance.name,
            "display_name": instance.display_name,
        })
    return tools


def get_markdown_tool(tool_name: Optional[str] = None) -> MarkdownTool:
    """指定されたツール名からツールインスタンスを取得する。"""
    name = (tool_name or "").strip().lower() or DEFAULT_TOOL

    if name not in _TOOL_REGISTRY:
        logger.warning(
            "未知のツール名 '%s' のため %s を使用します。", name, DEFAULT_TOOL
        )
        name = DEFAULT_TOOL

    return _TOOL_REGISTRY[name]()


# 組み込みツールの登録
def _register_builtin_tools() -> None:
    """組み込みツールを登録する。"""
    from .markitdown_tool import MarkItDownTool
    from .excel2md_tool import Excel2mdTool
    from .excel2md_mermaid_tool import Excel2mdMermaidTool

    register_tool(MarkItDownTool)
    register_tool(Excel2mdTool)
    register_tool(Excel2mdMermaidTool)


_register_builtin_tools()
