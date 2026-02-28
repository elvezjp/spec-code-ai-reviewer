# Issue #5 修正計画: ファイル名の不正文字サニタイズ

## 概要

Windows環境で `git clone` に失敗する問題の修正。Javaコンストラクタのシンボル名 `<init>` がファイル名にそのまま使用されており、`<` `>` はWindowsのファイルシステムで使用不可の文字であるためエラーが発生する。

## 原因分析

### 出力経路

1. `code2map/parsers/java_parser.py` L153: コンストラクタのシンボル名を `name="<init>"` として設定
2. `code2map/generators/parts_generator.py` L26: `_build_filename()` で `f"{parent}_{symbol.name}{ext}"` → `User_<init>.java`
3. `code2map/generators/parts_generator.py` L58: `symbol.part_file = f"parts/{filename}"` が INDEX.md / MAP.json に伝播

### `<init>` の由来

JVM仕様（§2.9）の命名規則に由来。バイトコードではコンストラクタは `<init>`、静的初期化ブロックは `<clinit>` として表現される。本プロジェクトではソースコード解析（javalangパーサー）を使っており、バイトコードから直接取得しているわけではなく、JVMの命名規則を意識して独自に設定している。

## 修正方針

### サニタイズ方式: `<>` を除去する

| 方式 | 変換例 | 採否 | 理由 |
|------|--------|------|------|
| `<>` を除去 | `User_init.java` | **採用** | 最もシンプルで可読性が高い |
| `<>` → `_` | `User__init_.java` | 不採用 | アンダースコアが連続して読みにくい |
| `<>` → `[]` | `User_[init].java` | 不採用 | `[]` もシェルでグロブ文字として解釈されうる |

### サニタイズ対象文字

Windowsで使用不可の文字を網羅的に除去する: `< > : " / \ | ? *`

## 修正対象

### 1. ソースコード修正（1ファイル）

| ファイル | 修正内容 |
|---------|---------|
| `code2map/generators/parts_generator.py` | `_build_filename()` にサニタイズ処理を追加 |

**修正イメージ**:
```python
import re

_UNSAFE_CHARS = re.compile(r'[<>:"/\\|?*]')

def _build_filename(symbol: Symbol, ext: str, existing: Dict[str, int]) -> str:
    if symbol.kind == "class":
        base = f"{symbol.name}.class{ext}"
    elif symbol.kind == "method":
        parent = symbol.parent or "Anonymous"
        base = f"{parent}_{symbol.name}{ext}"
    else:
        base = f"{symbol.name}{ext}"

    base = _UNSAFE_CHARS.sub("", base)  # サニタイズ追加

    if base in existing:
        seed = symbol.signature or f"{symbol.display_name()}_{symbol.start_line}"
        stem = base[: -len(ext)]
        base = f"{stem}__{_short_hash(seed)}{ext}"
    existing[base] = existing.get(base, 0) + 1
    return base
```

### ファイル名衝突について

`_build_filename()` には既存の重複検出機構（L30-33）があり、同名ファイルが生成された場合はハッシュサフィックスが自動付与される。例えば、同じクラスにコンストラクタ `<init>` とメソッド `init()` が存在する場合:

- コンストラクタ → サニタイズ後 `User_init.java`
- メソッド `init()` → `User_init.java`（衝突）
- → 後から処理された方にハッシュ付与: `User_init__a1b2.java`

**既存の重複検出機構がそのまま機能するため、衝突への追加対応は不要。**

### 2. サンプル出力ファイルの更新

サニタイズ後のファイル名に合わせて、サンプル出力を再生成する。

#### docs/examples/java/output/（6ファイル）

| 対象 | 変更内容 |
|------|---------|
| `parts/User_<init>.java` | `parts/User_init.java` にリネーム |
| `parts/UserAlreadyExistsException_<init>.java` | `parts/UserAlreadyExistsException_init.java` にリネーム |
| `parts/UserNotFoundException_<init>.java` | `parts/UserNotFoundException_init.java` にリネーム |
| `INDEX.md`（3箇所） | `part_file` パスを更新 |
| `MAP.json`（3箇所） | `part_file` フィールドを更新 |

#### versions/v0.1.1/examples/java/output/（6ファイル）

上記と同じパターンの変更。ただし versions ディレクトリはアーカイブ目的のため、修正対象外とする（旧バージョンの出力をそのまま保持）。

### 3. 変更不要な箇所

| 箇所 | 理由 |
|------|------|
| `java_parser.py` の `name="<init>"` | シンボルの論理名であり、ファイル名ではない |
| `java_parser.py` の `qualname` (`User#<init>`) | 内部識別用の名前であり、ファイル名ではない |
| parts ファイル内の `symbol: User#<init>` | ファイル内容のコメントであり、ファイル名ではない |
| INDEX.md 内の `User#<init>` 表示名部分 | シンボル名の表示であり、ファイルパスではない |
| Python の `__init__` | `<>` を含まないため影響なし |

## テスト計画

### 新規テスト

`tests/test_generators.py` または `tests/test_edge_cases.py` に以下を追加:

| テストケース | 検証内容 |
|------------|---------|
| `test_build_filename_sanitizes_angle_brackets` | `<init>` → `init` に変換されること |
| `test_build_filename_collision_after_sanitize` | サニタイズ後に衝突した場合、ハッシュサフィックスが付与されること |
| `test_java_constructor_parts_filename` | Javaコンストラクタの parts ファイル名に `<>` が含まれないこと |

### 既存テストへの影響

既存テストは Python のみを対象としているため、影響なし。

### 手動確認

- Windows環境で `git clone` が成功すること
- 生成された parts ファイルが正しくリンクされること（INDEX.md のパスからアクセス可能）

## 実装手順

1. `parts_generator.py` の `_build_filename()` にサニタイズ処理を追加
2. テストケースを追加し、全テスト PASS を確認
3. `docs/examples/java/output/` のサンプル出力を再生成
4. PR 作成・レビュー
