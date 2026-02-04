from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Symbol:
    name: str
    kind: str  # class, method, function
    start_line: int
    end_line: int
    original_file: str
    language: str
    parent: Optional[str] = None
    qualname: Optional[str] = None
    role: Optional[str] = None
    signature: Optional[str] = None
    calls: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)
    part_file: Optional[str] = None

    def display_name(self) -> str:
        if self.kind == "method" and self.parent:
            return f"{self.parent}#{self.name}"
        return self.name

    def line_range(self) -> str:
        return f"L{self.start_line}–L{self.end_line}"
