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
├── v0.3.1/
│   └── ...
├── v0.3.2/
│   └── ...
├── v0.4.0/
│   └── ...
├── v0.4.1/
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

| 項目 | v0.1.0 | v0.2.0 | v0.3.0 | v0.3.1 | v0.3.2 | v0.4.0 | v0.4.1 | v0.4.2 (現行) |
|------|--------|--------|--------|--------|--------|--------|--------|---------------|
| 分割モード | heading のみ | heading / nlp / ai | heading / nlp / ai | heading / nlp / ai | heading / nlp / ai | heading / nlp / ai | heading / nlp / ai | heading / nlp / ai |
| サマリー生成 | 固定100文字 | 固定100文字 | 固定100文字 | 固定100文字 | 固定100文字 | `--summary-max-chars` で文字数上限変更可、`--summary-mode ai` でLLM要約対応 | （v0.4.0 と同等） | （v0.4.0 と同等） |
| セクション単位オーバーライド | - | - | - | `--section-overrides` で `start_line` ごとに設定上書き可 | + skip: true でセクション除外可 | + `summary_max_chars`, `summary_mode` をセクション単位で指定可能 | + サブスプリットが親セクションの override を継承 | （v0.4.1 と同等） |
| 見出し一覧取得 | - | - | - | `headings` サブコマンド / `extract_headings()` | `headings` サブコマンド / `extract_headings()` | `headings` サブコマンド / `extract_headings()` | `headings` サブコマンド / `extract_headings()` | `headings` サブコマンド / `extract_headings()` |
| AI サブスプリット命名 | - | `<セクション名>: <LLM生成タイトル>` | `<セクション名>: part-N`（タイトル生成廃止） | `<セクション名>: part-N` | `<セクション名>: part-N` | `<セクション名>: part-N` | `<セクション名>: part-N` | `<セクション名>: part-N` |
| AI プロンプトカスタマイズ | - | 不可（ハードコード） | `--ai-prompt-extra-notes` で notes パート追記可 | + セクション単位の `ai_prompt_extra_notes` オーバーライド | + セクション単位の `ai_prompt_extra_notes` オーバーライド | + セクション単位の `ai_prompt_extra_notes` オーバーライド | + セクション単位の `ai_prompt_extra_notes` オーバーライド | + セクション単位の `ai_prompt_extra_notes` オーバーライド |
| AI プロンプト構造 | - | ハードコード | 4 パート構成（role / purpose / format / notes） | 4 パート構成 | 4 パート構成 | 4 パート構成（+ サマリー用4パート構成を追加） | 4 パート構成（+ サマリー用4パート構成） | 4 パート構成（+ サマリー用4パート構成） |
| LLM エラーハンドリング | - | ログ出力のみ | ログ出力のみ | ログ出力のみ | ログ出力のみ | ログ出力のみ | ログ出力 + `warnings` リストに追加 | ログ出力 + `warnings` リストに追加 |
| LLM / NLP 初期化 | - | コンストラクタで即時 | コンストラクタで即時 | 遅延初期化対応（オーバーライドで必要時に初期化） | 遅延初期化対応（オーバーライドで必要時に初期化） | 遅延初期化対応（summary_mode=ai でも初期化） | 遅延初期化対応（summary_mode=ai でも初期化） | 遅延初期化対応（summary_mode=ai でも初期化） |
| LLM プロバイダー | - | openai / anthropic / bedrock | openai / anthropic / bedrock | openai / anthropic / bedrock | openai / anthropic / bedrock | openai / anthropic / bedrock | openai / anthropic / bedrock | openai / anthropic / bedrock |
| LLM プロバイダー API | - | OpenAI: `max_tokens`、Bedrock: `invoke_model` | OpenAI: `max_tokens`、Bedrock: `invoke_model` | OpenAI: `max_tokens`、Bedrock: `invoke_model` | OpenAI: `max_tokens`、Bedrock: `invoke_model` | OpenAI: `max_tokens`、Bedrock: `invoke_model` | OpenAI: `max_tokens`、Bedrock: `invoke_model` | OpenAI: `max_completion_tokens`、Bedrock: Converse API |
| CLI オプション | `--out`, `--max-depth`, `--id-prefix`, `--verbose`, `--dry-run` | + `--split-mode`, `--split-threshold`, `--max-subsections`, `--ai-provider`, `--ai-model`, `--ai-region` | + `--ai-prompt-extra-notes` | + `--section-overrides` | + `--section-overrides` | + `--summary-max-chars`, `--summary-mode` | （v0.4.0 と同等） | （v0.4.0 と同等） |
