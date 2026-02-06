import json
from pathlib import Path

from code2map.generators.index_generator import generate_index
from code2map.generators.map_generator import generate_map
from code2map.generators.parts_generator import generate_parts
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
