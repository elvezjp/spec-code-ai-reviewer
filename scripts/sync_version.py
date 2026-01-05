#!/usr/bin/env python3
"""フロントエンドのバージョンをバックエンドと同期するスクリプト

各バージョンディレクトリの backend/pyproject.toml のバージョンを読み取り、
frontend/index.html のバージョン表記を更新します。

また、引数なしで実行した場合は、全フロントエンドのVERSIONS配列も
利用可能なバージョン一覧で更新します。

使い方:
    python3 scripts/sync_version.py          # 全バージョンを同期 + VERSIONS配列更新
    python3 scripts/sync_version.py v0.2.5   # 指定バージョンのみ同期（VERSIONS配列更新なし）
    python3 scripts/sync_version.py v0.1.1 v0.2.5  # 複数指定も可
    python3 scripts/sync_version.py --no-versions-array  # VERSIONS配列更新をスキップ
"""

import argparse
import re
import sys
from pathlib import Path


def get_root_dir() -> Path:
    """プロジェクトルートディレクトリを取得"""
    return Path(__file__).parent.parent


def get_latest_version_name() -> str | None:
    """latest シンボリックリンクが指すバージョン名（例: v0.2.5）を取得

    Returns:
        latest がシンボリックリンクで versions/vX.Y.Z を指している場合はそのディレクトリ名、
        それ以外（存在しない/シンボリックリンクでない/想定外パス）の場合は None。
    """
    root_dir = get_root_dir()
    latest_path = root_dir / "latest"
    if not latest_path.exists() or not latest_path.is_symlink():
        return None

    try:
        target = latest_path.resolve()
    except OSError:
        return None

    # .../versions/vX.Y.Z を想定
    if target.parent.name != "versions":
        return None
    if not target.name.startswith("v"):
        return None
    return target.name


def get_version_dirs(specified_versions: list[str] | None = None) -> list[Path]:
    """バージョンディレクトリのリストを取得

    Args:
        specified_versions: 指定されたバージョン名のリスト。Noneの場合は全バージョン。

    Returns:
        バージョンディレクトリのPathリスト
    """
    root_dir = get_root_dir()
    versions_dir = root_dir / "versions"

    if not versions_dir.exists():
        print(f"Error: versions directory not found at {versions_dir}", file=sys.stderr)
        sys.exit(1)

    if specified_versions:
        # 指定されたバージョンのみ
        dirs = []
        for version in specified_versions:
            version_dir = versions_dir / version
            if not version_dir.exists():
                print(f"Warning: version directory not found: {version_dir}", file=sys.stderr)
            else:
                dirs.append(version_dir)
        return dirs
    else:
        # 全バージョン（v で始まるディレクトリ）
        return sorted([d for d in versions_dir.iterdir() if d.is_dir() and d.name.startswith("v")])


def read_backend_version(version_dir: Path) -> str | None:
    """backend/pyproject.toml からバージョンを読み込む

    Args:
        version_dir: バージョンディレクトリのPath

    Returns:
        バージョン文字列。読み込み失敗時はNone。
    """
    pyproject_file = version_dir / "backend" / "pyproject.toml"

    if not pyproject_file.exists():
        print(f"  Warning: pyproject.toml not found at {pyproject_file}", file=sys.stderr)
        return None

    content = pyproject_file.read_text()

    # version = "..." の行からバージョンを抽出
    match = re.search(r'^version\s*=\s*"([^"]*)"', content, flags=re.MULTILINE)
    if not match:
        print(f"  Warning: version not found in {pyproject_file}", file=sys.stderr)
        return None

    return match.group(1)


def update_frontend_html(version_dir: Path, version: str) -> bool:
    """frontend/index.html のバージョン表記を更新

    Args:
        version_dir: バージョンディレクトリのPath
        version: 更新するバージョン文字列

    Returns:
        更新があった場合True
    """
    html_file = version_dir / "frontend" / "index.html"

    if not html_file.exists():
        print(f"  Warning: index.html not found at {html_file}", file=sys.stderr)
        return False

    try:
        content = html_file.read_text()
        updated = False

        # パターン1: <span class="font-medium">バージョン:</span> v0.2.4
        pattern1 = r'(<span class="font-medium">バージョン:</span>\s*v)[\d.]+'
        replacement1 = rf"\g<1>{version}"
        new_content = re.sub(pattern1, replacement1, content)
        if new_content != content:
            content = new_content
            updated = True

        # パターン2: <p><span class="font-medium">バージョン:</span> v0.2.4</p>
        pattern2 = r'(<p><span class="font-medium">バージョン:</span>\s*v)[\d.]+(</p>)'
        replacement2 = rf"\g<1>{version}\g<2>"
        new_content = re.sub(pattern2, replacement2, content)
        if new_content != content:
            content = new_content
            updated = True

        if updated:
            html_file.write_text(content)
            print(f"  Updated {html_file.relative_to(get_root_dir())} to v{version}")
            return True
        else:
            print(f"  {html_file.relative_to(get_root_dir())} already has v{version}")
            return False

    except Exception as e:
        print(f"  Error updating index.html: {e}", file=sys.stderr)
        return False


