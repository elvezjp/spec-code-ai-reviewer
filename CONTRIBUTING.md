# spec-code-ai-reviewer への貢献

このドキュメントでは、プロジェクトへの貢献に関するガイドラインを説明します。

## 貢献の方法

### バグの報告

バグを発見した場合は、以下の情報を含めて GitHub で Issue を作成してください：

- 明確で説明的なタイトル
- 問題を再現する手順
- 期待される動作
- 実際の動作
- サンプルファイル（可能であれば）
- Python のバージョン（バックエンド関連の場合）
- Node.js のバージョン（フロントエンド関連の場合）
- オペレーティングシステム

### 機能改善の提案

機能改善の提案を歓迎します！以下の内容で Issue を作成してください：

- 明確で説明的なタイトル
- 提案する機能の詳細な説明
- ユースケースとメリット
- 関連する例やモックアップ

### プルリクエスト

1. **リポジトリをフォーク**し、`main` からブランチを作成（ユーザ名/日付YYYYMMDD-内容）
   ```bash
   git checkout -b user/20260105-fix-feature
   ```

2. 既存のコードベースの**コーディングスタイルに従う**
   - 意味のある変数名と関数名を使用
   - 複雑なロジックにはコメントを追加
   - PEP 8 スタイルガイドラインに従う

3. 変更に対する**テストを作成**
   ```bash
   # バックエンドのテストを実行
   cd versions/v0.7.0/backend
   uv run pytest tests/ -v

   # バックエンドのカバレッジ付きテスト
   uv run pytest tests/ --cov=app --cov-report=html

   # フロントエンドのテストを実行
   cd versions/v0.7.0/frontend
   npm run test:run

   # フロントエンドのカバレッジ付きテスト
   npm run test:coverage
   ```

4. 必要に応じて**ドキュメントを更新**
   - ユーザー向けの変更は README.md を更新
   - 仕様の変更は spec.md を更新
   - 新機能を導入する場合は例を追加

5. 明確なコミットメッセージで**変更をコミット**
   ```bash
   git commit -m "Add feature: description of your changes"
   ```

6. **フォークにプッシュ**してプルリクエストを送信
   ```bash
   git push origin user/20260105-fix-feature
   ```

7. **レビューを待つ** - メンテナーが PR をレビューし、変更を依頼する場合があります

## 開発環境のセットアップ

### 前提条件

- Python 3.10 以上
- Node.js 18 以上
- [uv](https://docs.astral.sh/uv/) パッケージマネージャー
- AWS アカウント（Bedrock へのアクセス権限）または Anthropic/OpenAI API キー

### インストール

```bash
# フォークをクローン
git clone https://github.com/YOUR-USERNAME/spec-code-ai-reviewer.git
cd spec-code-ai-reviewer

# バックエンドの依存関係をインストール
cd versions/v0.7.0/backend
uv sync

# フロントエンドの依存関係をインストール
cd ../frontend
npm install
```

### テストの実行

```bash
# バックエンド：すべてのテストを実行
cd versions/v0.7.0/backend
uv run pytest tests/ -v

# バックエンド：特定のテストファイルを実行
uv run pytest tests/test_convert.py -v

# バックエンド：カバレッジ付きで実行
uv run pytest tests/ --cov=app --cov-report=html

# フロントエンド：すべてのテストを実行
cd versions/v0.7.0/frontend
npm run test:run

# フロントエンド：ウォッチモードでテストを実行
npm run test

# フロントエンド：カバレッジ付きで実行
npm run test:coverage
```

### 変更のテスト

PR を送信する前に、以下を確認してください：

1. 既存のすべてのテストがパスすること
2. 新機能には新しいテストが追加されていること
3. コードカバレッジが維持または改善されていること
4. アプリケーションがさまざまなファイルで正しく動作すること

## コーディングガイドライン

### Python スタイル（バックエンド）

- PEP 8 スタイルガイドラインに従う
- 適切な場所で型ヒントを使用
- 最大行長: 100 文字（長い文字列については柔軟に対応）
- 意味のある変数名を使用

### TypeScript/React スタイル（フロントエンド）

- ESLint の設定に従う（`npm run lint` で確認）
- TypeScript の厳格モードを使用
- コンポーネントは関数コンポーネントで記述
- Tailwind CSS でスタイリング
- 意味のあるコンポーネント名と変数名を使用

### ドキュメント

- すべてのパブリック関数とクラスに docstring/JSDoc を追加
- 明確で簡潔な言葉を使用
- 役立つ場合は docstring に例を含める

### コミットメッセージ

- 現在形を使用（「Added feature」ではなく「Add feature」）
- 命令形を使用（「Moves cursor to...」ではなく「Move cursor to...」）
- 最初の行は 72 文字以下に制限
- 関連する場合は Issue とプルリクエストを参照

例：
```
Add multi-provider LLM support

- Add Anthropic API integration
- Add OpenAI API integration
- Update configuration file format

Closes #123
```

## バージョン管理

貢献する際は：
- 最新バージョン（`versions/v0.7.0/`）に焦点を当てる
- 可能な限り後方互換性を維持する
- 破壊的変更は明確にドキュメント化する

## コードレビュープロセス

1. メンテナーがプルリクエストをレビューします
2. 変更の依頼や質問がある場合があります
3. 承認されると、PR がマージされます
4. 貢献はリリースノートで謝辞を記載します

## コミュニティガイドライン

- 敬意を持ち、包括的であること
- 建設的なフィードバックを提供すること
- 可能な場合は他の人を助けること
- 行動規範に従うこと

## ご質問

貢献についてご質問がある場合は、お気軽に：
- 「question」ラベルを付けて Issue を作成
- メンテナーに連絡
