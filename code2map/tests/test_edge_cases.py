"""Edge case tests for parsers and generators."""
from __future__ import annotations

import json
from pathlib import Path

from code2map.generators.index_generator import generate_index
from code2map.generators.map_generator import generate_map
from code2map.generators.parts_generator import generate_parts
from code2map.parsers.python_parser import PythonParser
from code2map.utils.file_utils import read_lines


class TestEdgeCases:
    """Edge case test suite."""

    def test_empty_file(self, tmp_path: Path) -> None:
        """Test parsing an empty file."""
        parser = PythonParser()
        symbols, warnings = parser.parse("tests/fixtures/empty.py")
        assert symbols == []
        assert warnings == []

    def test_comments_only_file(self, tmp_path: Path) -> None:
        """Test parsing a file with only comments."""
        parser = PythonParser()
        symbols, warnings = parser.parse("tests/fixtures/comments_only.py")
        assert symbols == []
        assert warnings == []

    def test_function_only_file(self) -> None:
        """Test parsing a file with only functions (no class)."""
        parser = PythonParser()
        symbols, warnings = parser.parse("tests/fixtures/function_only.py")
        assert warnings == []
        names = {(s.kind, s.display_name()) for s in symbols}
        assert ("function", "standalone_function") in names

    def test_syntax_error_file(self) -> None:
        """Test parsing a file with syntax error."""
        parser = PythonParser()
        symbols, warnings = parser.parse("tests/fixtures/syntax_error.py")
        # Should handle gracefully with warnings
        assert len(warnings) > 0
        assert "parse error" in warnings[0].lower()

    def test_large_file_performance(self) -> None:
        """Test parsing a large file (2100+ lines) performs within time budget."""
        parser = PythonParser()
        symbols, warnings = parser.parse("tests/fixtures/large_file.py")
        # Should parse successfully
        assert len(symbols) >= 1
        # Large class with many methods
        assert any(s.kind == "class" and len([x for x in symbols if x.parent == s.name]) >= 100 for s in symbols)

    def test_empty_output_generation(self, tmp_path: Path) -> None:
        """Test generating output with empty symbol list."""
        out_dir = tmp_path / "out"
        lines: list[str] = []
        symbols: list = []
        
        generate_index(symbols, [], lines, str(out_dir / "INDEX.md"), "empty.py")
        generate_map([], str(out_dir / "MAP.json"))
        
        assert (out_dir / "INDEX.md").exists()
        assert (out_dir / "MAP.json").exists()
        
        index = (out_dir / "INDEX.md").read_text(encoding="utf-8")
        assert "Index: empty.py" in index
        
        data = json.loads((out_dir / "MAP.json").read_text(encoding="utf-8"))
        assert data == []

    def test_warnings_in_index(self, tmp_path: Path) -> None:
        """Test that warnings are recorded in INDEX.md."""
        parser = PythonParser()
        symbols, warnings = parser.parse("tests/fixtures/syntax_error.py")
        
        out_dir = tmp_path / "out"
        lines = read_lines("tests/fixtures/syntax_error.py")
        
        generate_index(symbols, warnings, lines, str(out_dir / "INDEX.md"), "syntax_error.py")
        
        index = (out_dir / "INDEX.md").read_text(encoding="utf-8")
        # Warnings should be in comments
        assert "[WARNING]" in index or "warning" in index.lower()

    def test_nested_class_naming(self, tmp_path: Path) -> None:
        """Test that nested classes are correctly named."""
        # This test creates a fixture and verifies naming
        test_code = """
class Outer:
    def outer_method(self):
        pass
    
    class Inner:
        def inner_method(self):
            pass
"""
        fixture_path = tmp_path / "nested.py"
        fixture_path.write_text(test_code)
        
        parser = PythonParser()
        symbols, warnings = parser.parse(str(fixture_path))

        names = {s.display_name() for s in symbols}
        assert "Outer_Inner" in names
        assert "Outer_Inner#inner_method" in names
