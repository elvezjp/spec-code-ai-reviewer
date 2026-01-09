"""excel2md (CSV+Mermaid) を用いた Markdown 変換ツール。"""

import sys
import tempfile
from pathlib import Path

from .base import MarkdownTool
from .excel2md_tool import EXCEL2MD_PATH


class Excel2mdMermaidTool(MarkdownTool):
    """excel2md v1.7を利用したExcel→CSVマークダウン+Mermaid変換。

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
        # sys.pathを一時的に変更してexcel2mdをインポート
        original_path = sys.path.copy()
        try:
            if str(EXCEL2MD_PATH) not in sys.path:
                sys.path.insert(0, str(EXCEL2MD_PATH))

            # excel2mdモジュールをインポート
            from excel_to_md import build_argparser, run

            # 一時ディレクトリで作業
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_path = Path(tmpdir)

                # 入力ファイルを作成
                input_path = tmpdir_path / filename
                input_path.write_bytes(file_content)

                # 出力パスを設定（run()がファイルを生成する）
                output_basename = input_path.stem
                # CSVマークダウンモードでは {basename}_csv.md が生成される
                expected_output = tmpdir_path / f"{output_basename}_csv.md"

                # argparserでオプションを設定
                # v1.7: 概要セクションあり（デフォルト）、検証用メタデータなし、Mermaidあり
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

        finally:
            sys.path = original_path
