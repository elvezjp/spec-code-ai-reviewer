from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from code2map.models.symbol import Symbol
from code2map.utils.file_utils import slice_lines, write_text


def _normalize_role(role: str | None) -> str | None:
    if not role:
        return None
    line = role.strip().splitlines()[0].strip()
    if not line:
        return None
    if "." in line:
        return line.split(".")[0].strip()
    return line


def _detect_side_effects(text: str) -> List[str]:
    if not text:
        return []
    text_l = text.lower()
    rules = [
        ("file io", ["open(", "filewriter", "outputstream", "printwriter", "read(", "write(", "files.", "path", "shutil"]),
        ("stdout", ["print(", "system.out", "console.log", "stderr", "system.err"]),
        ("logging", ["logging.", "logger.", "log."]),
        ("network", ["http", "https", "socket", "request", "fetch(", "resttemplate", "webclient", "client", "post(", "put("]),
        ("db", ["jdbc", "select ", "insert ", "update ", "delete ", "execute(", "save", "persist", "flush", "commit"]),
        ("exceptions", ["throw new", "raise "]),
    ]
    effects: List[str] = []
    for name, keys in rules:
        if any(k in text_l for k in keys):
            effects.append(name)
    return effects


def generate_index(
    symbols: Iterable[Symbol],
    warnings: List[str],
    lines: List[str],
    output_path: str,
    input_file: str,
) -> None:
    symbols = list(symbols)
    classes = [s for s in symbols if s.kind == "class"]
    methods = [s for s in symbols if s.kind == "method"]
    functions = [s for s in symbols if s.kind == "function"]

    parts: List[str] = []
    file_name = Path(input_file).name
    parts.append(f"# Index: {file_name}")

    if warnings:
        for warning in warnings:
            parts.append(f"<!-- [WARNING] {warning} -->")

    if classes:
        parts.append("\n## Classes")
        for symbol in classes:
            id_label = f"[{symbol.id}] " if symbol.id else ""
            line = f"- {id_label}{symbol.display_name()} ({symbol.line_range()})"
            if symbol.part_file:
                line += f" -> {symbol.part_file}"
            parts.append(line)

    if methods:
        parts.append("\n## Methods")
        for symbol in methods:
            id_label = f"[{symbol.id}] " if symbol.id else ""
            line = f"- {id_label}{symbol.display_name()} ({symbol.line_range()})"
            if symbol.part_file:
                line += f" -> {symbol.part_file}"
            parts.append(line)
            role = _normalize_role(symbol.role)
            if role:
                parts.append(f"  - role: {role}")
            if symbol.calls:
                parts.append(f"  - calls: {', '.join(symbol.calls)}")
            code = slice_lines(lines, symbol.start_line, symbol.end_line)
            effects = _detect_side_effects(code)
            if effects:
                parts.append(f"  - side effects: {', '.join(effects)}")

    if functions:
        parts.append("\n## Functions")
        for symbol in functions:
            id_label = f"[{symbol.id}] " if symbol.id else ""
            line = f"- {id_label}{symbol.display_name()} ({symbol.line_range()})"
            if symbol.part_file:
                line += f" -> {symbol.part_file}"
            parts.append(line)
            role = _normalize_role(symbol.role)
            if role:
                parts.append(f"  - role: {role}")
            if symbol.calls:
                parts.append(f"  - calls: {', '.join(symbol.calls)}")
            code = slice_lines(lines, symbol.start_line, symbol.end_line)
            effects = _detect_side_effects(code)
            if effects:
                parts.append(f"  - side effects: {', '.join(effects)}")

    content = "\n".join(parts).rstrip() + "\n"
    write_text(output_path, content)
