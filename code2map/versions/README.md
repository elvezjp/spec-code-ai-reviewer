# versions/

各バージョンのソースコードのスナップショットを保存するディレクトリ。

リファクタリングや大きな変更を行う前の状態を `v{バージョン番号}/` として保持し、過去のバージョンとの比較や参照を可能にする。

> **注意**: v0.1.0 はスナップショット導入前のリリースのため、このディレクトリには含まれない。

## 構成

```
versions/
├── v0.1.1/          # pyproject.toml の version = "0.1.1" 時点のスナップショット
│   ├── code2map/
│   ├── tests/
│   ├── main.py
│   ├── pyproject.toml
│   ├── spec.md
│   └── uv.lock
├── v0.1.2/          # pyproject.toml の version = "0.1.2" 時点のスナップショット
│   ├── code2map/
│   ├── tests/
│   ├── pyproject.toml
│   ├── spec.md
│   └── uv.lock
├── v0.1.3/          # pyproject.toml の version = "0.1.3" 時点のスナップショット
│   ├── code2map/
│   ├── tests/
│   │   └── fixtures/java8_syntax.java  # v0.1.3 で追加
│   ├── pyproject.toml
│   ├── spec.md
│   └── uv.lock
└── README.md
```

## バージョン比較表

| 項目 | v0.1.0 | v0.1.1 | v0.1.2 | v0.1.3 | v0.2.0（現行） |
|------|:------:|:------:|:------:|:------:|:--------------:|
| リリース日 | 2026-01-27 | 2026-02-06 | 2026-02-25 | 2026-03-12 | 2026-03-12 |
| Javaパーサー | javalang | javalang | javalang | javalang | **tree-sitter** |
| Java 8+構文対応 | ✗ | ✗ | ✗ | ✗ | ✓ |
| パースエラーメッセージ | 空 | 空 | 空 | **詳細あり** | 詳細あり |
| シンボルID（`--id-prefix`） | ✗ | ✓ | ✓ | ✓ | ✓ |
| ファイル名サニタイズ | ✗ | ✗ | ✓ | ✓ | ✓ |
| スナップショット | なし | `versions/v0.1.1/` | `versions/v0.1.2/` | `versions/v0.1.3/` | —（現行） |

## 各バージョンの変更概要

### v0.2.0（現行）— 2026-03-12

**JavaパーサーをTree-sitterに全面置き換え**

- `javalang` → `tree-sitter` + `tree-sitter-java` に移行
- Java 8+構文（ラムダ式、メソッドリファレンス `Type[]::new` 等）を正常パース
- 依存関係: `javalang>=0.13.0` を削除、`tree-sitter>=0.21.0` + `tree-sitter-java>=0.21.0` を追加

### v0.1.3 — 2026-03-12

**Javaパースエラーメッセージの改善**

- `JavaSyntaxError` の `description` / `at` 属性を使用し、エラー内容と発生箇所を出力
- 修正前: `"Java parse error: "`（空） → 修正後: `"Java parse error: Expected '.' (at ...)"`
- テストフィクスチャ `tests/fixtures/java8_syntax.java` を追加

### v0.1.2 — 2026-02-25

**ファイル名サニタイズの追加**

- parts/ のファイル名から Windows 不可文字（`< > : " / \ | ? *`）を除去
- Javaコンストラクタ `<init>` のファイル名: `User_<init>.java` → `User_init.java`
- Windows 環境での `git clone` 失敗を解消

### v0.1.1 — 2026-02-06

**シンボルID機能の追加**

- `--id-prefix` オプションでシンボルIDのプレフィックスを指定可能（デフォルト: `CD`）
- INDEX.md にシンボルID（`[CD1]` 形式）を追加
- MAP.json の先頭に `id` フィールドを追加
- parts/ ヘッダに `id: CD1` 行を追加

### v0.1.0 — 2026-01-27

**初回リリース**（スナップショットなし）

- `code2map build` コマンドを実装
- Python パーサー（`ast` モジュール）・Java パーサー（`javalang`）
- INDEX.md / parts/ / MAP.json の生成
- GitHub Actions による CI（Python 3.9〜3.12）
