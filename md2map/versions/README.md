# versions

新しいバージョンをリリースする際に、旧バージョンのスナップショットを保持するためのディレクトリです。

## 目的

- 各バージョン時点のソースコード・仕様・テストを丸ごと保存し、いつでも参照・比較できるようにする
- バージョン間の差分確認や、過去バージョンの動作検証を容易にする

## ディレクトリ構成

```
versions/
├── v0.1.0/
│   ├── main.py
│   ├── md2map/
│   ├── pyproject.toml
│   ├── spec.md
│   └── tests/
├── v0.2.0/
│   └── ...
├── v0.3.0/
│   └── ...
└── README.md
```

## 保持対象

| 対象 | 説明 |
|---|---|
| `main.py` | エントリポイント |
| `md2map/` | ソースコード |
| `pyproject.toml` | プロジェクト設定・依存関係 |
| `uv.lock` | 依存関係ロックファイル |
| `spec.md` | 仕様書 |
| `tests/` | テストコード・フィクスチャ |

## バージョン比較

| 項目 | v0.1.0 | v0.2.0 | v0.3.0 (現行) |
|------|--------|--------|---------------|
| 分割モード | heading のみ | heading / nlp / ai | heading / nlp / ai |
| AI サブスプリット命名 | - | `<セクション名>: <LLM生成タイトル>` | `<セクション名>: part-N`（タイトル生成廃止） |
| AI プロンプトカスタマイズ | - | 不可（ハードコード） | `--ai-prompt-extra-notes` / `ai_prompt_extra_notes` で notes パート追記可 |
| AI プロンプト構造 | - | ハードコード | 4 パート構成（role / purpose / format / notes） |
| LLM プロバイダー | - | openai / anthropic / bedrock | openai / anthropic / bedrock |
| CLI オプション | `--out`, `--max-depth`, `--id-prefix`, `--verbose`, `--dry-run` | + `--split-mode`, `--split-threshold`, `--max-subsections`, `--ai-provider`, `--ai-model`, `--ai-region` | + `--ai-prompt-extra-notes` |
