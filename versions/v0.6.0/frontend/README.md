# v0.6.0 フロントエンド

Vite + React + TypeScript で構築されたフロントエンドアプリケーションです。

## 技術スタック

- **フレームワーク**: React 19 + TypeScript
- **ビルドツール**: Vite 7
- **スタイリング**: Tailwind CSS v4
- **アイコン**: lucide-react
- **ルーティング**: React Router v7
- **テスト**: Vitest + Testing Library

## ディレクトリ構成

```
src/
├── core/                    # 共通コンポーネント・フック
│   ├── components/
│   │   ├── ui/              # 汎用UIコンポーネント（Button, Card, Modal等）
│   │   └── shared/          # 機能横断コンポーネント（SettingsModal等）
│   ├── hooks/               # 共通カスタムフック
│   └── types/               # 共通型定義
├── features/                # 機能別モジュール
│   ├── reviewer/            # レビュー機能
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── types/
│   └── config-file-generator/  # 設定ファイルジェネレーター機能
│       ├── components/
│       ├── hooks/
│       ├── schema/
│       └── services/
├── pages/                   # ページコンポーネント
├── __tests__/               # テストファイル
├── App.tsx                  # ルートコンポーネント
└── main.tsx                 # エントリーポイント
```

## 起動方法

### 前提条件

- Node.js 20以上
- npm

### 開発サーバー起動

```bash
# 依存関係のインストール
npm install

# 開発サーバー起動（http://localhost:5173）
npm run dev
```

**注意**: バックエンドAPIを使用するため、別ターミナルでバックエンドも起動してください。

```bash
# バックエンド起動（別ターミナル）
cd ../backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### 本番ビルド

```bash
# ビルド（dist/に出力）
npm run build

# ビルド結果のプレビュー
npm run preview
```

## コマンド一覧

| コマンド | 説明 |
|---------|------|
| `npm run dev` | 開発サーバー起動 |
| `npm run build` | 本番ビルド |
| `npm run preview` | ビルド結果のプレビュー |
| `npm run lint` | ESLintによる静的解析 |
| `npm test` | テスト実行（watchモード） |
| `npm run test:run` | テスト実行（単発） |
| `npm run test:coverage` | カバレッジ付きテスト実行 |

## 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `VITE_API_URL` | バックエンドAPIのURL | `http://localhost:8000` |

開発時は `vite.config.ts` のプロキシ設定により、`/api` へのリクエストは自動的にバックエンドに転送されます。
