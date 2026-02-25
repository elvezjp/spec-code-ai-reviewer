from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple

from code2map.models.symbol import Symbol


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> Tuple[List[Symbol], List[str]]:
        raise NotImplementedError
