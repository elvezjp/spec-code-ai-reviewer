from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from code2map.generators.index_generator import generate_index
from code2map.generators.map_generator import generate_map
from code2map.generators.parts_generator import generate_parts
from code2map.parsers.java_parser import JavaParser
from code2map.parsers.python_parser import PythonParser
from code2map.utils.file_utils import read_lines, ensure_dir
from code2map.utils.logger import setup_logger, get_logger


LANG_EXT = {
    ".java": "java",
    ".py": "python",
}


def _detect_lang(path: str, explicit: str | None) -> str | None:
    if explicit:
        return explicit.lower()
    ext = Path(path).suffix.lower()
    return LANG_EXT.get(ext)


def _parser_for(lang: str):
    if lang == "java":
        return JavaParser()
    if lang == "python":
        return PythonParser()
    return None


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="code2map")
    sub = parser.add_subparsers(dest="command")

    build = sub.add_parser("build", help="Generate INDEX.md, parts, and MAP.json")
    build.add_argument("input_file")
    build.add_argument("--out", default="./code2map-out")
    build.add_argument("--lang", choices=["java", "python"], default=None)
    build.add_argument("--id-prefix", default="CD", help="Symbol ID prefix (default: CD)")
    build.add_argument("--verbose", action="store_true")
    build.add_argument("--dry-run", action="store_true")

    return parser


def _print_dry_run(symbols, parts: List[str], input_file: str) -> None:
    print("Symbols:")
    for symbol in symbols:
        print(f"- {symbol.display_name()} ({symbol.kind}) {symbol.line_range()}")
    print("\nPlanned outputs:")
    print(f"- INDEX.md (from {Path(input_file).name})")
    for part in parts:
        print(f"- {part}")
    print("- MAP.json")


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()

    if args.command != "build":
        parser.print_help()
        sys.exit(1)

    setup_logger(args.verbose)
    logger = get_logger("code2map")

    input_path = Path(args.input_file)
    if not input_path.exists():
        logger.error("Input file not found: %s", input_path)
        sys.exit(1)

    lang = _detect_lang(str(input_path), args.lang)
    if not lang:
        logger.error("Unable to detect language. Use --lang to specify.")
        sys.exit(1)

    parser_impl = _parser_for(lang)
    if not parser_impl:
        logger.error("Unsupported language: %s", lang)
        sys.exit(1)

    symbols, warnings = parser_impl.parse(str(input_path))
    for warning in warnings:
        logger.warning(warning)

    # シンボルIDの割り当て
    id_prefix = args.id_prefix
    for i, symbol in enumerate(symbols, start=1):
        symbol.id = f"{id_prefix}{i}"

    lines = read_lines(str(input_path))
    out_dir = args.out

    if args.dry_run:
        parts = generate_parts(symbols, lines, out_dir, dry_run=True)
        part_paths = [entry[0].part_file for entry in parts if entry[0].part_file]
        _print_dry_run(symbols, part_paths, str(input_path))
        sys.exit(2 if warnings else 0)

    ensure_dir(out_dir)
    fragments = generate_parts(symbols, lines, out_dir, dry_run=False)
    generate_index(symbols, warnings, lines, str(Path(out_dir) / "INDEX.md"), str(input_path))
    generate_map(fragments, str(Path(out_dir) / "MAP.json"))

    sys.exit(2 if warnings else 0)


if __name__ == "__main__":
    main()
