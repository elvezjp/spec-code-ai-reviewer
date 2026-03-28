# OpenAI・Bedrock プロバイダー API 呼び出し更新 修正計画書

## 概要

AI モードで OpenAI の gpt-5.2 を使用した際に「max_tokens がサポートされていない」旨のエラーが発生する。
また Bedrock プロバイダーも旧 API（`invoke_model`）を使用しており、最新の Converse API に移行すべき状態。

対応 Issue: [#21](https://github.com/elvezjp/md2map/issues/21)

## 背景

- OpenAI の新しいモデル（gpt-5.2 等）は `max_tokens` パラメータを廃止し、`max_completion_tokens` を使用する仕様に変更された
- Bedrock の `invoke_model` は生 JSON body で Anthropic モデル専用形式にハードコードされており、Amazon Nova 等の他モデルに対応できない
- 別プロジェクト（spec-code-ai-reviewer v0.9.5）では両方とも対応済み

## 前提

- 現在の実装: md2map ルート（`md2map/`）、バージョン v0.4.1
- 今回の修正は v0.4.2 として実装する

---

## Step 0: v0.4.1 の退避と v0.4.2 の準備

### v0.4.1 の退避

現在の実装を `versions/v0.4.1` に退避する。

```
対象ファイル:
  md2map/         → versions/v0.4.1/md2map/
  tests/          → versions/v0.4.1/tests/
  main.py         → versions/v0.4.1/main.py
  pyproject.toml  → versions/v0.4.1/pyproject.toml
  uv.lock         → versions/v0.4.1/uv.lock
  spec.md         → versions/v0.4.1/spec.md
```

### v0.4.2 の準備

- `pyproject.toml` の `version` を `"0.4.2"` に更新

---

## 現状の問題箇所

### 比較表（md2map vs spec-code-ai-reviewer v0.9.5）

| プロバイダー | 項目 | md2map（現状） | AIレビュアー（対応済み） |
|---|---|---|---|
| **OpenAI** | トークン指定 | `max_tokens` | `max_completion_tokens` |
| **Bedrock** | API 方式 | `invoke_model`（旧API） | `converse`（新API） |
| **Bedrock** | リクエスト形式 | 生 JSON body を自前構築 | 構造化パラメータ |
| **Bedrock** | トークン指定 | `"max_tokens"` in JSON body | `inferenceConfig={"maxTokens": ...}` |
| **Bedrock** | 対応モデル | Anthropic 専用（`anthropic_version` 固定） | Anthropic / Amazon Nova 等マルチモデル |
| **Anthropic** | — | 差異なし | 差異なし |

---

## Step 1: v0.4.1 の退避と v0.4.2 の準備

- `versions/v0.4.1/` に現在の実装を退避
- `pyproject.toml` の version を `"0.4.2"` に更新

---

## Step 2: OpenAI プロバイダーの修正

### `md2map/llm/openai_provider.py` の変更

`max_tokens` → `max_completion_tokens` に変更する。

```python
# Before
response = self._client.chat.completions.create(
    model=self._model,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ],
    max_tokens=self._max_tokens,
)

# After
response = self._client.chat.completions.create(
    model=self._model,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ],
    max_completion_tokens=self._max_tokens,
)
```

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `md2map/llm/openai_provider.py` L30 | `max_tokens` → `max_completion_tokens` |

---

## Step 3: Bedrock プロバイダーの修正

### `md2map/llm/bedrock_provider.py` の変更

`invoke_model` + 生 JSON body → `converse` API + 構造化パラメータに移行する。

```python
# Before
def send_message(self, system_prompt: str, user_message: str) -> str:
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": self._max_tokens,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_message},
        ],
    })

    response = self._client.invoke_model(
        modelId=self._model,
        contentType="application/json",
        accept="application/json",
        body=body,
    )

    response_body = json.loads(response["body"].read())
    content = response_body.get("content", [])
    if not content or not content[0].get("text"):
        raise RuntimeError("Bedrock API returned empty response")
    return content[0]["text"]

# After
def send_message(self, system_prompt: str, user_message: str) -> str:
    response = self._client.converse(
        modelId=self._model,
        messages=[{
            "role": "user",
            "content": [{"text": user_message}],
        }],
        system=[{"text": system_prompt}],
        inferenceConfig={"maxTokens": self._max_tokens},
    )

    output = response.get("output", {})
    message = output.get("message", {})
    content = message.get("content", [])
    if not content or not content[0].get("text"):
        raise RuntimeError("Bedrock API returned empty response")
    return content[0]["text"]
```

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `md2map/llm/bedrock_provider.py` L1-56 | `invoke_model` → `converse` API に全面書き換え、`import json` 不要に |

---

## Step 4: テストの更新

既存の LLM プロバイダーテストを更新し、新しい API 呼び出し形式に対応させる。

### テストケース

| # | ケース | 内容 |
|---|---|---|
| 1 | OpenAI パラメータ確認 | `max_completion_tokens` で API が呼ばれることを確認 |
| 2 | Bedrock Converse API 確認 | `converse` メソッドが正しいパラメータで呼ばれることを確認 |
| 3 | Bedrock レスポンスパース | Converse API のレスポンス形式が正しくパースされることを確認 |
| 4 | 既存 Anthropic テスト | 変更なし（回帰確認） |

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `tests/test_llm_providers.py`（既存 or 新規） | OpenAI / Bedrock のテストを更新 |

---

## Step 5: spec.md の更新

LLM プロバイダーに関する記述がある場合、以下を更新する:

- OpenAI プロバイダーが `max_completion_tokens` を使用する旨
- Bedrock プロバイダーが Converse API を使用し、マルチモデル対応である旨

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `spec.md` | LLM プロバイダーの API 仕様に関する記述を更新 |

---

## Step 6: CHANGELOG.md / CHANGELOG_ja.md の更新

### CHANGELOG.md（英語）

`[0.4.1]` の上に `[0.4.2]` セクションを追加する。

```markdown
## [0.4.2] - 2026-03-28

Updated OpenAI and Bedrock LLM provider API calls to latest specifications. OpenAI now uses `max_completion_tokens` parameter (required for gpt-5.2+). Bedrock migrated from `invoke_model` to Converse API for multi-model support.

### Changed

- **OpenAI provider**: Changed `max_tokens` parameter to `max_completion_tokens` in `chat.completions.create()` call
  - Required for newer OpenAI models (gpt-5.2 and later) that no longer support `max_tokens`

- **Bedrock provider**: Migrated from `invoke_model` (raw JSON body) to `converse` API
  - Replaced Anthropic-specific `anthropic_version` + `invoke_model` with model-agnostic Converse API
  - Token limit now specified via `inferenceConfig={"maxTokens": ...}` instead of JSON body
  - Supports Anthropic, Amazon Nova, and other Bedrock-compatible models
  - Removed `import json` dependency (no longer needed)

### Known Limitations

This version has the following limitations:

- NLP mode requires SudachiPy installation
- AI mode requires API keys or AWS credentials for each provider
- Single file processing only (directory-level analysis not supported)
- ATX-style headings only (Setext-style underline headings not supported)
```

### CHANGELOG_ja.md（日本語）

```markdown
## [0.4.2] - 2026-03-28

OpenAI・Bedrock の LLM プロバイダー API 呼び出しを最新仕様に更新。OpenAI は `max_completion_tokens` パラメータを使用するよう変更（gpt-5.2 以降で必須）。Bedrock は `invoke_model` から Converse API に移行し、マルチモデル対応を実現しました。

### 変更

- **OpenAI プロバイダー**: `chat.completions.create()` のパラメータを `max_tokens` から `max_completion_tokens` に変更
  - gpt-5.2 以降の新しい OpenAI モデルで `max_tokens` が廃止されたことへの対応

- **Bedrock プロバイダー**: `invoke_model`（生 JSON body）から `converse` API に移行
  - Anthropic 専用の `anthropic_version` + `invoke_model` を、モデル非依存の Converse API に置き換え
  - トークン上限の指定を JSON body 内の `max_tokens` から `inferenceConfig={"maxTokens": ...}` に変更
  - Anthropic / Amazon Nova 等の Bedrock 対応モデルを広くサポート
  - `import json` 依存を削除（不要になったため）

### 既知の制限事項

このバージョンには以下の制限があります：

- NLPモードは SudachiPy のインストールが必要
- AIモードは各プロバイダーのAPIキーまたはAWS認証情報が必要
- 単一ファイルのみ対応（ディレクトリ単位の解析は未対応）
- ATX形式の見出しのみ対応（Setext形式の下線見出しは未対応）
```

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `CHANGELOG.md` | `[0.4.2]` セクションを `[0.4.1]` の上に追加 |
| `CHANGELOG_ja.md` | `[0.4.2]` セクションを `[0.4.1]` の上に追加 |

---

## Step 7: versions/README.md のバージョン比較更新

### バージョン比較表の更新

ヘッダ行の `v0.4.1 (現行)` → `v0.4.1` に変更し、右端に `v0.4.2 (現行)` 列を追加する。

各行の v0.4.2 列の値:

| 項目 | v0.4.2 の値 |
|---|---|
| 分割モード | heading / nlp / ai |
| サマリー生成 | （v0.4.0 と同等） |
| セクション単位オーバーライド | + サブスプリットが親セクションの override を継承 |
| 見出し一覧取得 | `headings` サブコマンド / `extract_headings()` |
| AI サブスプリット命名 | `<セクション名>: part-N` |
| AI プロンプトカスタマイズ | + セクション単位の `ai_prompt_extra_notes` オーバーライド |
| AI プロンプト構造 | 4 パート構成（+ サマリー用4パート構成） |
| LLM エラーハンドリング | ログ出力 + `warnings` リストに追加 |
| LLM / NLP 初期化 | 遅延初期化対応（summary_mode=ai でも初期化） |
| LLM プロバイダー | openai / anthropic / bedrock |
| **LLM プロバイダー API** | **OpenAI: `max_completion_tokens`、Bedrock: Converse API** |
| CLI オプション | （v0.4.0 と同等） |

### ディレクトリ構成の更新

```
├── v0.4.1/
│   └── ...
```

を追加。

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/README.md` | バージョン比較表に v0.4.2 列追加、ディレクトリ構成に v0.4.1 追加 |

---

## Step 8: README.md / SECURITY.md のバージョン番号・構成更新

### README.md

- Directory Structure セクションの `versions/` 配下に `v0.4.1/` エントリを追加

```markdown
│   ├── v0.4.0/            # v0.4.0 snapshot
│   ├── v0.4.1/            # v0.4.1 snapshot   ← 追加
│   └── README.md          # versions directory description
```

### README_ja.md

- README.md と同等の変更を適用

### SECURITY.md

- Supported Versions テーブルのバージョン番号を更新

```markdown
| Version | Supported          |
| ------- | ------------------ |
| 0.4.2   | :white_check_mark: |
| < 0.4.2 | :x:                |
```

### SECURITY_ja.md

- SECURITY.md と同等の変更を適用

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `README.md` | Directory Structure に `v0.4.1/` 追加 |
| `README_ja.md` | Directory Structure に `v0.4.1/` 追加 |
| `SECURITY.md` | Supported Versions を `0.4.2` に更新 |
| `SECURITY_ja.md` | Supported Versions を `0.4.2` に更新 |

---

## 影響範囲

| 対象 | 影響 |
|---|---|
| `versions/v0.4.1/` | v0.4.1 の退避 |
| `pyproject.toml` | `version` を `"0.4.2"` に更新 |
| `md2map/llm/openai_provider.py` | `max_tokens` → `max_completion_tokens` に変更（1行） |
| `md2map/llm/bedrock_provider.py` | `invoke_model` → `converse` API に全面書き換え |
| `tests/` | OpenAI / Bedrock テストの更新 |
| `spec.md` | バージョン番号更新、LLM プロバイダー仕様の追記 |
| `CHANGELOG.md` | `[0.4.2]` セクション追加 |
| `CHANGELOG_ja.md` | `[0.4.2]` セクション追加 |
| `versions/README.md` | バージョン比較表に v0.4.2 列追加、ディレクトリ構成更新 |
| `README.md` | Directory Structure に `v0.4.1/` 追加 |
| `README_ja.md` | Directory Structure に `v0.4.1/` 追加 |
| `SECURITY.md` | Supported Versions を `0.4.2` に更新 |
| `SECURITY_ja.md` | Supported Versions を `0.4.2` に更新 |
| `md2map/llm/anthropic_provider.py` | 変更なし |
| `md2map/llm/config.py` | 変更なし |
| `md2map/llm/factory.py` | 変更なし |
| 既存テスト | Anthropic テストは影響なし |

---

## 完了チェックリスト

### Step 1: v0.4.1 の退避と v0.4.2 の準備

- [x] `versions/v0.4.1/` に既存実装を退避
- [x] `pyproject.toml` の version を `"0.4.2"` に更新

### Step 2: OpenAI プロバイダーの修正

- [x] `max_tokens` → `max_completion_tokens` に変更

### Step 3: Bedrock プロバイダーの修正

- [x] `invoke_model` → `converse` API に移行
- [x] `import json` の削除
- [x] レスポンスパース処理の更新

### Step 4: テストの更新

- [x] OpenAI パラメータテストの更新
- [x] Bedrock Converse API テストの更新
- [x] 全テスト通過（133件）

### Step 5: spec.md の更新

- [x] LLM プロバイダー仕様の記述を更新

### Step 6: CHANGELOG の更新

- [x] `CHANGELOG.md` に `[0.4.2]` セクション追加
- [x] `CHANGELOG_ja.md` に `[0.4.2]` セクション追加

### Step 7: versions/README.md の更新

- [x] バージョン比較表に v0.4.2 列追加
- [x] ディレクトリ構成に v0.4.1 追加

### Step 8: README.md / SECURITY.md の更新

- [x] `README.md` の Directory Structure に `v0.4.1/` 追加
- [x] `README_ja.md` の Directory Structure に `v0.4.1/` 追加
- [x] `SECURITY.md` の Supported Versions を `0.4.2` に更新
- [x] `SECURITY_ja.md` の Supported Versions を `0.4.2` に更新

### 最終確認

- [x] 既存テストが全て通過（後方互換性維持、全 133 件パス）
- [x] `spec.md` の更新内容が実装と整合している
- [x] CHANGELOG の英語・日本語が整合している
- [x] バージョン番号がすべてのファイルで `0.4.2` に統一されている

---
---

# 追加計画: AI プロバイダー認証情報の設定方法整備

対応 Issue: [#22](https://github.com/elvezjp/md2map/issues/22)

## 概要

AI モードで OpenAI / Anthropic / Bedrock を使用する際の認証情報について、`.env` ファイル対応、外部注入時の優先順位明確化、README への設定方法記載を行う。

## 背景

- 現在 `build_llm_config_from_env()` が `os.getenv()` で環境変数を直接読み取っているが、`.env` ファイルからの読み込みはサポートしていない
- 外部アプリケーション（spec-code-ai-reviewer 等）から `LLMConfig` を注入する場合の優先順位が明文化されていない
- README に認証情報の設定方法が記載されていない

## 現状の認証情報解決フロー

```
CLI (--ai-provider openai)
  → cli.py: build_llm_config_from_env(provider="openai")
    → factory.py: os.getenv("OPENAI_API_KEY")
      → LLMConfig(provider="openai", api_key=..., model=...)
        → MarkdownParser(llm_config=...)
```

外部アプリからの注入パス（spec-code-ai-reviewer の例）:

```
外部アプリの LLMConfig
  → _convert_to_md2map_llm_config()
    → md2map の LLMConfig(provider=..., api_key=..., ...)
      → MarkdownParser(llm_config=...)
```

## 認証情報の優先順位（設計）

```
1. llm_provider（直接注入されたプロバイダーインスタンス）  ← 既存
2. llm_config（直接注入された設定オブジェクト）            ← 既存
3. CLI オプション + 環境変数（build_llm_config_from_env）  ← 既存
4. .env ファイル                                          ← 新規
```

MarkdownParser のコンストラクタでの既存の優先順位（`llm_provider` > `llm_config` > `build_llm_config_from_env`）は変更しない。`.env` ファイルは `build_llm_config_from_env` 内で `os.getenv()` が参照する環境変数のソースとして機能する。

---

## Step 9: `.env` ファイル対応

### 方針

CLI のエントリポイント（`cli.py` の `main()`）で `.env` ファイルを読み込む。`python-dotenv` パッケージを使用し、既存の環境変数を上書きしない（`override=False`）。

これにより `build_llm_config_from_env()` 内の `os.getenv()` が `.env` の値を透過的に参照できる。`factory.py` 自体の変更は不要。

### `pyproject.toml` の変更

`python-dotenv` を `ai` オプション依存に追加する。

```toml
[project.optional-dependencies]
ai = [
    "openai>=1.0",
    "anthropic>=0.18",
    "boto3>=1.28",
    "python-dotenv>=1.0",
]
```

### `cli.py` の変更

`main()` の先頭で `.env` を読み込む。`python-dotenv` が未インストールの場合は無視する（AI モードを使わないユーザーは `md2map[ai]` をインストールしないため）。

```python
def main() -> int:
    # .env ファイルの読み込み（python-dotenv がインストールされている場合のみ）
    try:
        from dotenv import load_dotenv
        load_dotenv(override=False)
    except ImportError:
        pass

    # ... 既存処理 ...
```

### `.env.example` の作成

プロジェクトルートに `.env.example` を作成し、設定可能な環境変数の一覧を記載する。

```bash
# OpenAI
OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini

# Anthropic
# ANTHROPIC_API_KEY=sk-ant-...

# Amazon Bedrock
# AWS_ACCESS_KEY_ID=AKIA...
# AWS_SECRET_ACCESS_KEY=...
# AWS_REGION=ap-northeast-1

# Common
# MD2MAP_AI_MODEL=gpt-4o-mini
```

### `.gitignore` の確認

`.env` が `.gitignore` に含まれていることを確認する。含まれていなければ追加する。

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `pyproject.toml` | `ai` 依存に `python-dotenv>=1.0` を追加 |
| `md2map/cli.py` | `main()` 先頭で `load_dotenv(override=False)` を追加 |
| `.env.example` | 新規作成（環境変数一覧テンプレート） |
| `.gitignore` | `.env` が含まれていることを確認 |

---

## Step 10: README.md / README_ja.md への認証情報設定方法の記載

### README.md（英語）

「AI Mode Splitting」セクションの前に「Authentication」セクションを追加する。

```markdown
### Authentication (AI Mode)

AI mode requires credentials for the selected provider. Set them via environment variables or a `.env` file.

| Provider | Required Environment Variables | Default Model |
|----------|-------------------------------|---------------|
| OpenAI | `OPENAI_API_KEY` | `gpt-4o-mini` |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-haiku-4-5-20251001` |
| Bedrock | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` (or IAM role) | `global.anthropic.claude-haiku-4-5-20251001-v1:0` |

You can also set `MD2MAP_AI_MODEL` to override the default model for any provider.

#### Using a `.env` file

Copy the template and fill in your credentials:

\```bash
cp .env.example .env
# Edit .env with your credentials
\```

Environment variables set in the shell take precedence over `.env` values.
```

### README_ja.md（日本語）

README.md と同等の内容を日本語で記載する。

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `README.md` | 「Authentication (AI Mode)」セクションを追加 |
| `README_ja.md` | 「認証設定（AI モード）」セクションを追加 |

---

## Step 11: spec.md の認証情報解決順序の更新

### 既存の記述

spec.md の「6.1 LLM プロバイダー抽象化」に「LLM 設定の解決順序」がある。ここに `.env` ファイルと外部注入の優先順位を追記する。

```markdown
**LLM 設定の解決順序**:
1. `llm_provider`（プロバイダーインスタンスの直接注入）
2. `llm_config`（設定オブジェクトの直接注入）
3. CLI オプション（`--ai-model`, `--ai-region`）
4. 環境変数（`MD2MAP_AI_MODEL`, `AWS_REGION` 等）
5. `.env` ファイル（`override=False` のため、既存環境変数より低優先）
6. プロバイダーごとのデフォルト値
```

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `spec.md` | 認証情報の解決順序に `.env` と外部注入を追記 |

---

## Step 12: テストの追加

### テストケース

| # | ケース | 内容 |
|---|---|---|
| 1 | `.env` 読み込み確認 | `load_dotenv` が CLI 起動時に呼ばれることを確認（モック） |
| 2 | dotenv 未インストール時 | `ImportError` が握りつぶされ、正常に動作することを確認 |
| 3 | 環境変数優先確認 | 環境変数と `.env` の両方が設定されている場合、環境変数が優先されることを確認 |

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `tests/test_cli.py` | `.env` 読み込みに関するテストを追加 |

---

## 追加計画の影響範囲

| 対象 | 影響 |
|---|---|
| `pyproject.toml` | `ai` 依存に `python-dotenv>=1.0` を追加 |
| `md2map/cli.py` | `main()` 先頭に `load_dotenv` 追加（3行） |
| `.env.example` | 新規作成 |
| `.gitignore` | `.env` の確認・追加 |
| `README.md` | 認証設定セクション追加 |
| `README_ja.md` | 認証設定セクション追加 |
| `spec.md` | 解決順序の更新 |
| `tests/test_cli.py` | テスト追加 |
| `md2map/llm/factory.py` | **変更なし**（`.env` は `os.getenv` で透過的に参照される） |
| `md2map/llm/config.py` | **変更なし** |

---

## 追加計画の完了チェックリスト

### Step 9: `.env` ファイル対応

- [x] `pyproject.toml` に `python-dotenv>=1.0` を追加
- [x] `cli.py` の `main()` に `load_dotenv(override=False)` を追加
- [x] `.env.example` を作成
- [x] `.gitignore` に `.env` が含まれていることを確認（既存）

### Step 10: README の認証情報記載

- [x] `README.md` に認証設定セクションを追加
- [x] `README_ja.md` に認証設定セクションを追加

### Step 11: spec.md の更新

- [x] 認証情報の解決順序に `.env` と外部注入を追記

### Step 12: テストの追加

- [x] `.env` 読み込みテスト
- [x] dotenv 未インストール時のテスト
- [x] 環境変数優先テスト
- [x] 全テスト通過（136件）

### 最終確認

- [x] 既存テストが全て通過（後方互換性維持、全 136 件パス）
- [x] README の英語・日本語が整合している
- [x] `spec.md` の更新内容が実装と整合している
