"""マークダウンパーサー"""

import json
import math
import re
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from md2map.models.section import Section
from md2map.parsers.base_parser import BaseParser
from md2map.utils.file_utils import read_file
from md2map.utils.logger import get_logger

if TYPE_CHECKING:
    from md2map.llm.base_provider import BaseLLMProvider
    from md2map.llm.config import LLMConfig


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

    def __init__(
        self,
        split_mode: str = "heading",
        split_threshold: int = 500,
        max_subsections: int = 5,
        llm_config: Optional["LLMConfig"] = None,
        llm_provider: Optional["BaseLLMProvider"] = None,
    ) -> None:
        if split_mode not in {"heading", "nlp", "ai"}:
            raise ValueError(f"Invalid split_mode: {split_mode}")
        self._nlp_tokenizer = None
        self._llm_provider: Optional["BaseLLMProvider"] = None
        if split_mode == "nlp":
            try:
                from sudachipy import dictionary
            except ImportError as exc:
                raise RuntimeError(
                    "NLP mode requires optional dependency. "
                    "Install with: pip install md2map[nlp]"
                ) from exc
            self._nlp_tokenizer = dictionary.Dictionary().create()
        if split_mode == "ai":
            if llm_provider is not None:
                self._llm_provider = llm_provider
            elif llm_config is not None:
                from md2map.llm.factory import get_llm_provider
                self._llm_provider = get_llm_provider(llm_config)
            else:
                # 後方互換: 環境変数からフォールバック
                from md2map.llm.factory import build_llm_config_from_env
                fallback_config = build_llm_config_from_env(provider="bedrock")
                from md2map.llm.factory import get_llm_provider
                self._llm_provider = get_llm_provider(fallback_config)
        self.split_mode = split_mode
        self.split_threshold = max(1, split_threshold)
        self.max_subsections = max(1, max_subsections)

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

        # 追加分割（heading モード以外）
        if self.split_mode != "heading":
            sections = self._refine_sections(sections, lines)

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
                section.path = f"{stack[-1].path} > {section.display_name()}"
            else:
                section.path = section.display_name()

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
        skip_first = self.HEADING_PATTERN.match(section_lines[0].rstrip()) is not None
        section.summary = self._extract_summary(section_lines, skip_first_line=skip_first)

        # リンク抽出
        section.links = self.LINK_PATTERN.findall(section_text)

        # キーワード抽出（太字）
        section.keywords = list(set(self.BOLD_PATTERN.findall(section_text)))

        # 単語数カウント
        section.word_count = self._count_words(section_text)

    def _extract_summary(self, lines: List[str], skip_first_line: bool = True) -> Optional[str]:
        """最初の段落を要約として抽出する（100文字まで）

        Args:
            lines: セクションの行リスト

        Returns:
            要約文字列（100文字以内）、なければNone
        """
        content_started = False
        summary_lines: List[str] = []

        source_lines = lines[1:] if skip_first_line else lines
        for line in source_lines:
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

    def _get_own_content_range(
        self, section: Section, sections: List[Section]
    ) -> Tuple[int, int]:
        """セクションの自身コンテンツ範囲を返す

        子セクションを持つ場合は、見出し行の次〜最初の子セクションの開始行の前行まで。
        末端セクションの場合は、見出し行の次〜セクション終了行まで。

        Returns:
            (own_start, own_end): 自身コンテンツの行範囲（1-based, inclusive）
        """
        own_start = section.start_line + 1
        own_end = section.end_line

        for s in sections:
            if s.parent is section:
                own_end = s.start_line - 1
                break

        return own_start, own_end

    def _refine_sections(self, sections: List[Section], lines: List[str]) -> List[Section]:
        """セクションを再分割してサブスプリットを挿入する"""
        if self.max_subsections <= 1:
            return sections

        if self.split_mode not in ("nlp", "ai"):
            return sections

        refined: List[Section] = []

        for section in sections:
            # 自身のコンテンツ範囲を算出
            own_start, own_end = self._get_own_content_range(section, sections)

            if own_start > own_end:
                refined.append(section)
                continue

            own_text = "".join(lines[own_start - 1 : own_end])
            total_count = self._count_words(own_text)

            if total_count < self.split_threshold:
                refined.append(section)
                continue

            if self.split_mode == "ai":
                # AI モード: 行番号ベース
                content_lines_count = own_end - own_start + 1
                if content_lines_count < 2:
                    refined.append(section)
                    continue

                target_parts = min(
                    self.max_subsections,
                    max(2, math.ceil(total_count / self.split_threshold)),
                )

                line_ranges, titles = self._select_chunks_ai(
                    section, lines, own_start, own_end, target_parts
                )
                if not line_ranges:
                    line_ranges = self._chunk_lines_by_threshold(
                        lines, own_start, own_end, total_count, target_parts
                    )
                    titles = None

                if len(line_ranges) < 2:
                    refined.append(section)
                    continue

                refined.append(section)
                # 最初のサブスプリットに見出し行を含める
                line_ranges[0] = (section.start_line, line_ranges[0][1])
                if titles:
                    virtual_sections = self._build_virtual_sections_with_titles(
                        section, line_ranges, titles
                    )
                else:
                    virtual_sections = self._build_virtual_sections(
                        section, line_ranges
                    )
                refined.extend(virtual_sections)

            else:
                # NLP モード: 段落ベース
                paragraphs = self._split_paragraphs(lines, own_start, own_end)
                if len(paragraphs) < 2:
                    refined.append(section)
                    continue

                target_parts = min(
                    self.max_subsections,
                    max(2, math.ceil(total_count / self.split_threshold)),
                )
                target_parts = min(target_parts, len(paragraphs))

                boundaries = self._select_boundaries_nlp(
                    section, lines, paragraphs, target_parts
                )
                if boundaries:
                    chunks = self._chunks_from_boundaries(paragraphs, boundaries)
                else:
                    chunks = self._chunk_paragraphs_by_threshold(
                        paragraphs, lines, total_count, target_parts
                    )

                if len(chunks) < 2:
                    refined.append(section)
                    continue

                refined.append(section)
                # 段落チャンクを行範囲タプルに変換
                line_ranges = [
                    (chunk[0][0], chunk[-1][1]) for chunk in chunks
                ]
                # 最初のサブスプリットに見出し行を含める
                line_ranges[0] = (section.start_line, line_ranges[0][1])
                virtual_sections = self._build_virtual_sections(
                    section, line_ranges
                )
                refined.extend(virtual_sections)

        self._build_hierarchy(refined)
        return refined

    def _split_paragraphs(
        self, lines: List[str], start_line: int, end_line: int
    ) -> List[Tuple[int, int]]:
        """段落単位で分割して (start_line, end_line) の配列を返す"""
        paragraphs: List[Tuple[int, int]] = []
        i = start_line

        while i <= end_line:
            if not lines[i - 1].strip():
                i += 1
                continue
            para_start = i
            while i <= end_line and lines[i - 1].strip():
                i += 1
            para_end = i - 1
            paragraphs.append((para_start, para_end))

        return paragraphs

    def _chunks_from_boundaries(
        self, paragraphs: List[Tuple[int, int]], boundaries: List[int]
    ) -> List[List[Tuple[int, int]]]:
        """境界インデックスから段落チャンクを生成する"""
        chunks: List[List[Tuple[int, int]]] = []
        prev = 0
        for boundary in sorted(boundaries):
            if boundary < prev or boundary >= len(paragraphs) - 1:
                continue
            chunks.append(paragraphs[prev : boundary + 1])
            prev = boundary + 1
        if prev < len(paragraphs):
            chunks.append(paragraphs[prev:])
        return chunks

    def _chunk_paragraphs_by_threshold(
        self,
        paragraphs: List[Tuple[int, int]],
        lines: List[str],
        total_count: int,
        target_parts: int,
    ) -> List[List[Tuple[int, int]]]:
        """閾値ベースで段落を均等に分割する"""
        para_counts = [
            self._count_words("".join(lines[s - 1 : e]))
            for s, e in paragraphs
        ]
        target_per_part = max(1, math.ceil(total_count / target_parts))

        chunks: List[List[Tuple[int, int]]] = []
        current_chunk: List[Tuple[int, int]] = []
        current_count = 0

        for (para_range, para_count) in zip(paragraphs, para_counts):
            if (
                current_chunk
                and current_count + para_count > target_per_part
                and len(chunks) < target_parts - 1
            ):
                chunks.append(current_chunk)
                current_chunk = []
                current_count = 0
            current_chunk.append(para_range)
            current_count += para_count

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _select_boundaries_nlp(
        self,
        section: Section,
        lines: List[str],
        paragraphs: List[Tuple[int, int]],
        target_parts: int,
    ) -> List[int]:
        """NLP（Sudachi）で境界候補を選ぶ"""
        if self._nlp_tokenizer is None:
            return []

        para_terms: List[set[str]] = []
        for start, end in paragraphs:
            text = "".join(lines[start - 1 : end])
            nouns = {
                m.surface()
                for m in self._nlp_tokenizer.tokenize(text)
                if m.part_of_speech()[0] == "名詞"
            }
            para_terms.append(nouns)

        scores: List[Tuple[int, float]] = []
        for i in range(len(para_terms) - 1):
            a = para_terms[i]
            b = para_terms[i + 1]
            if not a and not b:
                similarity = 1.0
            elif not a or not b:
                similarity = 0.0
            else:
                similarity = len(a & b) / len(a | b)
            scores.append((i, similarity))

        num_splits = max(0, min(target_parts - 1, len(scores)))
        if num_splits == 0:
            return []

        scores.sort(key=lambda item: item[1])
        boundaries = [idx for idx, _ in scores[:num_splits]]
        return sorted(set(boundaries))

    def _add_line_numbers(self, content: str) -> str:
        """テキストに 1 始まりの行番号を付与する

        add-line-numbers パッケージを使用する。行番号は常に 1〜N（相対番号）。
        AI はこの相対番号で分割点を返し、呼び出し元で元ファイルの行番号に変換する。
        """
        from add_line_numbers import add_line_numbers_to_content

        numbered_text, _ = add_line_numbers_to_content(content)
        return numbered_text

    def _select_chunks_ai(
        self,
        section: Section,
        lines: List[str],
        own_start: int,
        own_end: int,
        target_parts: int,
    ) -> Tuple[List[Tuple[int, int]], Optional[List[str]]]:
        """AI（LLMプロバイダー）で行番号ベースのグループ分けとタイトルを取得する

        AI には 1〜N の相対行番号付きテキストを送信し、
        レスポンスの相対行番号を元ファイルの行番号に変換して返す。
        """
        if self._llm_provider is None:
            return [], None

        content = "".join(lines[own_start - 1 : own_end])
        numbered_text = self._add_line_numbers(content)
        total_lines = own_end - own_start + 1

        system_text = (
            "# 役割\n"
            "あなたは文書構造の分析に特化したアシスタントです。\n"
            "\n"
            "# 目的\n"
            "行番号付きテキストを、意味的なまとまりが壊れないよう"
            "話題や内容の切れ目で区切ってください。\n"
            "各区間には、その内容を端的に表すタイトルを付与してください。\n"
            "\n"
            "# 出力形式\n"
            "JSON 配列のみを返してください。説明文やマークダウン装飾は不要です。\n"
            "各要素は以下のフィールドを持つオブジェクトです:\n"
            "- title (string): 区間の内容を表す簡潔なタイトル（文書の言語に合わせる）\n"
            "- start_line (integer): 区間の開始行番号\n"
            "- end_line (integer): 区間の終了行番号（inclusive）\n"
            "\n"
            "スキーマ:\n"
            f"[{{\"title\": \"...\", \"start_line\": 1, \"end_line\": ...}}, ...]\n"
            "\n"
            "# 注意事項\n"
            "- 意味的に関連する行は同じ区間に含め、話題の変わり目で区切ること\n"
            "- 最初の区間は行 1 から開始すること\n"
            "- 前の区間の end_line + 1 が次の区間の start_line と一致すること"
            "（隙間・重複の禁止）\n"
            f"- 最後の区間は行 {total_lines} で終了すること"
            "（すべての行を漏れなくカバー）\n"
            "- タイトルは元の文書の言語（日本語の文書なら日本語）で付与すること\n"
        )
        user_text = (
            f"以下のテキストを、意味的なまとまりを保ちつつ"
            f"最大 {target_parts} つに区切ってください。\n"
            f"\n"
            f"{numbered_text}"
        )

        logger = get_logger()
        try:
            response_text = self._llm_provider.send_message(system_text, user_text)
        except Exception as exc:
            logger.warning(f"AI API call failed: {exc}")
            return [], None

        # LLM が ```json ... ``` で囲んで返す場合に対応
        stripped = response_text.strip()
        if stripped.startswith("```"):
            first_newline = stripped.find("\n")
            if first_newline != -1:
                stripped = stripped[first_newline + 1:]
            if stripped.endswith("```"):
                stripped = stripped[:-3]
            response_text = stripped.strip()
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            return [], None

        # LLM のレスポンスは 1-based 相対行番号
        items: List[Tuple[int, int, str]] = []
        for item in data:
            try:
                sl = int(item["start_line"])
                el = int(item["end_line"])
                title = str(item.get("title") or "").strip()
            except (ValueError, TypeError, KeyError):
                continue
            if sl < 1 or el > total_lines or el < sl:
                continue
            items.append((sl, el, title))

        if not items:
            return [], None

        items.sort(key=lambda x: x[0])
        # Validate coverage and non-overlap (1-based relative)
        if items[0][0] != 1 or items[-1][1] != total_lines:
            return [], None
        for i in range(len(items) - 1):
            if items[i][1] + 1 != items[i + 1][0]:
                return [], None

        # 相対行番号を元ファイルの行番号に変換
        line_ranges: List[Tuple[int, int]] = []
        titles: List[str] = []
        for sl, el, title in items:
            actual_start = own_start + sl - 1
            actual_end = own_start + el - 1
            line_ranges.append((actual_start, actual_end))
            titles.append(title)

        return line_ranges, titles

    def _chunk_lines_by_threshold(
        self,
        lines: List[str],
        own_start: int,
        own_end: int,
        total_count: int,
        target_parts: int,
    ) -> List[Tuple[int, int]]:
        """行数ベースで均等に分割する（AI モードのフォールバック）"""
        total_lines = own_end - own_start + 1
        lines_per_part = max(1, math.ceil(total_lines / target_parts))

        line_ranges: List[Tuple[int, int]] = []
        current_start = own_start

        while current_start <= own_end:
            current_end = min(current_start + lines_per_part - 1, own_end)
            # 最後のパート以外で残りが少ない場合はまとめる
            if (
                len(line_ranges) == target_parts - 1
                or own_end - current_end < lines_per_part // 2
            ):
                current_end = own_end
            line_ranges.append((current_start, current_end))
            current_start = current_end + 1

        return line_ranges

    def _build_virtual_sections_with_titles(
        self,
        section: Section,
        line_ranges: List[Tuple[int, int]],
        titles: List[str],
    ) -> List[Section]:
        """AI 生成タイトルを使用してサブスプリットセクションを生成する"""
        virtual_sections: List[Section] = []
        base_level = min(section.level + 1, 6)
        total = len(line_ranges)

        for i, (start_line, end_line) in enumerate(line_ranges, start=1):
            raw_title = titles[i - 1] if i - 1 < len(titles) else ""
            if raw_title:
                display_title = f"{section.display_name()}: {raw_title}"
            else:
                display_title = f"{section.display_name()}: part-{i}"
            virtual = Section(
                title=section.title,
                level=base_level,
                start_line=start_line,
                end_line=end_line,
                original_file=section.original_file,
                is_subsplit=True,
                note=f"Subsplit of {section.id or section.title} (L{start_line}\u2013L{end_line}, {self.split_mode} boundary split)",
                subsplit_title=display_title,
            )
            virtual_sections.append(virtual)

        return virtual_sections

    def _build_virtual_sections(
        self,
        section: Section,
        line_ranges: List[Tuple[int, int]],
    ) -> List[Section]:
        """サブスプリットセクションを生成する"""
        virtual_sections: List[Section] = []
        base_level = min(section.level + 1, 6)
        total = len(line_ranges)

        for i, (start_line, end_line) in enumerate(line_ranges, start=1):
            base_title = section.display_name()
            subsplit_title = f"{base_title}: part-{i}"
            virtual = Section(
                title=section.title,
                level=base_level,
                start_line=start_line,
                end_line=end_line,
                original_file=section.original_file,
                is_subsplit=True,
                note=f"Subsplit of {section.id or section.title} (L{start_line}\u2013L{end_line}, {self.split_mode} threshold split)",
                subsplit_title=subsplit_title,
            )
            virtual_sections.append(virtual)

        return virtual_sections
