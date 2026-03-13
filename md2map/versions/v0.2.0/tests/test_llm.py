"""LLM プロバイダー抽象化レイヤーのテスト"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from md2map.llm.base_provider import BaseLLMProvider
from md2map.llm.config import LLMConfig
from md2map.llm.factory import build_llm_config_from_env, get_llm_provider
from md2map.parsers.markdown_parser import MarkdownParser


FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# LLMConfig テスト
# ---------------------------------------------------------------------------


class TestLLMConfig:
    """LLMConfig のテスト"""

    def test_create_openai_config(self):
        config = LLMConfig(provider="openai", model="gpt-4o-mini", api_key="sk-test")
        assert config.provider == "openai"
        assert config.model == "gpt-4o-mini"
        assert config.api_key == "sk-test"
        assert config.max_tokens == 800

    def test_create_anthropic_config(self):
        config = LLMConfig(provider="anthropic", model="claude-haiku-4-5-20251001", api_key="sk-ant-test")
        assert config.provider == "anthropic"
        assert config.model == "claude-haiku-4-5-20251001"

    def test_create_bedrock_config(self):
        config = LLMConfig(
            provider="bedrock",
            model="anthropic.claude-haiku-4-5-20251001-v1:0",
            access_key_id="AKID",
            secret_access_key="SECRET",
            region="us-east-1",
        )
        assert config.provider == "bedrock"
        assert config.access_key_id == "AKID"
        assert config.region == "us-east-1"

    def test_custom_max_tokens(self):
        config = LLMConfig(provider="openai", model="gpt-4o", api_key="sk-test", max_tokens=1200)
        assert config.max_tokens == 1200

    def test_default_optional_fields(self):
        config = LLMConfig(provider="openai", model="gpt-4o-mini")
        assert config.api_key is None
        assert config.access_key_id is None
        assert config.secret_access_key is None
        assert config.region is None


# ---------------------------------------------------------------------------
# ファクトリ関数テスト
# ---------------------------------------------------------------------------


class TestGetLLMProvider:
    """get_llm_provider のテスト"""

    def test_unknown_provider_raises(self):
        config = LLMConfig(provider="unknown", model="test")
        with pytest.raises(ValueError, match="Unknown provider"):
            get_llm_provider(config)

    @patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False)
    def test_openai_provider_without_package(self):
        """openai パッケージがインポートできない場合"""
        config = LLMConfig(provider="openai", model="gpt-4o-mini", api_key="sk-test")
        with patch.dict("sys.modules", {"openai": None}):
            with pytest.raises(RuntimeError, match="openai"):
                get_llm_provider(config)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=False)
    def test_anthropic_provider_without_package(self):
        """anthropic パッケージがインポートできない場合"""
        config = LLMConfig(provider="anthropic", model="claude-haiku-4-5-20251001", api_key="sk-test")
        with patch.dict("sys.modules", {"anthropic": None}):
            with pytest.raises(RuntimeError, match="anthropic"):
                get_llm_provider(config)

    def test_bedrock_provider_without_package(self):
        """boto3 パッケージがインポートできない場合"""
        config = LLMConfig(
            provider="bedrock",
            model="anthropic.claude-haiku-4-5-20251001-v1:0",
            region="us-east-1",
        )
        with patch.dict("sys.modules", {"boto3": None}):
            with pytest.raises(RuntimeError, match="boto3"):
                get_llm_provider(config)


class TestBuildLLMConfigFromEnv:
    """build_llm_config_from_env のテスト"""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-key"}, clear=False)
    def test_openai_from_env(self):
        config = build_llm_config_from_env(provider="openai")
        assert config.provider == "openai"
        assert config.api_key == "sk-env-key"
        assert config.model == "gpt-4o-mini"  # デフォルト

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-key", "MD2MAP_AI_MODEL": "gpt-4o"}, clear=False)
    def test_openai_model_from_env(self):
        config = build_llm_config_from_env(provider="openai")
        assert config.model == "gpt-4o"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-key"}, clear=False)
    def test_openai_model_explicit(self):
        config = build_llm_config_from_env(provider="openai", model="gpt-4o-mini")
        assert config.model == "gpt-4o-mini"

    @patch.dict(os.environ, {}, clear=True)
    def test_openai_missing_key_raises(self):
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            build_llm_config_from_env(provider="openai")

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-key"}, clear=False)
    def test_anthropic_from_env(self):
        config = build_llm_config_from_env(provider="anthropic")
        assert config.provider == "anthropic"
        assert config.api_key == "sk-ant-key"

    @patch.dict(os.environ, {}, clear=True)
    def test_anthropic_missing_key_raises(self):
        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            build_llm_config_from_env(provider="anthropic")

    @patch.dict(os.environ, {}, clear=True)
    def test_bedrock_from_env_defaults(self):
        config = build_llm_config_from_env(provider="bedrock")
        assert config.provider == "bedrock"
        assert config.region == "ap-northeast-1"
        # IAM ロール認証の場合は access_key は None
        assert config.access_key_id is None

    @patch.dict(
        os.environ,
        {"AWS_ACCESS_KEY_ID": "AKID", "AWS_SECRET_ACCESS_KEY": "SECRET", "AWS_REGION": "us-west-2"},
        clear=False,
    )
    def test_bedrock_from_env_with_keys(self):
        config = build_llm_config_from_env(provider="bedrock")
        assert config.access_key_id == "AKID"
        assert config.secret_access_key == "SECRET"
        assert config.region == "us-west-2"

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            build_llm_config_from_env(provider="unknown")


# ---------------------------------------------------------------------------
# MarkdownParser への注入テスト
# ---------------------------------------------------------------------------


class MockLLMProvider(BaseLLMProvider):
    """テスト用の LLM プロバイダー"""

    def __init__(self, response_text: str = "[]"):
        self.response_text = response_text
        self.calls: list[tuple[str, str]] = []

    def send_message(self, system_prompt: str, user_message: str) -> str:
        self.calls.append((system_prompt, user_message))
        return self.response_text


class TestMarkdownParserLLMInjection:
    """MarkdownParser への LLM プロバイダー注入テスト"""

    def test_heading_mode_no_llm_needed(self):
        """heading モードでは LLM 不要"""
        parser = MarkdownParser(split_mode="heading")
        assert parser._llm_provider is None

    def test_ai_mode_with_llm_provider(self):
        """llm_provider を直接注入"""
        provider = MockLLMProvider()
        parser = MarkdownParser(split_mode="ai", llm_provider=provider)
        assert parser._llm_provider is provider

    def test_ai_mode_with_llm_config(self):
        """llm_config を注入してプロバイダーが生成される"""
        config = LLMConfig(provider="openai", model="gpt-4o-mini", api_key="sk-test")
        mock_provider = MockLLMProvider()
        with patch("md2map.llm.factory.get_llm_provider", return_value=mock_provider):
            parser = MarkdownParser(split_mode="ai", llm_config=config)
            assert parser._llm_provider is mock_provider

    def test_ai_mode_env_fallback(self):
        """llm_config / llm_provider なしの場合、bedrock にフォールバック"""
        mock_provider = MockLLMProvider()
        with patch("md2map.llm.factory.get_llm_provider", return_value=mock_provider):
            parser = MarkdownParser(split_mode="ai")
            assert parser._llm_provider is mock_provider

    def test_ai_mode_provider_priority_over_config(self):
        """llm_provider は llm_config より優先される"""
        provider = MockLLMProvider()
        config = LLMConfig(provider="openai", model="gpt-4o-mini", api_key="sk-test")
        parser = MarkdownParser(split_mode="ai", llm_config=config, llm_provider=provider)
        assert parser._llm_provider is provider

    def test_ai_mode_provider_called_on_parse(self):
        """AI モードで実際にプロバイダーが呼ばれ、行番号ベースで分割されることを確認"""
        # テスト用マークダウン: 10 行（L1=見出し, L2=空行, L3-L10=本文）
        # own_content 範囲は L2〜L10（9行）
        # AI には 1-based 相対番号（1〜9）で送信される
        ai_response = json.dumps([
            {"title": "前半", "start_line": 1, "end_line": 5},
            {"title": "後半", "start_line": 6, "end_line": 9},
        ])
        provider = MockLLMProvider(response_text=ai_response)

        content = "# Title\n\n"
        for i in range(4):
            content += "Paragraph " + str(i + 1) + " content. " * 50 + "\n\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = MarkdownParser(
                split_mode="ai",
                split_threshold=50,
                llm_provider=provider,
            )
            sections, warnings = parser.parse(temp_path)
            # プロバイダーが呼ばれたことを確認
            assert len(provider.calls) > 0
            # プロンプトに start_line が含まれていることを確認
            system_prompt = provider.calls[0][0]
            assert "start_line" in system_prompt
            assert "start_paragraph" not in system_prompt
            # 仮想セクションが生成されていることを確認
            virtual_sections = [s for s in sections if s.is_subsplit]
            assert len(virtual_sections) == 2
            assert virtual_sections[0].subsplit_title == "Title: 前半"
            assert virtual_sections[1].subsplit_title == "Title: 後半"
        finally:
            os.unlink(temp_path)

    def test_ai_mode_no_env_no_config_uses_bedrock(self):
        """環境変数も llm_config もない場合、bedrock がデフォルトで使われる"""
        mock_provider = MockLLMProvider()
        with patch.dict(os.environ, {}, clear=True):
            with patch("md2map.llm.factory.get_llm_provider", return_value=mock_provider):
                parser = MarkdownParser(split_mode="ai")
                assert parser._llm_provider is mock_provider


# ---------------------------------------------------------------------------
# 後方互換性テスト
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    """後方互換性のテスト"""

    def test_default_parser(self):
        """引数なし MarkdownParser() が従来通り動作する"""
        parser = MarkdownParser()
        assert parser.split_mode == "heading"
        assert parser._llm_provider is None
        assert parser._nlp_tokenizer is None

    def test_default_parser_parses(self):
        """引数なし MarkdownParser() でパースが動作する"""
        parser = MarkdownParser()
        sections, warnings = parser.parse(str(FIXTURES_DIR / "simple.md"))
        assert len(sections) > 0

    def test_heading_mode_explicit(self):
        """heading モードの明示的指定"""
        parser = MarkdownParser(split_mode="heading")
        sections, warnings = parser.parse(str(FIXTURES_DIR / "simple.md"))
        assert len(sections) > 0
        virtual = [s for s in sections if s.is_subsplit]
        assert len(virtual) == 0


# ---------------------------------------------------------------------------
# 親セクション自身コンテンツ範囲テスト
# ---------------------------------------------------------------------------


class TestOwnContentRange:
    """親セクションの自身コンテンツ範囲の算出と再分割テスト"""

    def test_parent_section_with_large_own_content(self):
        """子セクションを持つ親セクションの自身コンテンツが分割される"""
        # L1: # Parent
        # L2: (空行)
        # L3-L10: 巨大テーブル（own content）
        # L11: ## Child
        # L12: child content
        # own_content 範囲は L2〜L10（9行）
        # AI には 1-based 相対番号（1〜9）で送信される
        ai_response = json.dumps([
            {"title": "テーブル前半", "start_line": 1, "end_line": 5},
            {"title": "テーブル後半", "start_line": 6, "end_line": 9},
        ])
        provider = MockLLMProvider(response_text=ai_response)

        content = "# Parent\n\n"
        content += "| Col A | Col B |\n"
        content += "|-------|-------|\n"
        for i in range(6):
            content += f"| row{i} | data{i} |\n"
        content += "\n## Child\n\nChild content.\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = MarkdownParser(
                split_mode="ai",
                split_threshold=10,
                llm_provider=provider,
            )
            sections, _ = parser.parse(temp_path)

            # プロバイダーが呼ばれたことを確認
            assert len(provider.calls) > 0

            # 子セクション（## Child）が保持されていることを確認
            child_sections = [s for s in sections if s.title == "Child"]
            assert len(child_sections) == 1

            # 親セクション（# Parent）が保持されていることを確認
            parent_sections = [s for s in sections if s.title == "Parent" and not s.is_subsplit]
            assert len(parent_sections) == 1

        finally:
            os.unlink(temp_path)

    def test_ai_mode_fallback_on_invalid_response(self):
        """AI の無効なレスポンスで行数ベースのフォールバック分割が行われる"""
        provider = MockLLMProvider(response_text="invalid json")

        content = "# Title\n\n"
        for i in range(4):
            content += "Line " + str(i + 1) + " content. " * 50 + "\n\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = MarkdownParser(
                split_mode="ai",
                split_threshold=50,
                llm_provider=provider,
            )
            sections, _ = parser.parse(temp_path)

            # フォールバックで仮想セクションが生成されること
            virtual_sections = [s for s in sections if s.is_subsplit]
            assert len(virtual_sections) >= 2

            # フォールバック時は threshold split
            for vs in virtual_sections:
                assert "ai threshold split" in vs.note
        finally:
            os.unlink(temp_path)

    def test_ai_mode_line_numbers_in_prompt(self):
        """プロンプトに正しい行番号が含まれることを確認"""
        provider = MockLLMProvider(response_text="[]")

        content = "# Title\n\n"
        content += "Big content. " * 100 + "\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = MarkdownParser(
                split_mode="ai",
                split_threshold=50,
                llm_provider=provider,
            )
            parser.parse(temp_path)

            assert len(provider.calls) > 0
            user_message = provider.calls[0][1]
            # 行番号が 1 始まりの add-line-numbers 形式で含まれていることを確認
            assert "   1:" in user_message or "1:" in user_message
        finally:
            os.unlink(temp_path)
