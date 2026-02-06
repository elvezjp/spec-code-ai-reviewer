# code2map 実装計画 (Plan.md)

## 概要
code2map の実装を段階的に進める計画。主言語としてPythonを使用し、CLIツールとして開発。初期バージョンではJavaとPythonのソースコードを対象とする。
- MVPは**単一ファイル**のみを対象とし、ディレクトリ/複数ファイル解析は後続フェーズで対応する。

## 必要な技術・ライブラリ
- **言語**: Python 3.9+
- **CLI**: argparse (標準ライブラリ)
- **AST解析**:
  - Python: ast (標準ライブラリ)
  - Java: javalang (外部ライブラリ、pip install javalang)
- **ファイル操作**: os, pathlib (標準)
- **JSON出力**: json (標準)
- **ハッシュ**: hashlib (標準、SHA-256)
- **Markdown生成**: 文字列テンプレートで手動生成（外部ライブラリ不要）
- **テスト**: pytest, pytest-cov
- **型チェック**: mypy（開発時の品質管理）
- **リンター/フォーマッター**: ruff（lint + format を一括管理）

## ファイル構造
```
code2map/
├── main.py                 # エントリーポイント、CLI処理
├── parsers/
│   ├── __init__.py
│   ├── base_parser.py      # 共通パーサー基底クラス（抽象インターフェース）
│   ├── java_parser.py      # Java AST解析（javalang使用）
│   └── python_parser.py    # Python AST解析（ast使用）
├── generators/
│   ├── __init__.py
│   ├── index_generator.py  # INDEX.md 生成
│   ├── parts_generator.py  # parts/ ディレクトリ生成、ファイル分割
│   └── map_generator.py    # MAP.json 生成
├── models/
│   ├── __init__.py
│   ├── symbol.py           # Symbol クラス（クラス、メソッド等の統一表現）
│   └── metadata.py         # メタデータ構造
├── utils/
│   ├── __init__.py
│   ├── file_utils.py       # ファイル読み書き、行抽出
│   └── logger.py           # ログ設定
├── tests/
│   ├── __init__.py
│   ├── test_java_parser.py
│   ├── test_python_parser.py
│   ├── test_generators.py
│   ├── fixtures/            # テスト用サンプルコード
│   │   ├── sample.java
│   │   └── sample.py
│   └── test_e2e.py         # 統合テスト
├── pyproject.toml          # パッケージ設定・依存管理（PEP 621準拠）
├── .github/workflows/      # CI設定
│   └── tests.yml
├── README.md               # プロジェクト説明
├── Spec.md                 # 仕様書
└── Plan.md                 # 計画書
```

## 実装ステップ
### Phase 1: 基盤構築 (1-2週間)
**成果物**: CLI基本動作、プロジェクト構造確立

1. **プロジェクト初期化**
   - ディレクトリ構造作成（上記ファイル構造に従う）
   - `pyproject.toml` 作成（PEP 621準拠）:
     - `[project]`: name, version, dependencies（javalang）, requires-python >= 3.9
     - `[project.scripts]`: `code2map = "code2map.main:main"` （CLIエントリーポイント）
     - `[project.optional-dependencies]`: dev = ["pytest", "pytest-cov", "ruff", "mypy"]
   - `main.py` のスケルトン: argparse で CLI引数処理（build サブコマンド、--out, --lang, --verbose, --dry-run）
   - `.gitignore` 作成: `*.pyc`, `__pycache__`, `dist/`, `*.egg-info/`, `.mypy_cache/`, `.ruff_cache/` など
   - 開発環境セットアップ手順の確立:
     - `python -m venv .venv && source .venv/bin/activate`
     - `pip install -e ".[dev]"`

