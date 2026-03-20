"""パーサー基底クラス"""

from abc import ABC, abstractmethod
from typing import List, Tuple

from md2map.models.section import Section


class BaseParser(ABC):
    """パーサーの基底クラス

    マークダウンや他のマークアップ言語のパーサーはこのクラスを継承する。
    """

    @abstractmethod
    def parse(
        self, file_path: str, max_depth: int = 3
    ) -> Tuple[List[Section], List[str]]:
        """ファイルをパースしてセクションリストを返す

        Args:
            file_path: 入力ファイルパス
            max_depth: 分割対象の最大見出し深さ（1-6）

        Returns:
            Tuple[List[Section], List[str]]: (セクションリスト, 警告リスト)
        """
        raise NotImplementedError
