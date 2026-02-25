# code2map

[English](./README.md) | [日本語](./README_ja.md)

[![Elvez](https://img.shields.io/badge/Elvez-Product-3F61A7?style=flat-square)](https://elvez.co.jp/)
[![IXV Ecosystem](https://img.shields.io/badge/IXV-Ecosystem-3F61A7?style=flat-square)](https://elvez.co.jp/ixv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Stars](https://img.shields.io/github/stars/elvezjp/code2map?style=social)](https://github.com/elvezjp/code2map/stargazers)

巨大なソースコードを、AI解析・レビュー向けの「意味的マップ（索引＋分割片）」に変換するCLIツールです。

![Input/Output Example](docs/assets/example.png)

## ユースケース

- **AIコードレビュー**: 大規模ファイルをAIが理解しやすい単位に分割し、レビュー精度を向上
- **コード構造の可視化**: クラス・メソッドの一覧と依存関係を索引として出力
- **行番号マッピング**: AIの指摘箇所を元ファイルの行番号に確実に対応付け
- **ドキュメント生成の補助**: コード構造を把握した上での設計書作成を支援

## 開発の背景

本ツールは、日本語の開発文書・仕様書を対象とした開発支援AI **IXV（イクシブ）** の開発過程で生まれた小さな実用品です。

IXVでは、システム開発における日本語の文書について、理解・構造化・活用という課題に取り組んでおり、本リポジトリでは、その一部を切り出して公開しています。

## 特徴

- **意味的な分割**: クラス・メソッド・関数単位でコードを分割（ビルド用ではなくレビュー用）
- **Markdown索引生成**: 役割説明・呼び出し関係・副作用を含むINDEX.mdを自動生成
- **行番号対応表**: 分割片と元ファイルの対応をMAP.json（機械可読）で提供
- **Python・Java対応**: AST解析による正確なシンボル抽出
- **ドライラン機能**: 実際の出力前に生成計画を確認可能

## ドキュメント

- [CHANGELOG.md](CHANGELOG.md) - バージョン履歴
- [CONTRIBUTING.md](CONTRIBUTING.md) - コントリビューション方法
- [SECURITY.md](SECURITY.md) - セキュリティポリシー
- [spec.md](spec.md) - 技術仕様書
- [docs/examples/](docs/examples/) - 使用例とサンプル入出力

## セットアップ

### 必要環境

- Python 3.9以上
- [uv](https://docs.astral.sh/uv/)（推奨パッケージマネージャー）

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/elvezjp/code2map.git
cd code2map

# uvで依存関係をインストール（仮想環境も自動作成）
uv sync --all-extras

# 動作確認
uv run code2map --help
```

## 使い方

### 基本的な実行

```bash
# Pythonファイルを解析
uv run code2map build your_code.py --out ./output

# Javaファイルを解析
uv run code2map build YourCode.java --out ./output
```

### 出力の確認

```bash
# 索引を確認
cat output/INDEX.md

# 分割されたコード片を確認
ls output/parts/

# 行番号対応表を確認
cat output/MAP.json
```

### ドライラン（プレビュー）

```bash
# ファイルを生成せずに計画を確認
uv run code2map build your_code.py --dry-run
```

## 主要オプション

| オプション | デフォルト | 説明 |
|-----------|-----------|------|
| `--out <DIR>` | `./code2map-out` | 出力ディレクトリ |
| `--lang {java,python}` | 自動検出 | 言語の明示指定 |
| `--id-prefix <PREFIX>` | `CD` | シンボルIDのプレフィックス（CD1, CD2, ...） |
| `--verbose` | false | 詳細ログを出力 |
| `--dry-run` | false | ファイル生成せずプレビューのみ |

詳細は `uv run code2map build --help` を参照してください。

## 出力例

### INDEX.md

```markdown
# Index: user_management.py

## Classes
- [CD1] UserManager (L10–L150) → parts/UserManager.class.py
  - role: ユーザー管理を行うメインクラス
  - calls: Database.connect, Logger.info
  - side effects: DB操作, ログ出力

## Methods
- [CD2] UserManager#create_user (L45–L80) → parts/UserManager_create_user.py
  - role: 新規ユーザーを作成する
  - calls: validate_email, hash_password
  - side effects: DB操作
```

### MAP.json

```json
[
  {
    "id": "CD1",
    "symbol": "UserManager",
    "type": "class",
    "original_file": "user_management.py",
    "original_start_line": 10,
    "original_end_line": 150,
    "part_file": "parts/UserManager.class.py",
    "checksum": "a1b2c3d4..."
  }
]
```

## ディレクトリ構成

```text
code2map/
├── code2map/              # メインパッケージ
│   ├── cli.py             # CLIエントリーポイント
│   ├── generators/        # 出力生成モジュール
│   │   ├── index_generator.py   # INDEX.md生成
│   │   ├── map_generator.py     # MAP.json生成
│   │   └── parts_generator.py   # parts/生成
│   ├── models/            # データモデル
│   │   └── symbol.py      # シンボル情報クラス
│   ├── parsers/           # 言語パーサー
│   │   ├── base_parser.py     # 基底クラス
│   │   ├── java_parser.py     # Javaパーサー
│   │   └── python_parser.py   # Pythonパーサー
│   └── utils/             # ユーティリティ
│       ├── file_utils.py  # ファイル操作
│       └── logger.py      # ログ設定
├── tests/                 # テストコード
│   └── fixtures/          # テストフィクスチャ
├── docs/                  # ドキュメント
│   ├── assets/            # 画像等のアセット
│   └── examples/          # 使用例とサンプル入出力
├── versions/              # 過去バージョンのスナップショット
├── CHANGELOG.md           # 変更履歴
├── CONTRIBUTING.md        # コントリビューションガイド
├── README.md              # 英語版README
├── README_ja.md           # 本ファイル（日本語版）
├── SECURITY.md            # セキュリティポリシー
├── spec.md                # 技術仕様書
└── pyproject.toml         # プロジェクト設定
```

## 制限事項

- **単一ファイル対応**: 現在は1ファイルずつの処理（ディレクトリ一括は今後対応予定）
- **静的解析のみ**: 動的ディスパッチやリフレクションは検出不可
- **対応言語**: Python、Javaのみ（他言語は今後拡張予定）

詳細は [spec.md](spec.md) を参照してください。

## セキュリティ

セキュリティに関する詳細は [SECURITY.md](SECURITY.md) を参照してください。

- 信頼できないソースからのファイル処理には注意してください
- 出力ファイルには元のソースコードが含まれます

## コントリビューション

コントリビューションを歓迎します。詳細は [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

- バグ報告・機能提案: [Issues](https://github.com/elvezjp/code2map/issues)
- プルリクエスト: ブランチ命名規則 `{ユーザー名}/{日付}-{内容}`

## 変更履歴

詳細は [CHANGELOG.md](CHANGELOG.md) を参照してください。

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照してください。

## 問い合わせ先

- **Issues**: [GitHub Issues](https://github.com/elvezjp/code2map/issues)
- **メール**: info@elvez.co.jp
- **会社**: [株式会社エルブズ](https://elvez.co.jp/)
