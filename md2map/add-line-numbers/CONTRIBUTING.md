# add-line-numbers への貢献

このドキュメントでは、プロジェクトへの貢献に関するガイドラインを説明します。

## 貢献の方法

### バグの報告

バグを発見した場合は、以下の情報を含めて GitHub で Issue を作成してください：

- 明確で説明的なタイトル
- 問題を再現する手順
- 期待される動作
- 実際の動作
- サンプルファイル（可能であれば）
- Python のバージョン
- オペレーティングシステム

### 機能改善の提案

機能改善の提案を歓迎します！以下の内容で Issue を作成してください：

- 明確で説明的なタイトル
- 提案する機能の詳細な説明
- ユースケースとメリット
- 関連する例やモックアップ

### プルリクエスト

1. **リポジトリをフォーク**し、`main` からブランチを作成
   ```bash
   git checkout -b username/YYYYMMDD-description
   ```

2. 既存のコードベースの**コーディングスタイルに従う**
   - 意味のある変数名と関数名を使用
   - 複雑なロジックにはコメントを追加
   - PEP 8 スタイルガイドラインに従う

3. 変更に対する**テストを作成**
   ```bash
   pytest test.py -v
   ```

4. 必要に応じて**ドキュメントを更新**
   - ユーザー向けの変更は README.md を更新
   - 仕様の変更は spec.md を更新

5. 明確なコミットメッセージで**変更をコミット**
   ```bash
   git commit -m "Add feature: description of your changes"
   ```

6. **フォークにプッシュ**してプルリクエストを送信
   ```bash
   git push origin username/YYYYMMDD-description
   ```

7. **レビューを待つ** - メンテナーが PR をレビューし、変更を依頼する場合があります

## 開発環境のセットアップ

### 前提条件

- Python 3.8 以上

### インストール

```bash
# フォークをクローン
git clone https://github.com/YOUR-USERNAME/add-line-numbers.git
cd add-line-numbers

# テスト用に pytest をインストール（任意）
pip install pytest
```

### テストの実行

```bash
# テストを実行
pytest test.py -v

# 特定のテストを実行
pytest test.py::TestClassName::test_method -v
```

### 変更のテスト

PR を送信する前に、以下を確認してください：

1. 既存のすべてのテストがパスすること
2. 新機能には新しいテストが追加されていること
3. スクリプトがさまざまなテキストファイルで正しく動作すること

## コーディングガイドライン

### Python スタイル

- PEP 8 スタイルガイドラインに従う
- 適切な場所で型ヒントを使用
- 最大行長: 100 文字（長い文字列については柔軟に対応）
- 意味のある変数名を使用

### ドキュメント

- すべてのパブリック関数とクラスに docstring を追加
- 明確で簡潔な言葉を使用
- 役立つ場合は docstring に例を含める

### コミットメッセージ

- 現在形を使用（「Added feature」ではなく「Add feature」）
- 命令形を使用（「Moves cursor to...」ではなく「Move cursor to...」）
- 最初の行は 72 文字以下に制限
- 関連する場合は Issue とプルリクエストを参照

例：
```
Add support for custom line number format

- Add --format option for customizing line number format
- Update README with new option documentation

Closes #123
```

## コードレビュープロセス

1. メンテナーがプルリクエストをレビューします
2. 変更の依頼や質問がある場合があります
3. 承認されると、PR がマージされます

## コミュニティガイドライン

- 敬意を持ち、包括的であること
- 建設的なフィードバックを提供すること
- 可能な場合は他の人を助けること

## ご質問

貢献についてご質問がある場合は、お気軽に：

- 「question」ラベルを付けて Issue を作成
- README の問い合わせ先まで