def sync_version(version_dir: Path) -> bool:
    """指定バージョンディレクトリのバージョンを同期

    Args:
        version_dir: バージョンディレクトリのPath

    Returns:
        成功した場合True
    """
    print(f"Processing {version_dir.name}...")

    version = read_backend_version(version_dir)
    if not version:
        print(f"  Skipped: could not read version")
        return False

    print(f"  Backend version: {version}")
    update_frontend_html(version_dir, version)
    return True


def generate_versions_array(version_dirs: list[Path]) -> str:
    """VERSIONS配列のJavaScriptコードを生成

    Args:
        version_dirs: バージョンディレクトリのリスト

    Returns:
        VERSIONS配列のJavaScriptコード
    """
    # latest シンボリックリンクがある場合はそれを「最新」とする
    # （セマンティック的に最大のバージョンを最新扱いすると、実際のルーティングとズレるため）
    latest_name = get_latest_version_name()
    by_name = {d.name: d for d in version_dirs}

    remaining = sorted([d for d in version_dirs if d.name != latest_name], key=lambda d: d.name, reverse=True)
    sorted_dirs = [by_name[latest_name]] + remaining if latest_name in by_name else remaining

    entries = []
    for i, version_dir in enumerate(sorted_dirs):
        version_name = version_dir.name
        is_latest = i == 0  # 並び順の先頭（latest）を true
        entry = f"      {{ value: '{version_name}', label: '{version_name}', isLatest: {str(is_latest).lower()} }}"
        entries.append(entry)

    return "const VERSIONS = [\n" + ",\n".join(entries) + "\n    ];"


def update_versions_array(version_dir: Path, versions_array_code: str) -> bool:
    """frontend/index.html の VERSIONS配列を更新

    Args:
        version_dir: バージョンディレクトリのPath
        versions_array_code: 新しいVERSIONS配列のコード

    Returns:
        更新があった場合True
    """
    html_file = version_dir / "frontend" / "index.html"

    if not html_file.exists():
        return False

    try:
        content = html_file.read_text()

        # VERSIONS配列を検索（複数行にまたがる）
        # パターン: const VERSIONS = [ ... ];
        pattern = r'const VERSIONS = \[\s*\n(?:.*\n)*?\s*\];'

        if not re.search(pattern, content):
            # VERSIONS配列が見つからない場合はスキップ
            return False

        new_content = re.sub(pattern, versions_array_code, content)

        if new_content != content:
            html_file.write_text(new_content)
            print(f"  Updated VERSIONS array in {html_file.relative_to(get_root_dir())}")
            return True
        else:
            print(f"  VERSIONS array already up-to-date in {html_file.relative_to(get_root_dir())}")
            return False

    except Exception as e:
        print(f"  Error updating VERSIONS array: {e}", file=sys.stderr)
        return False


def sync_versions_arrays(version_dirs: list[Path]) -> int:
    """全フロントエンドのVERSIONS配列を更新

    Args:
        version_dirs: バージョンディレクトリのリスト

    Returns:
        更新されたファイル数
    """
    print("Updating VERSIONS arrays in all frontends...")

    versions_array_code = generate_versions_array(version_dirs)
    print(f"  Generated VERSIONS array with {len(version_dirs)} version(s)")

    updated_count = 0
    for version_dir in version_dirs:
        if update_versions_array(version_dir, versions_array_code):
            updated_count += 1

    return updated_count


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="フロントエンドのバージョンをバックエンドと同期するスクリプト",
        epilog="例: python3 scripts/sync_version.py v0.2.5 v0.1.1"
    )
    parser.add_argument(
        "versions",
        nargs="*",
        help="同期するバージョン名（例: v0.2.5）。省略時は全バージョン。"
    )
    parser.add_argument(
        "--no-versions-array",
        action="store_true",
        help="VERSIONS配列の更新をスキップする"
    )
    args = parser.parse_args()

    # 特定バージョンが指定された場合はVERSIONS配列更新はスキップ
    sync_all = not args.versions
    update_versions_array_flag = sync_all and not args.no_versions_array

    version_dirs = get_version_dirs(args.versions if args.versions else None)

    if not version_dirs:
        print("No version directories found.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(version_dirs)} version(s) to sync:")
    for d in version_dirs:
        print(f"  - {d.name}")
    print()

    # 各バージョンのバージョン番号を同期
    success_count = 0
    for version_dir in version_dirs:
        if sync_version(version_dir):
            success_count += 1
        print()

    print(f"Version sync completed! ({success_count}/{len(version_dirs)} succeeded)")

    # VERSIONS配列の更新（引数なしで実行した場合のみ）
    if update_versions_array_flag:
        print()
        # 全バージョンディレクトリを取得（VERSIONS配列には全バージョンを含める）
        all_version_dirs = get_version_dirs(None)
        updated_count = sync_versions_arrays(all_version_dirs)
        print(f"VERSIONS array update completed! ({updated_count} file(s) updated)")


if __name__ == "__main__":
    main()