2. **共通基盤**
   - `models/symbol.py`: Symbol データクラス定義（name, type, start_line, end_line, dependencies, role, calls, side_effects 等）。型ヒント必須。
   - `models/metadata.py`: 出力メタデータ構造
   - `parsers/base_parser.py`: シンボル抽出の抽象基底クラス（ABCで定義）
   - `utils/file_utils.py`: ファイル読み書き（UTF-8）、指定行抽出、SHA-256チェックサム計算
   - `utils/lang_detect.py`: ファイル拡張子から言語を自動検出するロジック（Spec.md 言語自動検出仕様に準拠）
   - `utils/logger.py`: ログ設定（logging標準ライブラリ）
   - `tests/fixtures/`: テスト用サンプルコード配置

**チェックリスト**:
- [x] `code2map --help` でCLI表示（エントリーポイント経由）
- [x] `code2map build sample.py --dry-run` でエラーなく動作
- [ ] `mypy code2map/` が型エラーなしで通過 ※ mypy 未インストール（devツール未セットアップ）
- [ ] `ruff check code2map/` がlintエラーなしで通過 ※ ruff 未インストール（devツール未セットアップ）

### Phase 2: パーサー実装 (2-3週間)
**成果物**: Java/Python両言語のシンボル抽出完了

3. **Python パーサー** (`parsers/python_parser.py`)
   - ast モジュールでクラス/メソッド/関数抽出
   - 行番号取得（ast.Node の lineno、end_lineno利用）
   - docstring 抽出（role欄用: 最初の行を使用、なければ省略）
   - 依存関係推定:
     - import文の解析
     - メソッド/関数呼び出しの抽出（AST訪問のみ）
   - Side Effects 検出: Spec.md キーワードテーブルに基づくヒューリスティック
   - ネスト関数: 親関数のシンボルに含める（個別分割しない）
   - テスト: `tests/test_python_parser.py`

4. **Java パーサー** (`parsers/java_parser.py`)
   - javalang で AST解析
   - クラス/メソッド/フィールド抽出
   - Javadoc 抽出（role欄用: 最初の文を使用、なければ省略）
   - 行範囲と依存関係の取得:
     - import文
     - メソッド呼び出し
   - Side Effects 検出: Spec.md キーワードテーブルに基づくヒューリスティック
   - ネストクラス対応: `OuterClass_InnerClass` 形式の命名
   - オーバーロード対応: パラメータ型情報またはハッシュで一意化
   - テスト: `tests/test_java_parser.py`

**チェックリスト**:
- [x] `tests/fixtures/sample.py` パース成功 + シンボル3個以上抽出
- [x] `tests/fixtures/sample.java` パース成功 + シンボル2個抽出（class + method）
- [x] ネストクラス / ネスト関数のテストケース PASS
- [x] docstring/Javadoc なしのケースでエラーにならないこと（function_only.py テストで確認）
- [ ] オーバーロード（同名メソッド）のテストケース ※ テストフィクスチャ未作成（ロジックは実装済）
- [x] pytest で全テスト PASS（19/19）

### Phase 3: 生成ロジック (2-3週間)
**成果物**: INDEX.md, parts/, MAP.json の生成完了

5. **INDEX.md 生成** (`generators/index_generator.py`)
   - クラス/メソッド一覧、行範囲、分割ファイルへのリンク作成
   - Docstring/Javadoc抽出（role欄）
   - 呼び出し関係の記載（calls欄、ヒューリスティック）
   - 副作用情報の推定（side effects欄、キーワード検出）
   - Markdown形式で `INDEX.md` ファイル出力
   - テスト: `tests/test_generators.py` で出力フォーマット検証

6. **parts/ 生成** (`generators/parts_generator.py`)
   - ソースコード分割: クラス/メソッド単位
   - 各分割ファイルのヘッダ付与（元ファイル、行範囲、シンボル名、依存情報）
   - ファイル命名: `parts/<ClassName>.class.<ext>`, `parts/<ClassName>_<methodName>.<ext>`
   - オーバーロード対応: ハッシュ衝突時の名前変更
   - テスト: 出力ファイル内容、ヘッダ形式検証

7. **MAP.json 生成** (`generators/map_generator.py`)
   - JSON スキーマに従った対応表出力
   - シンボル、type, 行番号、ファイル、checksum を記載
   - テスト: JSON妥当性検証

