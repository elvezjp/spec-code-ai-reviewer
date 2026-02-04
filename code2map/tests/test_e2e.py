"""End-to-end tests for CLI."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch
import pytest

from code2map.cli import main


def test_cli_build_python_success(tmp_path: Path) -> None:
    """Test `code2map build` with Python file."""
    output_dir = tmp_path / "out"
    
    with patch.object(sys, "argv", [
        "code2map", "build",
        "tests/fixtures/sample.py",
        "--out", str(output_dir),
    ]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
    
    assert (output_dir / "INDEX.md").exists()
    assert (output_dir / "MAP.json").exists()
    assert (output_dir / "parts").exists()
    
    index = (output_dir / "INDEX.md").read_text(encoding="utf-8")
    assert "helper" in index
    assert "Foo" in index
    
    data = json.loads((output_dir / "MAP.json").read_text(encoding="utf-8"))
    assert len(data) >= 2


def test_cli_build_java_success(tmp_path: Path) -> None:
    """Test `code2map build` with Java file."""
    output_dir = tmp_path / "out"
    
    with patch.object(sys, "argv", [
        "code2map", "build",
        "tests/fixtures/sample.java",
        "--out", str(output_dir),
    ]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
    
    assert (output_dir / "INDEX.md").exists()
    assert (output_dir / "MAP.json").exists()
    assert (output_dir / "parts").exists()
    
    index = (output_dir / "INDEX.md").read_text(encoding="utf-8")
    assert "Sample" in index
    assert "work" in index


def test_cli_dry_run(tmp_path: Path, capsys) -> None:
    """Test `--dry-run` option."""
    output_dir = tmp_path / "out"
    
    with patch.object(sys, "argv", [
        "code2map", "build",
        "tests/fixtures/sample.py",
        "--out", str(output_dir),
        "--dry-run",
    ]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
    
    # Verify no files created
    assert not (output_dir / "INDEX.md").exists()
    
    # Verify output shows planned symbols and files
    captured = capsys.readouterr()
    assert "Symbols:" in captured.out
    assert "helper" in captured.out
    assert "Planned outputs:" in captured.out
    assert "INDEX.md" in captured.out


def test_cli_lang_auto_detect(tmp_path: Path) -> None:
    """Test language auto-detection."""
    output_dir = tmp_path / "out"
    
    # Python without --lang
    with patch.object(sys, "argv", [
        "code2map", "build",
        "tests/fixtures/sample.py",
        "--out", str(output_dir),
    ]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
    
    index = (output_dir / "INDEX.md").read_text(encoding="utf-8")
    assert "helper" in index  # Python symbol found


def test_cli_lang_explicit(tmp_path: Path) -> None:
    """Test explicit language specification."""
    output_dir = tmp_path / "out"
    
    with patch.object(sys, "argv", [
        "code2map", "build",
        "tests/fixtures/sample.java",
        "--out", str(output_dir),
        "--lang", "java",
    ]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
    
    index = (output_dir / "INDEX.md").read_text(encoding="utf-8")
    assert "Sample" in index


def test_cli_verbose(tmp_path: Path, capsys) -> None:
    """Test `--verbose` option."""
    output_dir = tmp_path / "out"
    
    with patch.object(sys, "argv", [
        "code2map", "build",
        "tests/fixtures/sample.py",
        "--out", str(output_dir),
        "--verbose",
    ]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
    
    # Verbose mode should not error
    assert (output_dir / "INDEX.md").exists()


def test_cli_input_file_not_found(tmp_path: Path) -> None:
    """Test error when input file not found."""
    output_dir = tmp_path / "out"
    
    with patch.object(sys, "argv", [
        "code2map", "build",
        "tests/fixtures/nonexistent.py",
        "--out", str(output_dir),
    ]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1


def test_cli_unsupported_extension(tmp_path: Path) -> None:
    """Test error with unsupported file extension."""
    output_dir = tmp_path / "out"
    
    with patch.object(sys, "argv", [
        "code2map", "build",
        "tests/fixtures/sample.txt",
        "--out", str(output_dir),
    ]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

