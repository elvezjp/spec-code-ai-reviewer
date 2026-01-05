#!/usr/bin/env python3
"""
テキストファイルに行番号を付けるシンプルなスクリプト

使い方:
    python add_line_numbers.py                    # inputs/ → outputs/ (デフォルト)
    python add_line_numbers.py input_dir output_dir  # カスタムディレクトリ指定
"""

import os
import sys
from datetime import datetime
from pathlib import Path


def add_line_numbers_to_content(content: str) -> tuple[str, int]:
    """
    文字列に行番号を付与して返す

    Args:
        content: 行番号を付与する元のテキスト

    Returns:
        tuple: (行番号付きテキスト, 行数)
    """
    lines = content.splitlines()
    line_count = len(lines)

    numbered_lines = []
    for i, line in enumerate(lines, 1):
        numbered_lines.append(f"{i:4d}: {line}")

    return "\n".join(numbered_lines), line_count


def add_line_numbers_to_file(input_path: Path, output_path: Path) -> None:
    """
    テキストファイルに行番号を付けて出力する

    Args:
        input_path: 入力ファイルのパス
        output_path: 出力ファイルのパス
    """
    # 出力ディレクトリが存在しない場合は作成
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ファイルを読み込んで行番号を付ける
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    with open(output_path, 'w', encoding='utf-8') as f:
        for i, line in enumerate(lines, 1):
            f.write(f"{i:4d}: {line}")


def generate_directory_tree(directory: Path, prefix: str = "", max_depth: int = 5, current_depth: int = 0) -> str:
    """
    ディレクトリ構造をツリー形式の文字列として生成する

    Args:
        directory: 対象ディレクトリのパス
        prefix: ツリー表示用のプレフィックス
        max_depth: 最大探索深度
        current_depth: 現在の深度

    Returns:
        ツリー形式の文字列
    """
    if current_depth >= max_depth:
        return ""

    tree_lines = []

    try:
        # ディレクトリとファイルを取得してソート
        entries = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name))

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1

            # ツリー記号を決定
            if is_last:
                current_prefix = "└── "
                next_prefix = "    "
            else:
                current_prefix = "├── "
                next_prefix = "│   "

            # エントリ名を追加
            if entry.is_dir():
                tree_lines.append(f"{prefix}{current_prefix}{entry.name}/")
                # 再帰的にサブディレクトリを処理
                subtree = generate_directory_tree(entry, prefix + next_prefix, max_depth, current_depth + 1)
                if subtree:
                    tree_lines.append(subtree)
            else:
                # すべてのファイルを表示
                tree_lines.append(f"{prefix}{current_prefix}{entry.name}")
    except PermissionError:
        pass

    return "\n".join(tree_lines)


