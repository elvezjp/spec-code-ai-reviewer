from __future__ import annotations

from pathlib import Path
from typing import List


def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def read_lines(path: str) -> List[str]:
    return Path(path).read_text(encoding="utf-8", errors="replace").splitlines()


def write_text(path: str, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def slice_lines(lines: List[str], start_line: int, end_line: int) -> str:
    if start_line < 1:
        start_line = 1
    if end_line < start_line:
        end_line = start_line
    return "\n".join(lines[start_line - 1 : end_line])


def ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)