**チェックリスト**:
- [x] `INDEX.md` 生成成功、Markdown形式正常
- [x] `parts/` 内ファイル生成成功、ヘッダ形式正常
- [x] `MAP.json` 生成成功、JSON妥当性正常
- [x] pytest で全テスト PASS

### Phase 4: 統合とテスト (1-2週間)
**成果物**: 実行可能なCLIツール、自動テスト環境、ドキュメント完成

8. **メイン処理統合** (`main.py`)
   - CLI引数パース して言語判定、パーサー選択
   - パーサー → INDEX.md生成 → parts生成 → MAP.json生成 の流れ実装
   - 出力ディレクトリ自動作成
   - エラー処理、明確なエラーメッセージ出力
   - `--dry-run`, `--verbose` オプション実装
   - テスト: `tests/test_e2e.py` で end-to-end実行

9. **自動テスト環境構築** (`.github/workflows/tests.yml`)
   - GitHub Actions で Python 3.9/3.10/3.11/3.12 で pytest 実行
   - カバレッジレポート生成（pytest-cov）
   - lint チェック（ruff check）
   - フォーマットチェック（ruff format --check）
   - 型チェック（mypy）

10. **ドキュメント完成**
    - README.md: インストール、使用例、ワークフロー、既知制限を記載
    - Spec.md: 技術スタック確定、エラーハンドリング詳細化
    - Plan.md: 進捗状況、完了フェーズのまとめ
    - CONTRIBUTING.md: 開発ガイドライン（PR/Issues対応方法）
    - 警告の出力先（MVP）は `INDEX.md` と `stderr` に限定し、`MAP.json` には含めない方針を明記

**チェックリスト**:
- [x] `code2map build tests/fixtures/sample.java --out /tmp/test-out` 成功
- [x] `/tmp/test-out/INDEX.md`, `parts/`, `MAP.json` 全て生成
- [x] pytest: 全ユニット・統合テスト PASS（19/19、カバレッジ87%）
- [ ] GitHub Actions: 自動テスト green ※ リモート未push（ローカルのみ確認済）
- [ ] README, Spec, Plan 最終レビュー完了 ※ 本評価で実施中

## タイムライン
| フェーズ | 期間 | 目標 | 依存 |
|--------|------|------|------|
| Phase 1 | 1-2週間 | CLI基本動作、プロジェクト構造確立 | - |
| Phase 2 | 2-3週間 | Java/Python パーサー完成 | Phase 1 |
| Phase 3 | 2-3週間 | INDEX.md, parts/, MAP.json 生成完成 | Phase 2 |
| Phase 4 | 1-2週間 | 統合テスト、ドキュメント、リリース準備 | Phase 3 |
| **総期間** | **6-8週間** | **v0.1.0 リリース（MVP）** | - |

## リスク管理 & バックアップ計画
### 想定リスク
| リスク | 対策 |
|------|------|
| Java/Python パーサの複雑性 | Phase 2 で簡易実装から開始。複雑な言語機能は後回し |
| AST解析エラー（不正構文） | `--verbose` で詳細ログ、部分的解析継続 |
| 大規模ファイル処理遅延 | メモリ効率を意識。必要に応じてジェネレータ化 |
| 仕様の変更要求 | MVP (v0.1.0) 後に Phase 5 で対応 |

### アーリーアクセス（Phase 2-3完了後）
- beta版を社内レビュー、フィードバック収集
- ユースケース検証（想定ワークフロー通り動作するか）

### v0.1.0 リリース条件
- Phase 4 すべて完了
- ユニット・統合テスト全て PASS
- README/Spec 完成
- GitHub リポジトリ公開準備完了

## エッジケーステスト計画
Phase 2-3 で以下のエッジケースをテストフィクスチャとして用意し、正しく動作することを確認する。

