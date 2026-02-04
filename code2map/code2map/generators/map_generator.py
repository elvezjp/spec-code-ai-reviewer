from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import List, Tuple

from code2map.models.symbol import Symbol
from code2map.utils.file_utils import write_text


def _checksum(fragment: str) -> str:
    return hashlib.sha256(fragment.encode("utf-8")).hexdigest()


def generate_map(entries: List[Tuple[Symbol, str]], output_path: str) -> None:
    payload = []
    for symbol, fragment in entries:
        if not symbol.part_file:
            continue
        payload.append(
            {
                "symbol": symbol.display_name(),
                "type": symbol.kind,
                "original_file": Path(symbol.original_file).name,
                "original_start_line": symbol.start_line,
                "original_end_line": symbol.end_line,
                "part_file": symbol.part_file,
                "checksum": _checksum(fragment),
            }
        )

    content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    write_text(output_path, content)
