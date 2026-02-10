"""split.py の単体テスト

テストケース:
- UT-SPL-001: split_markdown() - 正常系（基本的なMarkdown分割）
- UT-SPL-002: split_markdown() - 正常系（maxDepth指定）
- UT-SPL-003: split_markdown() - セクションなし
- UT-SPL-004: split_markdown() - エラー（パースエラー）
- UT-SPL-005: split_code() - 正常系（Python）
- UT-SPL-006: split_code() - 正常系（Java）
- UT-SPL-007: split_code() - シンボルなし
- UT-SPL-008: split_code() - エラー（未対応言語）
- UT-SPL-009: split_code() - エラー（パースエラー）
- UT-SPL-010: _estimate_tokens() - トークン数推定
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import SplitMarkdownRequest, SplitCodeRequest

client = TestClient(app)


class TestSplitMarkdownAPI:
    """split_markdown() のテスト"""

    @patch("md2map.generators.parts_generator.generate_parts")
    @patch("md2map.generators.index_generator.generate_index")
    @patch("md2map.utils.file_utils.read_file")
    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_001_success_basic(
        self, mock_parser_cls, mock_read_file, mock_gen_index, mock_gen_parts
    ):
        """UT-SPL-001: 正常系（基本的なMarkdown分割）"""
        import os

        # モックセクション
        mock_section = MagicMock()
        mock_section.title = "概要"
        mock_section.level = 1
        mock_section.path = "概要"
        mock_section.start_line = 1
        mock_section.end_line = 5
        mock_section.id = "MD1"

        mock_parser = MagicMock()
        mock_parser.parse.return_value = ([mock_section], [])
        mock_parser_cls.return_value = mock_parser

        mock_read_file.return_value = (
            ["# 概要\n", "\n", "これは概要です。\n", "\n", "詳細説明\n"],
            None,
        )

        # generate_partsがoutputディレクトリを作成する動作をシミュレート
        def create_output_dir(sections, lines, out_dir):
            os.makedirs(out_dir, exist_ok=True)

        mock_gen_parts.side_effect = create_output_dir

        # generate_indexがINDEX.mdを書き込む動作をシミュレート
        def write_index(sections, warnings, index_path, filename):
            with open(index_path, "w") as f:
                f.write("# INDEX\n\n- MD1: 概要\n")

        mock_gen_index.side_effect = write_index

        request = SplitMarkdownRequest(
            content="# 概要\n\nこれは概要です。\n\n詳細説明",
            filename="test.md",
            maxDepth=2,
        )

        response = client.post("/api/split/markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["parts"]) == 1
        assert data["parts"][0]["section"] == "概要"
        assert data["parts"][0]["level"] == 1
        assert data["parts"][0]["id"] == "MD1"
        assert data["indexContent"] is not None
        assert "INDEX" in data["indexContent"]

    @patch("md2map.generators.parts_generator.generate_parts")
    @patch("md2map.generators.index_generator.generate_index")
    @patch("md2map.utils.file_utils.read_file")
    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_002_success_max_depth(
        self, mock_parser_cls, mock_read_file, mock_gen_index, mock_gen_parts
    ):
        """UT-SPL-002: 正常系（maxDepth指定）"""
        import os

        # H1とH2の両方を含むセクション
        mock_section1 = MagicMock()
        mock_section1.title = "第1章"
        mock_section1.level = 1
        mock_section1.path = "第1章"
        mock_section1.start_line = 1
        mock_section1.end_line = 3
        mock_section1.id = "MD1"

        mock_section2 = MagicMock()
        mock_section2.title = "1.1 概要"
        mock_section2.level = 2
        mock_section2.path = "第1章 > 1.1 概要"
        mock_section2.start_line = 4
        mock_section2.end_line = 6
        mock_section2.id = "MD2"

        mock_parser = MagicMock()
        mock_parser.parse.return_value = ([mock_section1, mock_section2], [])
        mock_parser_cls.return_value = mock_parser

        mock_read_file.return_value = (
            ["# 第1章\n", "\n", "章の説明\n", "## 1.1 概要\n", "\n", "概要の説明\n"],
            None,
        )

        # generate_partsがoutputディレクトリを作成する動作をシミュレート
        def create_output_dir(sections, lines, out_dir):
            os.makedirs(out_dir, exist_ok=True)

        mock_gen_parts.side_effect = create_output_dir

        def write_index(sections, warnings, index_path, filename):
            with open(index_path, "w") as f:
                f.write("# INDEX\n\n- MD1: 第1章\n- MD2: 1.1 概要\n")

        mock_gen_index.side_effect = write_index

        request = SplitMarkdownRequest(
            content="# 第1章\n\n章の説明\n## 1.1 概要\n\n概要の説明",
            filename="test.md",
            maxDepth=3,  # H3まで分割
        )

        response = client.post("/api/split/markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["parts"]) == 2
        # maxDepthがパーサーに渡されていることを確認
        mock_parser.parse.assert_called_once()
        call_args = mock_parser.parse.call_args
        assert call_args[0][1] == 3  # maxDepth

    @patch("md2map.utils.file_utils.read_file")
    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_003_no_sections(self, mock_parser_cls, mock_read_file):
        """UT-SPL-003: セクションなし"""
        mock_parser = MagicMock()
        mock_parser.parse.return_value = ([], [])  # セクションなし
        mock_parser_cls.return_value = mock_parser

        request = SplitMarkdownRequest(
            content="見出しのないテキスト",
            filename="test.md",
        )

        response = client.post("/api/split/markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["parts"] == []
        assert "No sections found" in data["indexContent"]

    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_004_parse_error(self, mock_parser_cls):
        """UT-SPL-004: エラー（パースエラー）"""
        mock_parser = MagicMock()
        mock_parser.parse.side_effect = Exception("Parse error")
        mock_parser_cls.return_value = mock_parser

        request = SplitMarkdownRequest(
            content="# 壊れたMarkdown",
            filename="test.md",
        )

        response = client.post("/api/split/markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "エラー" in data["error"]

    @patch("md2map.generators.parts_generator.generate_parts")
    @patch("md2map.generators.index_generator.generate_index")
    @patch("md2map.utils.file_utils.read_file")
    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_010_token_estimation(
        self, mock_parser_cls, mock_read_file, mock_gen_index, mock_gen_parts
    ):
        """UT-SPL-010: トークン数推定"""
        import os

        mock_section = MagicMock()
        mock_section.title = "日本語セクション"
        mock_section.level = 1
        mock_section.path = "日本語セクション"
        mock_section.start_line = 1
        mock_section.end_line = 2
        mock_section.id = "MD1"

        mock_parser = MagicMock()
        mock_parser.parse.return_value = ([mock_section], [])
        mock_parser_cls.return_value = mock_parser

        # 日本語と英語の混在テキスト
        japanese_content = "# 日本語セクション\nこれは日本語のテストです。This is English."
        lines = japanese_content.split("\n")
        mock_read_file.return_value = ([line + "\n" for line in lines], None)

        # generate_partsがoutputディレクトリを作成する動作をシミュレート
        def create_output_dir(sections, lines, out_dir):
            os.makedirs(out_dir, exist_ok=True)

        mock_gen_parts.side_effect = create_output_dir

        def write_index(sections, warnings, index_path, filename):
            with open(index_path, "w") as f:
                f.write("# INDEX\n")

        mock_gen_index.side_effect = write_index

        request = SplitMarkdownRequest(
            content=japanese_content,
            filename="test.md",
        )

        response = client.post("/api/split/markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["parts"]) == 1
        # トークン数が推定されていることを確認
        assert data["parts"][0]["estimatedTokens"] > 0


class TestSplitCodeAPI:
    """split_code() のテスト"""

    @patch("code2map.generators.parts_generator.generate_parts")
    @patch("code2map.generators.index_generator.generate_index")
    @patch("code2map.utils.file_utils.read_lines")
    @patch("code2map.utils.file_utils.slice_lines")
    @patch("code2map.parsers.python_parser.PythonParser")
    def test_ut_spl_005_success_python(
        self, mock_parser_cls, mock_slice, mock_read_lines, mock_gen_index, mock_gen_parts
    ):
        """UT-SPL-005: 正常系（Python）"""
        import os

        # モックシンボル
        mock_symbol = MagicMock()
        mock_symbol.name = "hello"
        mock_symbol.kind = "function"
        mock_symbol.parent = None
        mock_symbol.start_line = 1
        mock_symbol.end_line = 3
        mock_symbol.id = "CD1"

        mock_parser = MagicMock()
        mock_parser.parse.return_value = ([mock_symbol], [])
        mock_parser_cls.return_value = mock_parser

        mock_read_lines.return_value = ["def hello():", "    print('hello')", ""]
        mock_slice.return_value = "def hello():\n    print('hello')\n"

        # generate_partsがoutputディレクトリを作成する動作をシミュレート
        def create_output_dir(symbols, lines, out_dir):
            os.makedirs(out_dir, exist_ok=True)

        mock_gen_parts.side_effect = create_output_dir

        def write_index(symbols, warnings, lines, index_path, filename):
            with open(index_path, "w") as f:
                f.write("# CODE INDEX\n\n- CD1: hello (function)\n")

        mock_gen_index.side_effect = write_index

        request = SplitCodeRequest(
            content="def hello():\n    print('hello')\n",
            filename="test.py",
        )

        response = client.post("/api/split/code", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["language"] == "python"
        assert len(data["parts"]) == 1
        assert data["parts"][0]["symbol"] == "hello"
        assert data["parts"][0]["symbolType"] == "function"
        assert data["parts"][0]["id"] == "CD1"
        assert data["indexContent"] is not None

    @patch("code2map.generators.parts_generator.generate_parts")
    @patch("code2map.generators.index_generator.generate_index")
    @patch("code2map.utils.file_utils.read_lines")
    @patch("code2map.utils.file_utils.slice_lines")
    @patch("code2map.parsers.java_parser.JavaParser")
    def test_ut_spl_006_success_java(
        self, mock_parser_cls, mock_slice, mock_read_lines, mock_gen_index, mock_gen_parts
    ):
        """UT-SPL-006: 正常系（Java）"""
        import os

        # モッククラスシンボル
        mock_class = MagicMock()
        mock_class.name = "HelloWorld"
        mock_class.kind = "class"
        mock_class.parent = None
        mock_class.start_line = 1
        mock_class.end_line = 7
        mock_class.id = "CD1"

        # モックメソッドシンボル
        mock_method = MagicMock()
        mock_method.name = "main"
        mock_method.kind = "method"
        mock_method.parent = "HelloWorld"
        mock_method.start_line = 2
        mock_method.end_line = 5
        mock_method.id = "CD2"

        mock_parser = MagicMock()
        mock_parser.parse.return_value = ([mock_class, mock_method], [])
        mock_parser_cls.return_value = mock_parser

        java_code = """public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}"""
        mock_read_lines.return_value = java_code.split("\n")
        mock_slice.side_effect = [java_code, "public static void main(String[] args) {\n        System.out.println(\"Hello\");\n    }"]

        # generate_partsがoutputディレクトリを作成する動作をシミュレート
        def create_output_dir(symbols, lines, out_dir):
            os.makedirs(out_dir, exist_ok=True)

        mock_gen_parts.side_effect = create_output_dir

        def write_index(symbols, warnings, lines, index_path, filename):
            with open(index_path, "w") as f:
                f.write("# CODE INDEX\n\n- CD1: HelloWorld (class)\n  - CD2: main (method)\n")

        mock_gen_index.side_effect = write_index

        request = SplitCodeRequest(
            content=java_code,
            filename="HelloWorld.java",
        )

        response = client.post("/api/split/code", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["language"] == "java"
        assert len(data["parts"]) == 2
        assert data["parts"][0]["symbol"] == "HelloWorld"
        assert data["parts"][0]["symbolType"] == "class"
        assert data["parts"][1]["symbol"] == "main"
        assert data["parts"][1]["symbolType"] == "method"
        assert data["parts"][1]["parentSymbol"] == "HelloWorld"

    @patch("code2map.utils.file_utils.read_lines")
    @patch("code2map.parsers.python_parser.PythonParser")
    def test_ut_spl_007_no_symbols(self, mock_parser_cls, mock_read_lines):
        """UT-SPL-007: シンボルなし"""
        mock_parser = MagicMock()
        mock_parser.parse.return_value = ([], [])  # シンボルなし
        mock_parser_cls.return_value = mock_parser

        request = SplitCodeRequest(
            content="# コメントのみ\n# シンボルなし",
            filename="empty.py",
        )

        response = client.post("/api/split/code", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["parts"] == []
        assert data["language"] == "python"
        assert "No symbols found" in data["indexContent"]

    def test_ut_spl_008_unsupported_language(self):
        """UT-SPL-008: エラー（未対応言語）"""
        request = SplitCodeRequest(
            content="console.log('hello');",
            filename="test.js",  # JavaScript は未対応
        )

        response = client.post("/api/split/code", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "未対応" in data["error"]
        assert ".js" in data["error"]

    @patch("code2map.parsers.python_parser.PythonParser")
    def test_ut_spl_009_parse_error(self, mock_parser_cls):
        """UT-SPL-009: エラー（パースエラー）"""
        mock_parser = MagicMock()
        mock_parser.parse.side_effect = Exception("Syntax error")
        mock_parser_cls.return_value = mock_parser

        request = SplitCodeRequest(
            content="def broken(",  # 構文エラーのあるコード
            filename="broken.py",
        )

        response = client.post("/api/split/code", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "エラー" in data["error"]


class TestEstimateTokens:
    """_estimate_tokens() のテスト"""

    def test_estimate_tokens_english(self):
        """英語のみのトークン推定"""
        from app.routers.split import _estimate_tokens

        # 英語は約0.25トークン/文字
        text = "Hello World"  # 11文字
        tokens = _estimate_tokens(text)
        assert tokens == int(11 * 0.25)

    def test_estimate_tokens_japanese(self):
        """日本語のみのトークン推定"""
        from app.routers.split import _estimate_tokens

        # 日本語は約1.5トークン/文字
        text = "こんにちは"  # 5文字（全て0x3000以上）
        tokens = _estimate_tokens(text)
        assert tokens == int(5 * 1.5)

    def test_estimate_tokens_mixed(self):
        """日本語と英語の混在"""
        from app.routers.split import _estimate_tokens

        text = "Hello世界"  # Hello(5文字) + 世界(2文字)
        tokens = _estimate_tokens(text)
        expected = int(2 * 1.5 + 5 * 0.25)  # 日本語2文字 + 英語5文字
        assert tokens == expected