def generate_readme(output_dir: Path, input_dir: Path) -> None:
    """
    行番号付きファイルディレクトリ用のREADME.mdを生成する

    Args:
        output_dir: 出力ディレクトリのパス
        input_dir: 入力ディレクトリのパス（生成元の参照用）
    """
    readme_path = output_dir / "README.md"

    # 入力ディレクトリの相対パスを取得（説明用）
    try:
        input_relative = Path(input_dir).resolve().relative_to(Path.cwd())
    except ValueError:
        input_relative = Path(input_dir)

    # 出力ディレクトリの相対パスを取得（ディレクトリ構造表示用）
    try:
        output_relative = Path(output_dir).resolve().relative_to(Path.cwd())
        output_dirname = output_relative.name
    except ValueError:
        output_dirname = Path(output_dir).name

    # ディレクトリ構造を生成
    directory_tree = generate_directory_tree(output_dir)

    # 現在時刻を取得
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    readme_content = f"""# 行番号付きファイルディレクトリ

## 概要

このディレクトリには、**行番号が付与されたテキストファイル**が含まれています。

## 行番号の形式

各ファイル内の各行は、以下の形式で行番号が付与されています：

```
   1: package com.example;
   2:
   3: import java.util.List;
   4: public class Example {{
   5:     public void method() {{
   6:         // コード
   7:     }}
   8: }}
```

### 行番号フォーマットの特徴

- **形式**: `行番号: `（行番号の後にコロンとスペース）
- **パディング**: 行番号は右揃えで表示され、最大桁数に合わせてスペースでパディングされます
- **例**:
  - 1桁の行番号: `   1: `
  - 2桁の行番号: `  10: `
  - 3桁の行番号: ` 100: `
  - 4桁の行番号: `1000: `

## AIへの重要な指示

### 1. 行番号の認識

このディレクトリ内のファイルを処理する際は、**各行の先頭にある行番号を認識し、内容の一部として扱ってください**。

### 2. 行番号参照時の形式

ファイル内の特定の行を参照する際は、**ファイル内に表示されている行番号をそのまま使用してください**。

**正しい参照例:**
- 「12行目の内容を確認してください」
- 「45行目から50行目までの処理を修正してください」
- 「`12: import java.util.List;` の行を...」

**誤った参照例:**
- 「実際のファイルの12行目」（行番号を無視した参照）

### 3. ファイル解析時の注意点

- 行番号は**ファイル内容の一部**として扱ってください
- 行番号を削除したり、無視したりしないでください
- 構造解析や構文解析を行う際も、行番号を含めた状態で処理してください

### 4. ファイル編集時の注意点

このディレクトリ内のファイルを編集する場合は：
- 行番号の形式を維持してください（`行番号: `の形式）
- 行番号の連続性を保ってください
- 行を追加・削除する場合は、行番号を適切に再計算してください

## ディレクトリ構造

このディレクトリは、元のファイルのディレクトリ構造を保持しています。

```
{output_dirname}/
{directory_tree}
```

## 生成元との関係

このディレクトリ内のファイルは、元のファイル（`{input_relative}`ディレクトリ）に行番号を付与して生成されたものです。

- **元のファイル**: 行番号なしの通常のファイル
- **このディレクトリ**: 行番号が付与されたファイル

## 使用例

### ファイル参照の例

```
  12: import java.util.List;
  13:
  14: public class Example {{
  15:     public void method() {{
  16:         List<String> list = new ArrayList<>();
  17:     }}
  18: }}
```

上記のファイルを参照する際は：
- 「16行目の`List<String> list = new ArrayList<>();`を...」と表現してください
- 実際のファイル内では「`  16: List<String> list = new ArrayList<>();`」と表示されています

## まとめ

- 行番号はファイル内容の一部として扱う
- 行番号参照時は、ファイル内に表示されている行番号を使用する
- ファイル編集時も行番号の形式を維持する
- 行番号を無視したり削除したりしない

---

**注意**: このディレクトリ内のファイルは自動生成されたものです。元のファイルを変更する場合は、元のディレクトリ（`{input_relative}`など）で編集し、再度行番号を付与してください。

**生成日時**: {current_time} - このREADME.mdは `add_line_numbers.py` スクリプトによって自動生成されました。
"""

    readme_path.write_text(readme_content, encoding='utf-8')
    print(f"✓ README.md を生成しました: {readme_path}")


def process_directory(input_dir: str, output_dir: str) -> None:
    """
    ディレクトリ内の全テキストファイルを処理する

    Args:
        input_dir: 入力ディレクトリ
        output_dir: 出力ディレクトリ
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.exists():
        print(f"エラー: 入力ディレクトリが見つかりません: {input_dir}")
        sys.exit(1)

    # 全ファイルを再帰的に探す（ディレクトリは除外）
    all_files = [f for f in input_path.glob("**/*") if f.is_file()]

    if not all_files:
        print(f"警告: {input_dir} 内にファイルが見つかりませんでした")
        return

    print(f"処理中: {len(all_files)} 個のファイル")
    print(f"入力: {input_dir}")
    print(f"出力: {output_dir}")
    print("-" * 60)

    processed_count = 0
    skipped_count = 0

    # 各ファイルを処理
    for file in all_files:
        # 相対パスを取得してディレクトリ構造を保持
        relative_path = file.relative_to(input_path)
        output_file = output_path / relative_path

        try:
            add_line_numbers_to_file(file, output_file)
            print(f"✓ {relative_path}")
            processed_count += 1
        except UnicodeDecodeError:
            print(f"✗ {relative_path}: UTF-8として読み込めないためスキップ")
            skipped_count += 1
        except Exception as e:
            print(f"✗ {relative_path}: {e}")
            skipped_count += 1

    print("-" * 60)
    print(f"完了: {processed_count} 個のファイルを処理しました")
    if skipped_count > 0:
        print(f"スキップ: {skipped_count} 個のファイル")

    # README.mdを生成
    try:
        generate_readme(output_path, input_path)
    except Exception as e:
        print(f"警告: README.mdの生成に失敗しました: {e}")


def main():
    """メイン関数"""
    # コマンドライン引数の処理
    if len(sys.argv) == 1:
        # デフォルト: inputs/ → outputs/
        input_dir = "inputs"
        output_dir = "outputs"
    elif len(sys.argv) == 3:
        # カスタムディレクトリ指定
        input_dir = sys.argv[1]
        output_dir = sys.argv[2]
    else:
        print(__doc__)
        print("\nエラー: 引数の数が正しくありません")
        print("使い方:")
        print("  python add_line_numbers.py")
        print("  python add_line_numbers.py <入力ディレクトリ> <出力ディレクトリ>")
        sys.exit(1)

    process_directory(input_dir, output_dir)


if __name__ == "__main__":
    main()
