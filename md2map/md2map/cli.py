"""CLI エントリポイント"""

import argparse
import sys
from pathlib import Path

from md2map.generators.index_generator import generate_index
from md2map.generators.map_generator import generate_map
from md2map.generators.parts_generator import generate_parts
from md2map.parsers.markdown_parser import MarkdownParser
from md2map.utils.file_utils import ensure_dir, read_file
from md2map.utils.logger import setup_logger


def build_arg_parser() -> argparse.ArgumentParser:
    """コマンドライン引数パーサーを構築する

    Returns:
        ArgumentParser インスタンス
    """
    parser = argparse.ArgumentParser(
        prog="md2map",
        description="マークダウンファイルを意味的単位に分割し、AI解析用の索引を生成する",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # build サブコマンド
    build_parser = subparsers.add_parser(
        "build", help="マークダウンファイルを解析して出力を生成"
    )
    build_parser.add_argument("input_file", help="解析対象のマークダウンファイル")
    build_parser.add_argument(
        "--out",
        default="./md2map-out",
        help="出力ディレクトリ（デフォルト: ./md2map-out）",
    )
    build_parser.add_argument(
        "--max-depth",
        type=int,
        default=3,
        choices=range(1, 7),
        metavar="N",
        help="分割対象の最大見出し深さ 1-6（デフォルト: 3）",
    )
    build_parser.add_argument(
        "--id-prefix",
        default="MD",
        help="セクションIDのプレフィックス（デフォルト: MD → MD1, MD2, ...）",
    )
    build_parser.add_argument(
        "--verbose", action="store_true", help="詳細ログを出力"
    )
    build_parser.add_argument(
        "--dry-run", action="store_true", help="ファイル生成せずプレビューのみ"
    )

    return parser


def cmd_build(args: argparse.Namespace) -> int:
    """build コマンドの実行

    Args:
        args: パース済みの引数

    Returns:
        終了コード (0: 成功, 1: エラー, 2: 警告あり)
    """
    logger = setup_logger(args.verbose)

    # 入力ファイル検証
    input_path = Path(args.input_file)
    if not input_path.exists():
        logger.error(f"File not found: {args.input_file}")
        return 1

    if not input_path.suffix.lower() == ".md":
        logger.warning(f"File extension is not .md: {args.input_file}")

    # ファイル読み込み
    lines, read_warnings = read_file(str(input_path))
    if lines is None:
        return 1

    # パース
    logger.info(f"Parsing: {input_path}")
    parser = MarkdownParser()
    sections, warnings = parser.parse(str(input_path), args.max_depth)
    warnings.extend(read_warnings)

    # セクションIDの割り当て
    id_prefix = args.id_prefix
    for i, section in enumerate(sections, start=1):
        section.id = f"{id_prefix}{i}"

    # 警告出力
    for warning in warnings:
        logger.warning(warning)

    # dry-run モード
    if args.dry_run:
        print(f"\n=== Detected Sections ({len(sections)}) ===\n")
        for section in sections:
            indent = "  " * (section.level - 1)
            print(f"{indent}[{section.id}] [H{section.level}] {section.title} ({section.line_range()})")

        print(f"\n=== Files to be generated ===\n")
        print(f"  {args.out}/INDEX.md")
        print(f"  {args.out}/MAP.json")
        for section in sections:
            # 仮のファイル名を表示
            from md2map.generators.parts_generator import build_filename
            filename = build_filename(section, set())
            print(f"  {args.out}/parts/{filename}")

        return 2 if warnings else 0

    # 出力ディレクトリ作成
    out_dir = Path(args.out)
    if not ensure_dir(str(out_dir)):
        logger.error(f"Failed to create output directory: {out_dir}")
        return 1

    # parts/ 生成
    logger.info("Generating parts...")
    generate_parts(sections, lines, str(out_dir))

    # INDEX.md 生成
    logger.info("Generating INDEX.md...")
    generate_index(sections, warnings, str(out_dir / "INDEX.md"), input_path.name)

    # MAP.json 生成
    logger.info("Generating MAP.json...")
    generate_map(sections, str(out_dir), str(out_dir / "MAP.json"))

    logger.info(f"Output generated in: {out_dir}")

    return 2 if warnings else 0


def main() -> int:
    """メインエントリポイント

    Returns:
        終了コード
    """
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.command == "build":
        return cmd_build(args)

    return 1


if __name__ == "__main__":
    sys.exit(main())
