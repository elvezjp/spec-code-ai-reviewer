# Examples

code2mapの使用例です。各言語のサンプルファイルと、その出力結果を格納しています。

## Directory Structure

```
examples/
├── v0.2.0/                             # 最新バージョンの出力
│   ├── java/
│   │   ├── UserManagementService.java  # 入力ファイル
│   │   └── output/                     # 出力結果
│   │       ├── INDEX.md
│   │       ├── MAP.json
│   │       └── parts/
│   └── python/
│       ├── user_management_service.py  # 入力ファイル
│       └── output/                     # 出力結果
│           ├── INDEX.md
│           ├── MAP.json
│           └── parts/
└── v0.1.2/                             # 旧バージョンの出力（参照用）
    ├── java/
    └── python/
```

## Usage

### Java

```bash
# リポジトリルートから実行
uv run code2map build docs/examples/v0.2.0/java/UserManagementService.java --out docs/examples/v0.2.0/java/output
```

### Python

```bash
# リポジトリルートから実行
uv run code2map build docs/examples/v0.2.0/python/user_management_service.py --out docs/examples/v0.2.0/python/output
```

## Sample Files

### Java: UserManagementService.java

ユーザー管理システムのサービスクラス。以下の機能を含みます：

- `UserManagementService`: メインサービスクラス
  - ユーザーの登録、更新、削除
  - ユーザーの検索（ID、年齢範囲、メールドメイン）
  - 入力バリデーション
- `User`: ユーザーエンティティ
- `UserAlreadyExistsException`: ユーザー重複例外
- `UserNotFoundException`: ユーザー未発見例外

### Python: user_management_service.py

Javaサンプルと同等の機能をPythonで実装したもの。以下の機能を含みます：

- `UserManagementService`: メインサービスクラス
  - ユーザーの登録、更新、削除
  - ユーザーの検索（ID、年齢範囲、メールドメイン）
  - 入力バリデーション
- `User`: ユーザーエンティティ（dataclass）
- `UserAlreadyExistsException`: ユーザー重複例外
- `UserNotFoundException`: ユーザー未発見例外
