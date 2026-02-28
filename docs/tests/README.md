# テスト — spec-code-ai-reviewer

このディレクトリは、リリース前にAIを用いてレビューとシナリオテストを実行するための指示書と結果を管理する場所です。

## ディレクトリ構成

```
tests/
├── README.md          # このファイル
├── review.md          # AIレビュー指示書
├── scenarios.md       # シナリオテスト指示書
└── results/           # 実行結果の保存先
    └── YYYYMMDD-HHMM-review.md
    └── YYYYMMDD-HHMM-scenario.md
```

## 使い方

1. **AIレビュー**: `review.md` の内容をAIに渡して実行し、結果を `results/` に保存する
2. **シナリオテスト**: `scenarios.md` の内容をAIに渡して実行し、結果を `results/` に保存する

## 結果ファイルの命名規則

- **形式**: `YYYYMMDD-HHMM-{review|scenario}.md`
  - `YYYYMMDD-HHMM`: 実行日時（例: 20260228-1400）
  - `review` または `scenario`: テスト種別
- **例**: `20260228-1400-review.md`, `20260228-1500-scenario.md`

## 関連ドキュメント

- [spec.md](../versions/v0.9.0/spec.md) — 最新バージョンの仕様書
