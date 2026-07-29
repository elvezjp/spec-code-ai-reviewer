"""excel2md (CSV+Mermaid) を用いた Markdown 変換ツール。"""

import tempfile
from pathlib import Path

from excel2md.cli import build_argparser
from excel2md.runner import run

from .base import MarkdownTool
from ..safe_path import safe_filename


class Excel2mdMermaidTool(MarkdownTool):
    """excel2md を利用したExcel→CSVマークダウン+Mermaid変換。

    概要セクションあり、検証用メタデータなし、Mermaidフローチャートありで出力する。
    シェイプからMermaidフローチャートを検出して出力する（mermaid_detect_mode=shapes）。
    """

    @property
    def name(self) -> str:
        """ツールの識別名。"""
        return "excel2md_mermaid"

    @property
    def display_name(self) -> str:
        """ツールの表示名。"""
        return "excel2md (CSV+Mermaid)"

    def convert(self, file_content: bytes, filename: str) -> str:
        """file_contentとfilenameを受け取りCSVマークダウン+Mermaid文字列を返す。"""
        # 一時ディレクトリで作業
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # 入力ファイルを作成
            input_path = tmpdir_path / safe_filename(filename)
            input_path.write_bytes(file_content)

            # 出力パスを設定（run()がファイルを生成する）
            output_basename = input_path.stem
            # CSVマークダウンモードでは {basename}_csv.md が生成される
            expected_output = tmpdir_path / f"{output_basename}_csv.md"

            # argparserでオプションを設定
            # 概要セクションあり（デフォルト）、検証用メタデータなし、Mermaidあり
            parser = build_argparser()
            args = parser.parse_args(
                [
                    str(input_path),
                    "-o",
                    str(tmpdir_path / f"{output_basename}.md"),
                    "--csv-markdown-enabled",
                    "--no-csv-include-metadata",
                    "--mermaid-enabled",
                    "--mermaid-detect-mode",
                    "shapes",
                ]
            )

            # 変換実行
            result = run(str(input_path), args.output, args)

            # 出力ファイルを読み取り
            if result and Path(result).exists():
                output_file = Path(result)
            elif expected_output.exists():
                output_file = expected_output
            else:
                raise RuntimeError(
                    "excel2md変換に失敗しました: 出力ファイルが見つかりません"
                )

            return output_file.read_text(encoding="utf-8")

    def preprocess_for_organize(self, markdown: str) -> str:
        """excel2mdの概要セクションを除去する。

        excel2mdの出力構造:
        - タイトル: # CSV出力: filename.xlsx または # SheetName
        - 概要セクション: ## 概要 ... (ツール説明文)
        - セパレータ: ---
        - 本文: # Sheet: ... (実際のシート内容)

        タイトルと概要セクションはツール固有の情報であり、
        メタ情報は別途付与するため、最初の --- までを除去する。
        """
        # セパレータ行を検出して、それ以降を返す
        lines = markdown.split("\n")

        for i, line in enumerate(lines):
            # --- のみの行を検出（セパレータ）
            if line.strip() == "---":
                # セパレータ以降を返す（空行をスキップ）
                remaining = "\n".join(lines[i + 1 :]).strip()
                if remaining:
                    return remaining
                break

        # セパレータが見つからない場合はそのまま返す
        return markdown
