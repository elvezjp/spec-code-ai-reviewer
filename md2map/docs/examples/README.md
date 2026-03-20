# Examples

各バージョンの md2map 実行結果のサンプルです。入力ファイルと出力結果を含みます。

## ディレクトリ構成

```
examples/
├── v0.1/           # v0.1.0 の出力例（heading モードのみ）
├── v0.2/           # v0.2.0 の出力例（heading / nlp / ai モード）
├── v0.3/           # v0.3.0 の出力例（heading / nlp / ai モード）
└── v0.3.1/         # v0.3.1 の出力例（heading / nlp / ai モード + headings コマンド）
```

## 入力ファイル

- `20260218サンプルコーディング規約.md` - v0.2 以降で使用しているサンプル入力ファイル

## 再生成コマンド

### v0.3.1

```bash
# heading モード
uv run md2map build docs/examples/v0.3.1/20260218サンプルコーディング規約.md \
  --out docs/examples/v0.3.1/output-heading --split-mode heading

# NLP モード
uv run md2map build docs/examples/v0.3.1/20260218サンプルコーディング規約.md \
  --out docs/examples/v0.3.1/output-nlp --split-mode nlp

# AI モード
uv run md2map build docs/examples/v0.3.1/20260218サンプルコーディング規約.md \
  --out docs/examples/v0.3.1/output-ai --split-mode ai

# headings コマンド
uv run md2map headings docs/examples/v0.3.1/20260218サンプルコーディング規約.md \
  > docs/examples/v0.3.1/headings.json
```

### v0.3

```bash
uv run md2map build docs/examples/v0.3/20260218サンプルコーディング規約.md \
  --out docs/examples/v0.3/output-heading --split-mode heading

uv run md2map build docs/examples/v0.3/20260218サンプルコーディング規約.md \
  --out docs/examples/v0.3/output-nlp --split-mode nlp

uv run md2map build docs/examples/v0.3/20260218サンプルコーディング規約.md \
  --out docs/examples/v0.3/output-ai --split-mode ai
```

### v0.2

```bash
uv run md2map build docs/examples/v0.2/20260218サンプルコーディング規約.md \
  --out docs/examples/v0.2/output-heading --split-mode heading

uv run md2map build docs/examples/v0.2/20260218サンプルコーディング規約.md \
  --out docs/examples/v0.2/output-nlp --split-mode nlp

uv run md2map build docs/examples/v0.2/20260218サンプルコーディング規約.md \
  --out docs/examples/v0.2/output-ai --split-mode ai
```

### v0.1

v0.1 は heading モードのみ対応。

```bash
uv run md2map build docs/examples/v0.1/20260121AIオーディター形式サンプルコーディング規約.md \
  --out docs/examples/v0.1/output
```

## 注意事項

- AI モードの出力は LLM の応答によって分割位置が変わるため、再生成のたびに結果が異なる場合があります
- NLP モード・heading モードの出力は決定的です（同じ入力に対して常に同じ結果）
- 各バージョンの出力はそのバージョンの実装で生成されたものです。旧バージョンの再生成には `versions/` 配下の実装を使用してください
