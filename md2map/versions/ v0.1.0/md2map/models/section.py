"""セクションデータモデル"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Section:
    """マークダウンセクションを表すデータクラス

    Attributes:
        title: 見出しテキスト
        level: 見出しレベル（1-6）
        start_line: 開始行番号（1-based）
        end_line: 終了行番号（inclusive）
        original_file: 元ファイル名
        parent: 親セクション
        path: 階層パス（"親 > 子" 形式）
        summary: 要約（最初の段落、100文字まで）
        keywords: キーワードリスト
        links: リンク一覧 [(text, url), ...]
        part_file: 生成されたパートファイルの相対パス
        word_count: 単語数/文字数
        id: セクションの一意識別子（{prefix}{連番} 形式）
    """

    # 基本情報
    title: str
    level: int
    start_line: int
    end_line: int
    original_file: str

    # 階層情報
    parent: Optional["Section"] = None
    path: str = ""

    # 抽出情報
    summary: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    links: List[Tuple[str, str]] = field(default_factory=list)

    # 出力情報
    part_file: Optional[str] = None
    word_count: int = 0
    id: Optional[str] = None

    def display_name(self) -> str:
        """表示用名前を返す

        Returns:
            見出しテキスト
        """
        return self.title

    def line_range(self) -> str:
        """行範囲を "L開始–L終了" 形式で返す

        Returns:
            行範囲文字列
        """
        return f"L{self.start_line}–L{self.end_line}"

    def __repr__(self) -> str:
        return f"Section(title={self.title!r}, level={self.level}, lines={self.line_range()})"
