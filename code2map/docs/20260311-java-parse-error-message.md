# Issue #9 修正計画: Javaパーサーの改善

> **対応完了**: 本計画に基づく修正は [PR #11](https://github.com/elvezjp/code2map/pull/11) にて完了しました。

## 概要

Java 8+構文を含むファイルのパースが失敗した際、エラーメッセージが空になり、エラーの原因・発生箇所が呼び出し元に伝わらない問題を修正する。

本修正は Issue #9 の段階的対応の第1フェーズとして、**エラーメッセージの改善**のみを行う。パーサーライブラリの置き換え（tree-sitter 等）は第2フェーズとして別途検討する。

## 対応方針

1. **第1フェーズ**: エラーメッセージの改善 — パース失敗時に原因と発生箇所を正しく伝える（v0.1.3）
2. **第2フェーズ（要検討）**: パーサーライブラリの置き換え — Java 8+構文を根本的にサポートする（v0.2.0）

## 原因分析

### エラーメッセージが空になる原因

`javalang.parser.JavaSyntaxError` は `str()` で空文字を返すが、属性には有用な情報が格納されている。

```python
# 現在の実装（java_parser.py L80）
warnings.append(f"Java parse error: {exc}")
# → "Java parse error: "（空文字）
```

| 属性 | 値の例 | 現在使用 |
|---|---|---|
| `str(exc)` | `""` （空） | ○（だが空） |
| `exc.description` | `"Expected '.'"` | × |
| `exc.at` | `Keyword "new" line N, position M` | × |

### 呼び出し元への影響

ライブラリとして利用する場合（例: FastAPIバックエンド）、以下のフローで問題が発生する：

```
code_parser.parse(input_path)
    → ([], ["Java parse error: "])  # symbols=空, warnings=中身なしメッセージ
        → if not symbols: return success=True  # パースエラーが正常扱いされる
```

1. `warnings` のメッセージが空のため、呼び出し元がエラー内容を把握できない
2. 呼び出し元が `symbols` の空チェックのみで分岐している場合、パースエラーが「シンボル0件（正常）」として扱われる

## 修正対象

### 1. ソースコード修正（1ファイル）

| ファイル | 修正内容 |
|---------|---------|
| `code2map/parsers/java_parser.py` | `JavaSyntaxError` のエラーメッセージ構築を改善 |

**修正イメージ**:
```python
# 修正前（L79-80）
except (javalang.parser.JavaSyntaxError, IndexError) as exc:
    warnings.append(f"Java parse error: {exc}")

# 修正後
except (javalang.parser.JavaSyntaxError, IndexError) as exc:
    if hasattr(exc, 'description') and hasattr(exc, 'at'):
        warnings.append(f"Java parse error: {exc.description} (at {exc.at})")
    else:
        warnings.append(f"Java parse error: {exc}")
```

**出力の変化**:
- 修正前: `"Java parse error: "`
- 修正後: `"Java parse error: Expected '.' (at Keyword "new" line N, position M)"`

### 2. 変更不要な箇所

| 箇所 | 理由 |
|------|------|
| `cli.py` | `logger.warning(warning)` で warnings をそのまま出力しており、メッセージが改善されれば対応不要 |
| `BaseParser` / `PythonParser` | Java 固有の問題であり影響なし |
| 呼び出し元（ai-reviewer 等） | code2map 側で正しいメッセージを返せば、既存の `warnings` 参照ロジックで動作する。ただし、呼び出し元の `symbols` 空チェック分岐は呼び出し元側の課題として別途対応が必要 |

## テスト計画

### 新規テスト

`tests/` に以下を追加:

| テストケース | 検証内容 |
|------------|---------|
| `test_java_parse_error_message_not_empty` | パースエラー時の warnings メッセージが空でないこと |
| `test_java_parse_error_contains_location` | warnings メッセージにエラー発生箇所の情報（行番号等）が含まれること |
| `test_java_parse_error_contains_description` | warnings メッセージにエラーの説明が含まれること |

### テスト用フィクスチャ

`javalang` でパースエラーが発生する最小限のJavaコードを用意する:

```java
// tests/fixtures/java8_syntax.java
public class Java8Syntax {
    enum Status {
        A("a");
        private final String key;
        Status(String key) { this.key = key; }
        public String[] getKeys() {
            return java.util.Arrays.stream(Status.values())
                .map(Status::name).toArray(String[]::new);
        }
    }
}
```

### 既存テストへの影響

既存テストは正常パース時のケースのみのため、影響なし。

### 手動確認

- `uv run code2map build <Java8+構文を含むファイル>` 実行時に、エラーの原因と箇所が表示されること
- ライブラリとして `JavaParser().parse()` を呼び出した際、`warnings` に有用なメッセージが含まれること

## 実装手順

本修正はパーサーの動作変更を含むため、バージョンを v0.1.2 → v0.1.3 に上げる。

### Task 1: 現行バージョン（v0.1.2）のスナップショット保存

修正前のコードを `versions/v0.1.2/` に保存する（既存の `versions/v0.1.1/` と同様の構成）。

1. `versions/v0.1.2/` ディレクトリを作成
2. 以下をコピー:
   - `code2map/` （パッケージ全体）
   - `tests/`
   - `pyproject.toml`
   - `spec.md`
   - `uv.lock`

### Task 2: テスト用フィクスチャの作成

1. `javalang` でパースエラーが発生する最小限のJavaコード `tests/fixtures/java8_syntax.java` を作成

### Task 3: エラーメッセージの修正

1. `code2map/parsers/java_parser.py` の `JavaSyntaxError` キャッチ部分を修正
   - `exc.description` と `exc.at` 属性を使用してメッセージを構築

### Task 4: テストの追加と実行

1. パースエラー時のメッセージに関するテストケースを追加
2. 新規テスト PASS を確認
3. 既存テスト PASS を確認（デグレなし）

### Task 5: バージョン更新

1. `pyproject.toml` の version を `"0.1.3"` に更新
2. `code2map/__init__.py` の `__version__` を `"0.1.3"` に更新
3. `CHANGELOG.md` に v0.1.3 のエントリを追加

### Task 6: PR 作成・レビュー

1. ブランチを作成（命名規則に従う）
2. 変更をコミット
3. PR を作成しレビュー依頼

## 完了チェックリスト

- [x] `versions/v0.1.2/` に現行コードのスナップショットが保存されている
- [x] `tests/fixtures/java8_syntax.java` が作成されている
- [x] `java_parser.py` のエラーメッセージが `exc.description` と `exc.at` を使用している
- [x] パースエラー時の warnings メッセージが空でないこと（テスト PASS）
- [x] パースエラー時の warnings メッセージにエラー箇所の情報が含まれること（テスト PASS）
- [x] 既存テストが全て PASS していること（デグレなし）
- [x] `pyproject.toml` の version が `"0.1.3"` に更新されている
- [x] `code2map/__init__.py` の `__version__` が `"0.1.3"` に更新されている
- [x] `CHANGELOG.md` に v0.1.3 のエントリが追加されている
- [x] PR が作成されレビュー依頼されている

---

# 第2フェーズ（要検討）: tree-sitter への置き換え

## 概要

`javalang` を `tree-sitter`（`tree-sitter` + `tree-sitter-java`）に置き換え、Java 8+構文のパースを根本的にサポートする。第1フェーズのエラーメッセージ改善はあくまで暫定対応であり、本フェーズで構文サポートの根本解決を目指す。

バージョンは v0.1.3 → v0.2.0 に上げる。

## 背景

`javalang` の問題点：

- Java 8+構文（ラムダ式、メソッドリファレンス `Type[]::new` 等）でパースエラーが発生する
- 長期間メンテナンスされていない（最終リリース2018年頃）
- エラー耐性が低い（1箇所の未対応構文でファイル全体のパースが失敗する）
- 今後の新構文（record、sealed class、switch式等）にも対応できない

## tree-sitter 採用の評価

### メリット

| 項目 | 説明 |
|------|------|
| 構文サポート | Java 17+を含むほぼ全ての構文を正しくパース可能 |
| エラー耐性 | 部分的に壊れたコードでもパース可能な部分は正常に返す |
| パフォーマンス | C実装ベースのため高速 |
| 言語拡張 | C, TypeScript等も同じエコシステムで対応可能 |
| メンテナンス | tree-sitter-java は活発にメンテされている |

### 考慮事項

| 項目 | 説明 |
|------|------|
| AST形式の違い | tree-sitter は具象構文木（CST）寄りで、`javalang` の抽象構文木（AST）より冗長 |
| 書き直し範囲 | `JavaParser` クラスの `parse()` メソッドを全面的に書き直す必要がある |
| メソッド呼び出し抽出 | `javalang` の `method.filter(MethodInvocation)` 相当の処理を手動走査またはクエリで実装する必要がある |
| Javadoc抽出 | tree-sitter はコメントもノードとして返すため、抽出方法を変更する必要がある |
| `BaseParser` インターフェース | `parse()` の戻り値 `Tuple[List[Symbol], List[str]]` は変更不要（内部実装のみ変更） |

### 依存関係の変更

```diff
- javalang>=0.13.0
+ tree-sitter>=0.21.0
+ tree-sitter-java>=0.21.0
```

## 修正対象

### 1. ソースコード修正

| ファイル | 修正内容 |
|---------|---------|
| `code2map/parsers/java_parser.py` | `javalang` を `tree-sitter` に全面置き換え |
| `pyproject.toml` | 依存関係の変更（`javalang` → `tree-sitter` + `tree-sitter-java`） |

### 2. 変更不要な箇所

| 箇所 | 理由 |
|------|------|
| `BaseParser` | インターフェース変更なし |
| `PythonParser` | Python側は `ast` モジュールを使用しており影響なし |
| `cli.py` | パーサーの内部実装に依存しない |
| 呼び出し元（ai-reviewer 等） | `parse()` の戻り値型が同一のため影響なし |
| `generators/` | `Symbol` リストを受け取るため、パーサー実装に依存しない |

### 3. 実装時に確認が必要な項目

`javalang` ベースの現行実装から tree-sitter に移行する際、以下の機能が同等に動作することを確認する：

| 機能 | 現行実装（javalang） | tree-sitter での実装方針 |
|------|---------------------|------------------------|
| クラス抽出 | `tree.types` の走査 | `class_declaration` ノードの走査 |
| メソッド抽出 | `node.methods` の走査 | `method_declaration` ノードの走査 |
| コンストラクタ抽出 | `node.constructors` の走査 | `constructor_declaration` ノードの走査 |
| ネストクラス | `node.body` の再帰走査 | 子ノードの再帰走査 |
| メソッド呼び出し抽出 | `method.filter(MethodInvocation)` | `method_invocation` ノードの走査 |
| Javadoc抽出 | `_extract_javadoc()` で行ベース走査 | `comment` / `block_comment` ノードの走査 |
| import文抽出 | `tree.imports` | `import_declaration` ノードの走査 |
| 行番号取得 | `node.position.line` | `node.start_point[0] + 1` |
| ブロック終了行 | `_find_brace_block_end()` | `node.end_point[0] + 1` |
| パラメータ型取得 | `param.type.name` | `formal_parameter` → `type_identifier` ノードの走査 |

## 実装手順

### Task 1: 現行バージョン（v0.1.3）のスナップショット保存

1. `versions/v0.1.3/` ディレクトリを作成
2. 以下をコピー:
   - `code2map/` （パッケージ全体）
   - `tests/`
   - `pyproject.toml`
   - `spec.md`
   - `uv.lock`

### Task 2: 依存関係の変更

1. `pyproject.toml` の `dependencies` から `javalang` を削除し、`tree-sitter` + `tree-sitter-java` を追加
2. `uv sync` で依存関係を更新

### Task 3: JavaParser の書き直し

1. `java_parser.py` を tree-sitter ベースに全面書き直し
2. 現行の `_find_brace_block_end()` は不要になるため削除
3. `_extract_javadoc()` を tree-sitter のコメントノード走査に変更
4. `BaseParser` の `parse()` インターフェースは維持する

### Task 4: テストの実行と追加

1. 既存テスト PASS を確認（デグレなし）
2. 第1フェーズで追加したパースエラーテストの動作確認（tree-sitter ではパースエラーにならないため、テストの期待値を調整）
3. Java 8+構文を含むファイルが正常にパースされることのテストを追加

### Task 5: バージョン更新

1. `pyproject.toml` の version を `"0.2.0"` に更新
2. `code2map/__init__.py` の `__version__` を `"0.2.0"` に更新
3. `CHANGELOG.md` に v0.2.0 のエントリを追加

### Task 6: 仕様書の更新

1. `spec.md` を tree-sitter ベースの実装に合わせて更新
   - 依存ライブラリの記述（`javalang` → `tree-sitter` + `tree-sitter-java`）
   - パーサーの動作説明を実装と一致するよう修正

### Task 7: サンプル出力の更新

1. `docs/examples/java/output/` を `docs/examples/java/output_v0.1.2/` にリネームして保存
2. v0.2.0 でサンプルJavaファイルを再実行し、`docs/examples/java/output/` に出力を生成

### Task 8: 公開用ドキュメントの更新

1. `README.md` のバージョン・依存関係・機能説明を v0.2.0 に合わせて更新
2. `SECURITY.md` 等、その他の公開ドキュメントを確認し必要に応じて更新

### Task 9: PR 作成・レビュー

1. ブランチを作成（命名規則に従う）
2. 変更をコミット
3. PR を作成しレビュー依頼

## 完了チェックリスト

- [x] `versions/v0.1.3/` に v0.1.3 コードのスナップショットが保存されている
- [x] `pyproject.toml` の依存関係が `tree-sitter` + `tree-sitter-java` に変更されている
- [x] `java_parser.py` が tree-sitter ベースに書き直されている
- [x] `javalang` への依存が完全に除去されている
- [x] 既存テストが全て PASS していること（デグレなし）
- [x] Java 8+構文を含むファイルが正常にパースされること（テスト PASS）
- [x] メソッド呼び出し抽出（`calls`）が動作すること
- [x] Javadoc抽出（`role`）が動作すること
- [x] ネストクラスが正しく抽出されること
- [x] `pyproject.toml` の version が `"0.2.0"` に更新されている
- [x] `code2map/__init__.py` の `__version__` が `"0.2.0"` に更新されている
- [x] `CHANGELOG.md` に v0.2.0 のエントリが追加されている
- [x] `spec.md` が tree-sitter ベースの実装と一致している
- [x] `docs/examples/v0.1.2/` に旧サンプル出力（Java・Python）が保存されている
- [x] `docs/examples/v0.2.0/` に v0.2.0 のサンプル出力（Java・Python）が生成されている
- [x] `README.md` が v0.2.0 の内容に更新されている
- [x] PR が作成されレビュー依頼されている
