import json
from pathlib import Path

from code2map.generators.index_generator import generate_index
from code2map.generators.map_generator import generate_map
from code2map.generators.parts_generator import generate_parts
from code2map.models.symbol import Symbol
from code2map.parsers.python_parser import PythonParser
from code2map.utils.file_utils import read_lines


def test_generators_create_outputs(tmp_path: Path):
    parser = PythonParser()
    symbols, warnings = parser.parse("tests/fixtures/sample.py")
    lines = read_lines("tests/fixtures/sample.py")
    out_dir = tmp_path / "out"

    fragments = generate_parts(symbols, lines, str(out_dir), dry_run=False)
    generate_index(symbols, warnings, lines, str(out_dir / "INDEX.md"), "tests/fixtures/sample.py")
    generate_map(fragments, str(out_dir / "MAP.json"))

    assert (out_dir / "INDEX.md").exists()
    assert (out_dir / "MAP.json").exists()
    assert (out_dir / "parts").exists()
    data = json.loads((out_dir / "MAP.json").read_text(encoding="utf-8"))
    assert len(data) >= 2


def test_generators_with_id(tmp_path: Path):
    """Test generators with ID assigned to symbols."""
    parser = PythonParser()
    symbols, warnings = parser.parse("tests/fixtures/sample.py")
    lines = read_lines("tests/fixtures/sample.py")
    out_dir = tmp_path / "out"

    # IDを割り当て
    for i, symbol in enumerate(symbols, start=1):
        symbol.id = f"CD{i}"

    fragments = generate_parts(symbols, lines, str(out_dir), dry_run=False)
    generate_index(symbols, warnings, lines, str(out_dir / "INDEX.md"), "tests/fixtures/sample.py")
    generate_map(fragments, str(out_dir / "MAP.json"))

    # INDEX.md にIDが含まれる
    index = (out_dir / "INDEX.md").read_text(encoding="utf-8")
    assert "[CD1]" in index

    # MAP.json にIDが含まれる
    data = json.loads((out_dir / "MAP.json").read_text(encoding="utf-8"))
    assert data[0]["id"] == "CD1"
    # IDが最初のキーであることを確認
    assert list(data[0].keys())[0] == "id"

    # parts ファイルにIDが含まれる
    parts_files = list((out_dir / "parts").glob("*.py"))
    assert len(parts_files) > 0
    content = parts_files[0].read_text(encoding="utf-8")
    assert "# id: CD" in content


def test_generators_without_id(tmp_path: Path):
    """Test generators without ID (backward compatibility)."""
    parser = PythonParser()
    symbols, warnings = parser.parse("tests/fixtures/sample.py")
    lines = read_lines("tests/fixtures/sample.py")
    out_dir = tmp_path / "out"

    # IDを割り当てない
    fragments = generate_parts(symbols, lines, str(out_dir), dry_run=False)
    generate_index(symbols, warnings, lines, str(out_dir / "INDEX.md"), "tests/fixtures/sample.py")
    generate_map(fragments, str(out_dir / "MAP.json"))

    # MAP.json にIDフィールドが存在しない
    data = json.loads((out_dir / "MAP.json").read_text(encoding="utf-8"))
    assert "id" not in data[0]

    # INDEX.md に [CD] 形式のIDが含まれない
    index = (out_dir / "INDEX.md").read_text(encoding="utf-8")
    assert "[CD" not in index

    # parts ファイルに id 行が含まれない
    parts_files = list((out_dir / "parts").glob("*.py"))
    assert len(parts_files) > 0
    content = parts_files[0].read_text(encoding="utf-8")
    assert "# id:" not in content
