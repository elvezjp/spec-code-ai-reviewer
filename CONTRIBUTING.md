# Contributing to code2map

code2mapへの貢献に興味を持っていただきありがとうございます。このドキュメントでは、プロジェクトへの貢献方法について説明します。

## 貢献の方法

プロジェクトへの貢献は以下の方法で行えます：

- **バグの報告**: 問題を発見した場合はIssueを作成してください
- **機能改善の提案**: 新機能のアイデアがあればIssueで提案してください
- **プルリクエスト**: コードの修正や機能追加をPRで送信してください

## バグ報告

バグを報告する際は、以下の情報を含めてIssueを作成してください：

- **明確で説明的なタイトル**: 問題を簡潔に説明するタイトル
- **再現手順**: 問題を再現するための具体的な手順
- **期待される動作**: 本来どのように動作すべきか
- **実際の動作**: 実際に起きた動作やエラーメッセージ
- **サンプルファイル**（可能であれば）: 問題を再現できる入力ファイル
- **環境情報**:
  - code2mapのバージョン（`uv run code2map --version`）
  - Pythonのバージョン（`python --version`）
  - OS（macOS, Linux, Windowsなど）

### バグ報告の例

```markdown
## タイトル
Python 3.12でデコレータ付きメソッドの解析に失敗する

## 再現手順
1. Python 3.12環境でcode2mapをインストール
2. 以下のコードを含むファイルを作成:
   ```python
   class Foo:
       @property
       def bar(self):
           return 1
   ```
3. `uv run code2map build test.py --out ./out` を実行

## 期待される動作
`bar`プロパティがINDEX.mdに記載される

## 実際の動作
以下のエラーが発生:
```
ParseError: Unexpected token at line 3
```

## 環境
- code2map: 0.1.0
- Python: 3.12.0
- OS: macOS 14.0
```

## 機能改善の提案

新機能や改善を提案する際は、以下の情報を含めてIssueを作成してください：

- **明確で説明的なタイトル**: 提案を簡潔に説明するタイトル
- **機能の詳細な説明**: 何を実現したいのか具体的に説明
- **ユースケースとメリット**: なぜこの機能が必要か、どのような場面で役立つか
- **関連する例やモックアップ**（可能であれば）: 期待する出力形式や動作のサンプル

## プルリクエストの手順

### 1. リポジトリのフォークとブランチ作成

```bash
# リポジトリをフォーク（GitHub上で実行）

# フォークしたリポジトリをクローン
git clone https://github.com/YOUR_USERNAME/code2map.git
cd code2map

# アップストリームを追加
git remote add upstream https://github.com/elvezjp/code2map.git

# 作業ブランチを作成
git checkout -b YOUR_USERNAME/YYYYMMDD-feature-name
```

**ブランチ命名規則**: `{ユーザー名}/{日付YYYYMMDD}-{内容}`

例:
- `tominaga/20260127-add-typescript-support`
- `yamada/20260201-fix-parse-error`

### 2. コーディングスタイルへの準拠

- [PEP 8](https://peps.python.org/pep-0008/) スタイルガイドラインに従ってください
- Ruffを使用してコードをフォーマットしてください

```bash
# コードのフォーマットとリント
uv run ruff format .
uv run ruff check . --fix
```

### 3. テストの作成と実行

新機能やバグ修正には、対応するテストを追加してください。

```bash
# すべてのテストを実行
uv run pytest

# 特定のテストファイルを実行
uv run pytest tests/test_python_parser.py

# カバレッジレポートを生成
uv run pytest --cov=code2map --cov-report=html
```

### 4. ドキュメントの更新

- 新機能を追加した場合は、README.mdを更新してください
- APIの変更がある場合は、関連するドキュメントを更新してください

### 5. コミットメッセージの書き方

コミットメッセージは以下の形式で記載してください：

```
<type>: <subject>

<body>

<footer>
```

**type**:
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメントのみの変更
- `style`: コードの意味に影響しない変更（フォーマットなど）
- `refactor`: バグ修正でも新機能でもないコード変更
- `test`: テストの追加・修正
- `chore`: ビルドプロセスやツールの変更

**良い例**:
```
feat: TypeScriptパーサーを追加

TypeScriptファイル(.ts, .tsx)の解析機能を実装しました。
- クラス、関数、インターフェースの抽出に対応
- デコレータの解析に対応

Closes #123
```

**悪い例**:
```
fix bug
```
```
修正
```

### 6. プッシュとPR送信

```bash
# 変更をプッシュ
git push origin YOUR_USERNAME/YYYYMMDD-feature-name
```

GitHub上でPull Requestを作成し、以下を含めてください：

- 変更内容の説明
- 関連するIssue番号（あれば）
- テスト方法

### 7. レビュー対応

- レビューコメントには丁寧に対応してください
- 修正が必要な場合は、追加コミットで対応してください

### PR送信前のチェックリスト

- [ ] コードがPEP 8スタイルに準拠している
- [ ] `uv run ruff check .` がエラーなしで完了する
- [ ] `uv run pytest` がすべてパスする
- [ ] 新機能には対応するテストを追加した
- [ ] 必要に応じてドキュメントを更新した
- [ ] コミットメッセージが規則に従っている

## 開発環境のセットアップ

### 前提条件

- Python 3.9以上
- [uv](https://docs.astral.sh/uv/)（推奨パッケージマネージャー）
- Git

### インストール手順

```bash
# リポジトリをクローン
git clone https://github.com/elvezjp/code2map.git
cd code2map

# 開発用依存関係を含めてインストール
uv sync --all-extras

# 動作確認
uv run code2map --help
uv run pytest
```

## テストの実行

```bash
# すべてのテストを実行
uv run pytest

# 詳細な出力で実行
uv run pytest -v

# 特定のテストファイルを実行
uv run pytest tests/test_python_parser.py

# 特定のテスト関数を実行
uv run pytest tests/test_python_parser.py::test_parse_class

# カバレッジ付きで実行
uv run pytest --cov=code2map

# HTMLカバレッジレポートを生成
uv run pytest --cov=code2map --cov-report=html
open htmlcov/index.html
```

## コーディングガイドライン

### スタイルガイド

- [PEP 8](https://peps.python.org/pep-0008/) に準拠してください
- Ruffをフォーマッタおよびリンターとして使用します

### 命名規則

- **関数・変数**: snake_case（例: `parse_file`, `output_dir`）
- **クラス**: PascalCase（例: `PythonParser`, `SymbolInfo`）
- **定数**: UPPER_SNAKE_CASE（例: `DEFAULT_OUTPUT_DIR`）
- **プライベート**: 先頭にアンダースコア（例: `_internal_method`）

### ドキュメント

- 公開関数・クラスにはdocstringを記載してください
- Google形式のdocstringを推奨します

```python
def parse_file(file_path: str, language: str | None = None) -> ParseResult:
    """ソースファイルを解析してシンボル情報を抽出する。

    Args:
        file_path: 解析対象のファイルパス
        language: 言語指定（省略時は拡張子から自動判定）

    Returns:
        解析結果を含むParseResultオブジェクト

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        ParseError: 解析に失敗した場合
    """
```

## お問い合わせ

- 質問や相談がある場合は、GitHubのIssueを作成してください
- `question` ラベルを付けていただけると助かります
- 一般的な議論はGitHub Discussionsもご利用いただけます

---

ご貢献をお待ちしております！