| ケース | 期待動作 |
|--------|---------|
| 空ファイル（0行） | シンボル0個、空のINDEX.md / MAP.json を生成 |
| コメントのみのファイル | シンボル0個、正常終了 |
| 単一関数のみ（クラスなし）のPythonファイル | 関数シンボル1個を抽出 |
| 構文エラーを含むファイル | 部分的解析続行、終了コード `2`、INDEX.md に `[WARNING]` |
| オーバーロードされた同名メソッド（Java） | ハッシュ付きで一意なファイル名生成 |
| 深いネスト（3階層以上のクラス） | 命名規則に従い正しくファイル生成 |
| 非UTF-8エンコーディングファイル | 警告メッセージ + ベストエフォート処理 |
| 出力先に既存ファイルがある場合 | 上書き動作、他ファイルは保持 |
| 非対応拡張子（--lang未指定） | エラーメッセージ + 終了コード `1` |
| 2000行超の大規模ファイル | 数秒以内に処理完了（パフォーマンス） |

## 開発環境セットアップ
```bash
# リポジトリクローン
git clone https://github.com/<org>/code2map.git
cd code2map

# 仮想環境の作成・有効化
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# 開発モードでインストール（依存含む）
pip install -e ".[dev]"

# 動作確認
code2map --help
pytest
ruff check code2map/
mypy code2map/
```

## v0.1.0 実装評価結果

### 達成状況サマリ
| 項目 | 結果 |
|------|------|
| テスト | 19/19 PASS (0.55秒) |
| カバレッジ | 87%（目標80%超） |
| Python パーサー | ✅ 実装完了 |
| Java パーサー | ✅ 実装完了 |
| INDEX.md 生成 | ✅ 実装完了 |
| parts/ 生成 | ✅ 実装完了 |
| MAP.json 生成 | ✅ 実装完了 |
| CLI (build/dry-run/verbose) | ✅ 実装完了 |
| エッジケーステスト | ✅ 9テストケース実装 |
| e2e テスト | ✅ 8テストケース実装 |
| CI/CD (GitHub Actions) | ✅ 設定作成済（ローカルのみ確認） |

### ファイル構造の計画との差異
| 計画のファイル | 実際 | 状況 |
|--------------|------|------|
| `pyproject.toml` | `setup.py` | 代替手段で実装。機能同等 |
| `models/metadata.py` | 未作成 | Symbol クラスに統合。実用上問題なし |
| `utils/lang_detect.py` | 未作成 | `cli.py` 内の `_detect_lang()` で実装 |
| `CONTRIBUTING.md` | 未作成 | 未着手 |
| `CHANGELOG.md` | 作成済 | 計画になかったが追加（良い判断） |
| `tests/test_edge_cases.py` | 作成済 | 計画になかったが追加（良い判断） |

### 残課題（v0.1.1 で対応推奨）

#### 優先度: 高
1. **Side Effects キーワード拡充**: 実装のキーワードが Spec のテーブルより大幅に少ない。`logging.`, `logger.`, `raise`, `commit`, `requests.` 等の追加が必要
2. **開発ツール（ruff, mypy）のインストール確認**: venv に ruff/mypy が未インストールの状態。`pip install -e ".[dev]"` の実行確認が必要

#### 優先度: 中
3. **`pyproject.toml` への移行**: PEP 621 準拠の現代的パッケージング。`setup.py` からの移行
4. **Java オーバーロードのテストフィクスチャ作成**: ロジックは実装済だがテストが不在
5. **Java コンストラクタの calls 抽出**: `<init>` シンボルに呼び出し関係が記録されない
6. **デッドコード削除**: `python_parser.py` の `_ignore_new_symbol` フィールド

#### 優先度: 低
7. **`CONTRIBUTING.md` 作成**
8. **`models/metadata.py` / `utils/lang_detect.py` の分離**: アーキテクチャ整理として
9. **パース失敗時の部分シンボル返却**: 構文エラー時に既抽出分を返す機能

## 拡張計画
- 新言語追加（JavaScript: acorn, C++: clang）
- 設定ファイル（分割粒度カスタム）
- GitHub Actions統合（PRごと自動生成）
- Side Effects キーワードリストのユーザーカスタマイズ対応
- Tree-sitter への移行による精度・パフォーマンス向上
