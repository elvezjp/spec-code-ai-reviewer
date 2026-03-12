from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Dict, List, Tuple

from code2map.models.symbol import Symbol
from code2map.utils.file_utils import ensure_dir, slice_lines, write_text

_UNSAFE_CHARS = re.compile(r'[<>:"/\\|?*]')


def _short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:4]


def _comment_prefix(language: str, ext: str) -> str:
    if language == "python" or ext == ".py":
        return "#"
    return "//"


def _build_filename(symbol: Symbol, ext: str, existing: Dict[str, int]) -> str:
    if symbol.kind == "class":
        base = f"{symbol.name}.class{ext}"
    elif symbol.kind == "method":
        parent = symbol.parent or "Anonymous"
        base = f"{parent}_{symbol.name}{ext}"
    else:
        base = f"{symbol.name}{ext}"

    base = _UNSAFE_CHARS.sub("", base)

    if base in existing:
        seed = symbol.signature or f"{symbol.display_name()}_{symbol.start_line}"
        stem = base[: -len(ext)]
        base = f"{stem}__{_short_hash(seed)}{ext}"
    existing[base] = existing.get(base, 0) + 1
    return base


def generate_parts(
    symbols: List[Symbol],
    lines: List[str],
    out_dir: str,
    dry_run: bool = False,
) -> List[Tuple[Symbol, str]]:
    ext = Path(symbols[0].original_file).suffix if symbols else ""
    parts_dir = Path(out_dir) / "parts"
    if not dry_run:
        ensure_dir(out_dir)
        ensure_dir(str(parts_dir))

    existing: Dict[str, int] = {}
    fragments: List[Tuple[Symbol, str]] = []

    for symbol in symbols:
        if symbol.kind not in {"class", "method", "function"}:
            continue
        fragment = slice_lines(lines, symbol.start_line, symbol.end_line)
        filename = _build_filename(symbol, ext, existing)
        symbol.part_file = f"parts/{filename}"
        fragments.append((symbol, fragment))

        if dry_run:
            continue

        prefix = _comment_prefix(symbol.language, ext)
        header_lines = [
            f"{prefix} code2map fragment (non-buildable)",
        ]
        if symbol.id:
            header_lines.append(f"{prefix} id: {symbol.id}")
        header_lines.extend([
            f"{prefix} original: {Path(symbol.original_file).as_posix()}",
            f"{prefix} lines: {symbol.start_line}-{symbol.end_line}",
            f"{prefix} symbol: {symbol.display_name()}",
        ])
        notes: List[str] = []
        if symbol.dependencies:
            notes.append("references " + ", ".join(symbol.dependencies))
        if symbol.calls:
            notes.append("calls " + ", ".join(symbol.calls))
        if notes:
            header_lines.append(f"{prefix} notes: {'; '.join(notes)}")

        content = "\n".join(header_lines) + "\n" + fragment + "\n"
        write_text(str(parts_dir / filename), content)

    return fragments
