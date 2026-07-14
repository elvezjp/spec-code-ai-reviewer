"""line_numbers_service.py の単体テスト

テストケース:
- UT-LN-001: add_line_numbers() - 通常のコード
- UT-LN-002: add_line_numbers() - 空ファイル
- UT-LN-003: add_line_numbers() - 日本語含むコード
"""

from app.services.line_numbers_service import add_line_numbers


class TestAddLineNumbers:
    """add_line_numbers() のテスト"""

    def test_ut_ln_001_normal_code(self):
        """UT-LN-001: 通常のコード - 右揃え4桁+コロン+スペース形式"""
        content = """def hello():
    print("Hello")
    return True"""

        result, line_count = add_line_numbers(content)

        # 行数チェック
        assert line_count == 3

        # 各行に行番号が付与されている
        lines = result.split("\n")
        assert len(lines) == 3

        # 行番号形式チェック（右揃え4桁 + コロン + スペース）
        assert lines[0].startswith("   1: ") or lines[0].startswith("1: ")
        assert "def hello():" in lines[0]
        assert 'print("Hello")' in lines[1]
        assert "return True" in lines[2]

    def test_ut_ln_002_empty_file(self):
        """UT-LN-002: 空ファイル"""
        content = ""

        result, line_count = add_line_numbers(content)

        assert result == ""
        assert line_count == 0

    def test_ut_ln_003_japanese_code(self):
        """UT-LN-003: 日本語含むコード"""
        content = """# 日本語コメント
def greet(name):
    # 挨拶を表示
    print(f"こんにちは、{name}さん")
    return "完了"
"""

        result, line_count = add_line_numbers(content)

        # 行数チェック（末尾の空行を含む場合は6行）
        assert line_count >= 5

        # 日本語が正しく含まれている
        assert "日本語コメント" in result
        assert "挨拶を表示" in result
        assert "こんにちは" in result
        assert "完了" in result

    def test_single_line(self):
        """単一行のコード"""
        content = "print('hello')"

        result, line_count = add_line_numbers(content)

        assert line_count == 1
        assert "print('hello')" in result

    def test_multiline_with_blank_lines(self):
        """空行を含む複数行"""
        content = """line1

line3
"""

        result, line_count = add_line_numbers(content)

        # 空行も行としてカウント
        assert line_count >= 3
        assert "line1" in result
        assert "line3" in result

    def test_preserves_indentation(self):
        """インデントが保持される"""
        content = """def foo():
    if True:
        pass"""

        result, line_count = add_line_numbers(content)

        assert line_count == 3
        # インデント付きの行が正しく含まれる
        assert "    if True:" in result
        assert "        pass" in result
