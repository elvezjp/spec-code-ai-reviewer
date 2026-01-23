"""Markdown変換ツールレジストリのテスト。"""

import pytest

from app.markdown_tools import get_markdown_tool, get_available_tools
from app.markdown_tools.markitdown_tool import MarkItDownTool


class TestGetMarkdownTool:
    """get_markdown_tool() 関数のテスト。"""

    def test_default_returns_markitdown(self):
        """引数なしの場合、MarkItDownToolを返す。"""
        tool = get_markdown_tool()

        assert isinstance(tool, MarkItDownTool)
        assert tool.name == "markitdown"

    def test_explicit_markitdown(self):
        """明示的にmarkitdownを指定した場合、MarkItDownToolを返す。"""
        tool = get_markdown_tool("markitdown")

        assert isinstance(tool, MarkItDownTool)

    def test_case_insensitive(self):
        """ツール名は大文字小文字を区別しない。"""
        tool_lower = get_markdown_tool("markitdown")
        tool_upper = get_markdown_tool("MARKITDOWN")
        tool_mixed = get_markdown_tool("MarkItDown")

        assert isinstance(tool_lower, MarkItDownTool)
        assert isinstance(tool_upper, MarkItDownTool)
        assert isinstance(tool_mixed, MarkItDownTool)

    def test_unknown_tool_falls_back(self, caplog):
        """未知のツール名はデフォルトにフォールバックする。"""
        caplog.set_level("WARNING", logger="app.markdown_tools.registry")

        tool = get_markdown_tool("unknown-tool")

        assert isinstance(tool, MarkItDownTool)
        assert any("未知のツール名" in message for message in caplog.messages)

    def test_empty_string_returns_default(self):
        """空文字列はデフォルトを返す。"""
        tool = get_markdown_tool("")

        assert isinstance(tool, MarkItDownTool)

    def test_whitespace_only_returns_default(self):
        """空白のみの文字列はデフォルトを返す。"""
        tool = get_markdown_tool("   ")

        assert isinstance(tool, MarkItDownTool)

    def test_none_returns_default(self):
        """Noneはデフォルトを返す。"""
        tool = get_markdown_tool(None)

        assert isinstance(tool, MarkItDownTool)


class TestGetAvailableTools:
    """get_available_tools() 関数のテスト。"""

    def test_returns_list(self):
        """リスト形式で返す。"""
        tools = get_available_tools()

        assert isinstance(tools, list)
        assert len(tools) >= 1

    def test_contains_markitdown(self):
        """markitdownが含まれている。"""
        tools = get_available_tools()
        tool_names = [t["name"] for t in tools]

        assert "markitdown" in tool_names

    def test_has_required_fields(self):
        """各ツール情報に必須フィールドがある。"""
        tools = get_available_tools()

        for tool in tools:
            assert "name" in tool
            assert "display_name" in tool
            assert isinstance(tool["name"], str)
            assert isinstance(tool["display_name"], str)


class TestMarkItDownToolProperties:
    """MarkItDownToolのプロパティテスト。"""

    def test_name_property(self):
        """nameプロパティが正しい値を返す。"""
        tool = MarkItDownTool()

        assert tool.name == "markitdown"

    def test_display_name_property(self):
        """display_nameプロパティが正しい値を返す。"""
        tool = MarkItDownTool()

        assert tool.display_name == "MarkItDown"
