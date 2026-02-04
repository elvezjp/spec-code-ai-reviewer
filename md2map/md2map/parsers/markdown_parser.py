"""マークダウンパーサー"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from md2map.models.section import Section
from md2map.parsers.base_parser import BaseParser
from md2map.utils.file_utils import read_file
from md2map.utils.logger import get_logger


class MarkdownParser(BaseParser):
    """マークダウンファイルパーサー

    ATX形式の見出し（# 記法）を解析してセクションに分割する。
    """

    # 見出しパターン（ATX形式）
    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")

    # コードブロック開始/終了パターン
    CODE_BLOCK_PATTERN = re.compile(r"^(`{3,}|~{3,})")

    # リンクパターン
    LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    # 太字パターン（キーワード抽出用）
    BOLD_PATTERN = re.compile(r"\*\*([^*]+)\*\*")

    # フロントマターパターン
    FRONTMATTER_PATTERN = re.compile(r"^---\s*$")

    def parse(
        self, file_path: str, max_depth: int = 3
    ) -> Tuple[List[Section], List[str]]:
        """マークダウンファイルをパースする

        Args:
            file_path: 入力ファイルパス
            max_depth: 分割対象の最大見出し深さ（1-6）

        Returns:
            Tuple[List[Section], List[str]]: (セクションリスト, 警告リスト)
        """
        logger = get_logger()
        warnings: List[str] = []

        # ファイル読み込み
        lines, read_warnings = read_file(file_path)
        warnings.extend(read_warnings)

        if lines is None:
            return [], warnings

        file_name = Path(file_path).name

        # 見出し抽出
        headings = self._extract_headings(lines, max_depth)

        # 警告: 見出しが見つからない場合
        if not headings:
            warning_msg = "No headings found in the document"
            warnings.append(warning_msg)
            logger.warning(warning_msg)

            # 文書全体を1セクションとして扱う
            section = Section(
                title=Path(file_path).stem,
                level=1,
                start_line=1,
                end_line=len(lines),
                original_file=file_name,
                path=Path(file_path).stem,
            )
            self._extract_section_info(section, lines)
            return [section], warnings

        # 見出しレベルのスキップをチェック
        skip_warnings = self._check_level_skip(headings)
        warnings.extend(skip_warnings)

        # セクション構築
        sections = self._build_sections(headings, lines, file_name)

        # 各セクションの追加情報を抽出
        for section in sections:
            self._extract_section_info(section, lines)

        return sections, warnings

    def _extract_headings(
        self, lines: List[str], max_depth: int
    ) -> List[Dict[str, any]]:
        """見出しを抽出する（コードブロック・フロントマター内は除外）

        Args:
            lines: ファイルの行リスト
            max_depth: 最大見出し深さ

        Returns:
            見出し情報のリスト [{"level": int, "title": str, "line": int}, ...]
        """
        headings: List[Dict[str, any]] = []
        in_code_block = False
        code_block_marker: Optional[str] = None
        in_frontmatter = False
        frontmatter_started = False

        for i, line in enumerate(lines, start=1):
            stripped = line.rstrip()

            # フロントマターの処理（ファイル先頭の --- で囲まれた部分）
            if i == 1 and self.FRONTMATTER_PATTERN.match(stripped):
                in_frontmatter = True
                frontmatter_started = True
                continue

            if frontmatter_started and in_frontmatter:
                if self.FRONTMATTER_PATTERN.match(stripped):
                    in_frontmatter = False
                continue

            # コードブロックの追跡
            code_match = self.CODE_BLOCK_PATTERN.match(stripped)
            if code_match:
                marker = code_match.group(1)[0]  # ` または ~
                if not in_code_block:
                    in_code_block = True
                    code_block_marker = marker
                elif marker == code_block_marker:
                    in_code_block = False
                    code_block_marker = None
                continue

            if in_code_block:
                continue

            # 見出しマッチ
            match = self.HEADING_PATTERN.match(stripped)
            if match:
                level = len(match.group(1))
                if level <= max_depth:
                    headings.append({
                        "level": level,
                        "title": match.group(2).strip(),
                        "line": i,
                    })

        return headings

    def _check_level_skip(self, headings: List[Dict[str, any]]) -> List[str]:
        """見出しレベルのスキップをチェックする

        Args:
            headings: 見出し情報のリスト

        Returns:
            警告メッセージのリスト
        """
        warnings: List[str] = []
        logger = get_logger()

        prev_level = 0
        for heading in headings:
            level = heading["level"]
            if prev_level > 0 and level > prev_level + 1:
                warning_msg = (
                    f"Heading level skipped from H{prev_level} to H{level} "
                    f"at line {heading['line']}: {heading['title']}"
                )
                warnings.append(warning_msg)
                logger.warning(warning_msg)
            prev_level = level

        return warnings

    def _build_sections(
        self, headings: List[Dict[str, any]], lines: List[str], file_name: str
    ) -> List[Section]:
        """見出しリストからセクションを構築する

        Args:
            headings: 見出し情報のリスト
            lines: ファイルの行リスト
            file_name: ファイル名

        Returns:
            セクションのリスト
        """
        sections: List[Section] = []

        for i, heading in enumerate(headings):
            # 終了行の決定
            if i + 1 < len(headings):
                end_line = headings[i + 1]["line"] - 1
            else:
                end_line = len(lines)

            section = Section(
                title=heading["title"],
                level=heading["level"],
                start_line=heading["line"],
                end_line=end_line,
                original_file=file_name,
            )
            sections.append(section)

        # 階層パスの構築
        self._build_hierarchy(sections)

        return sections

    def _build_hierarchy(self, sections: List[Section]) -> None:
        """セクションの階層関係を構築する

        Args:
            sections: セクションのリスト（変更される）
        """
        stack: List[Section] = []

        for section in sections:
            # スタックから現在のレベル以上のものを削除
            while stack and stack[-1].level >= section.level:
                stack.pop()

            # 親の設定
            if stack:
                section.parent = stack[-1]
                section.path = f"{stack[-1].path} > {section.title}"
            else:
                section.path = section.title

            stack.append(section)

    def _extract_section_info(self, section: Section, lines: List[str]) -> None:
        """セクションの追加情報（要約、キーワード、リンク）を抽出する

        Args:
            section: セクション（変更される）
            lines: ファイルの行リスト
        """
        # セクションの行を取得
        section_lines = lines[section.start_line - 1 : section.end_line]
        section_text = "".join(section_lines)

        # 要約抽出（見出し直後の段落）
        section.summary = self._extract_summary(section_lines)

        # リンク抽出
        section.links = self.LINK_PATTERN.findall(section_text)

        # キーワード抽出（太字）
        section.keywords = list(set(self.BOLD_PATTERN.findall(section_text)))

        # 単語数カウント
        section.word_count = self._count_words(section_text)

    def _extract_summary(self, lines: List[str]) -> Optional[str]:
        """最初の段落を要約として抽出する（100文字まで）

        Args:
            lines: セクションの行リスト

        Returns:
            要約文字列（100文字以内）、なければNone
        """
        content_started = False
        summary_lines: List[str] = []

        for line in lines[1:]:  # 見出し行をスキップ
            stripped = line.strip()

            if not stripped:
                if content_started:
                    break  # 空行で段落終了
                continue

            if stripped.startswith("#"):
                break  # 次の見出しで終了

            # コードブロックの開始は無視
            if self.CODE_BLOCK_PATTERN.match(stripped):
                break

            content_started = True
            summary_lines.append(stripped)

        if not summary_lines:
            return None

        summary = " ".join(summary_lines)

        # 太字記法を除去
        summary = re.sub(r"\*\*([^*]+)\*\*", r"\1", summary)

        if len(summary) > 100:
            summary = summary[:97] + "..."

        return summary

    def _count_words(self, text: str) -> int:
        """単語数/文字数をカウントする

        日本語を含む場合は文字数、それ以外は単語数をカウントする。

        Args:
            text: カウント対象のテキスト

        Returns:
            単語数または文字数
        """
        # 見出し記法やコードブロック記法を除去
        clean_text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        clean_text = re.sub(r"^(`{3,}|~{3,}).*$", "", clean_text, flags=re.MULTILINE)

        # 日本語文字（ひらがな、カタカナ、漢字）が含まれるかチェック
        has_japanese = bool(re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", clean_text))

        if has_japanese:
            # 日本語: 空白と改行を除いた文字数
            return len(re.sub(r"\s", "", clean_text))
        else:
            # 英語: 単語数
            words = clean_text.split()
            return len(words)
