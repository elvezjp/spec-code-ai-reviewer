# reasoningEffort 設定対応 実装計画書

> **ステータス**: 計画（2026-07-22）
> **対象バージョン**: v0.10.0 以降

## 概要

思考（reasoning）型モデルの思考量を制御する `reasoning_effort` パラメータを、
設定ファイル（ConfigFileGenerator で生成）から指定できるようにする。

[Kimi K3 での測定](./20260722-kimi-k3-reasoning-effort-benchmark.md)で、
`low` はデフォルト（`max`）の約4.1倍高速でありながら、本リポジトリのサンプルに対する
検出力が低下しないことを確認済み。利用者がモデル・用途に応じて思考量を調整できるようにする。

## パラメータ仕様の調査結果

### Kimi（Moonshot AI / OpenAI互換API）

| 項目 | 内容 |
|---|---|
| パラメータ名 | `reasoning_effort`（リクエストトップレベル） |
| 許容値 | `low` / `high` / `max` |
| デフォルト | `max` |
| 対応モデル | `kimi-k3`（思考は常時有効で無効化不可。強度調整のみ可能） |
| 参考 | [Kimi K3 Quickstart](https://platform.kimi.ai/docs/guide/kimi-k3-quickstart) / [Thinking Effort](https://platform.kimi.ai/docs/guide/thinking-effort) |

補足: Kimi の k2 系は `reasoning_effort` ではなく `thinking.type`（`enabled` / `disabled`）で制御する
（OpenAI SDK の標準引数ではないため本対応のスコープ外）。

### OpenAI 公式 API

| 項目 | 内容 |
|---|---|
| パラメータ名 | `reasoning_effort`（Chat Completions / Responses 両対応） |
| 許容値（全体集合） | `none` / `minimal` / `low` / `medium` / `high` / `xhigh` / `max` |
| デフォルト | モデル依存（例: GPT-5.5 は `medium`） |
| 対応モデル | o系・GPT-5系の推論モデル。**モデルごとに許容値のサブセットが異なる**（例: `xhigh` は gpt-5.1-codex-max 以降、`none` は gpt-5.2 以降） |
| 注意 | **非推論モデル（gpt-4o 等）はパラメータ自体に非対応でエラーになる** |
| 参考 | [Reasoning models ガイド](https://developers.openai.com/api/docs/guides/reasoning) |

### 設計上の帰結

1. **許容値を enum で固定しない**: Kimi と OpenAI で値の集合が異なり、OpenAI 内でもモデル依存。
   設定値は文字列としてそのまま API に渡し（パススルー）、値の妥当性検証は API 側に委ねる。
   不正値は API エラーとしてそのまま利用者に表示される（既存のエラーハンドリング経路）。
2. **未指定時は送信しない**: パラメータを付けなければ各モデルのデフォルト動作となり、
   従来と完全互換。非推論モデル（gpt-4o 等）を使う場合は未指定のままにしてもらう。
3. **対象は openai プロバイダーのみ**: anthropic / bedrock は別パラメータ体系のためスコープ外。

## 変更内容

### 1. ConfigFileGenerator（フロントエンド）

**`frontend/src/features/config-file-generator/schema/configSchema.ts`**

`llm` セクションの `openai` ケースに任意のテキストフィールドを追加する。

```ts
{
  id: 'reasoningEffort',
  label: 'Reasoning Effort（推論モデルのみ・任意）',
  type: 'text',
  placeholder: 'low / medium / high / max など（モデルにより異なる）',
},
```

- 既存の仕組みで、**未入力の任意フィールドは設定ファイルに出力されない**（`markdownGenerator.ts` の既存挙動）
- 出力形式: `- reasoningEffort: low`（フィールド id がそのまま出力キーになる既存仕様）
- `notes` に補足を追加:
  - 「Reasoning Effort は推論モデル（Kimi K3、GPT-5系等）の思考量を調整します。許容値はモデルにより異なります（Kimi K3: low/high/max、OpenAI: モデルごとに none/minimal/low/medium/high/xhigh/max のサブセット）。」
  - 「gpt-4o 等の非推論モデルでは指定しないでください（APIエラーになります）。」

新しいフィールドタイプ（select 等）は追加しない。選択式にするとモデルごとの許容値差分を
スキーマで管理し続けるコストが発生するため、自由入力＋説明文とする。

### 2. AIレビュアー本体（フロントエンド）

| ファイル | 変更 |
|---|---|
| `features/reviewer/types/index.ts` ほか型定義 | `LlmSettings` / `LlmConfig` に `reasoningEffort?: string` を追加 |
| `features/reviewer/hooks/useReviewerSettings.ts` | ①`llmKeyMap` に `reasoning_effort: 'reasoningEffort'` を追加（手書き設定ファイルのスネークケース互換）②`llmConfig` の組み立てに `reasoningEffort: reviewerConfig.llm.reasoningEffort` を追加 |
| `features/reviewer/services/api.ts` | `TestConnectionRequest` に `reasoningEffort?: string` を追加 |
| `features/reviewer/index.tsx` | 接続テスト呼び出しの組み立て（baseUrl と同様の箇所）に `reasoningEffort` を追加 |

レビュー系 API（一括 / 分割 / 統合 / Markdown整理 / サマリー）は `llmConfig` オブジェクトを
そのまま送信しているため、型と組み立ての追加だけで自動的に流れる。

### 3. バックエンド

| ファイル | 変更 |
|---|---|
| `app/models/schemas.py` | ①`LLMConfig` に `reasoningEffort: str \| None`（`validation_alias=AliasChoices("reasoningEffort", "reasoning_effort")`）を追加 ②`TestConnectionRequest` にも同様に追加 |
| `app/routers/review.py` | `/test-connection` の `LLMConfig` 組み立て（baseUrl と同じ箇所）に `reasoningEffort=request.reasoningEffort` を追加 |
| `app/services/openai_service.py` | `OpenAIProvider._create_chat_completion` で **`reasoningEffort` 指定時のみ** `reasoning_effort` を API に渡す（baseUrl の有無は問わない。公式 API の推論モデルでも有効なため） |

anthropic_service / bedrock_service は変更しない。

### 4. 検証用フックの撤去

`openai_service.py` に暫定で入れている検証用コード
（`_EXPERIMENT_REASONING_EFFORT` 定数・`[TIMING]` ログ）を削除し、本実装に置き換える。

### 5. md2map への引き継ぎ（フェーズ2・別対応）

分割プレビューの AI サマリー生成・AI 分割（md2map 経由）にも効かせるには、
md2map 側の `LLMConfig` / `OpenAIProvider` への `reasoning_effort` 追加が必要
（[md2map#37](https://github.com/elvezjp/md2map/pull/37) の base_url と同じ要領）。

- md2map 対応後、本体側は `split.py` の `_convert_to_md2map_llm_config` に1行追加するだけ
- セクション単位の短文要約には `low` で十分な見込みであり、
  [並列化（md2map#39）](https://github.com/elvezjp/md2map/pull/39)との組み合わせで大幅な高速化が期待できる
- 本計画書のスコープ外とし、md2map 側の Issue / PR で対応する

## テスト計画

### バックエンド

- `LLMConfig` が `reasoningEffort` / `reasoning_effort` の両キーを受け付ける（スキーマテスト）
- `OpenAIProvider`:
  - `reasoningEffort` 指定時に `reasoning_effort` が API 呼び出しに含まれる（baseUrl あり／なし両方）
  - 未指定時は `reasoning_effort` が含まれない（従来と同一の呼び出し）
- `/test-connection` が `reasoningEffort` を `LLMConfig` に引き継ぐ

### フロントエンド

- ConfigFileGenerator: `reasoningEffort` 入力時に `- reasoningEffort: low` が出力される／未入力時は出力されない
- 設定ファイルパーサー: `reasoningEffort:` / `reasoning_effort:` の両表記を読み込める
- `llmConfig` 組み立てに `reasoningEffort` が含まれる（既存の baseUrl テストと同様の観点）

### 手動確認

- Kimi K3 + `low` で一括レビューが高速化されること（ベンチマーク済みの再確認）
- `reasoningEffort` 未設定の既存設定ファイルで従来どおり動作すること（後方互換）
- 不正値（例: `turbo`）指定時に API エラーが利用者に表示されること

## 互換性

- 設定ファイルに `reasoningEffort` がない場合は一切送信しないため、既存設定ファイルは無変更で従来どおり動作する
- 設定ファイルのバージョン番号（`info.version`）の更新は不要（任意項目の追加のみ）

## 関連

- [20260722-kimi-k3-reasoning-effort-benchmark.md](./20260722-kimi-k3-reasoning-effort-benchmark.md)（測定結果）
- [PR #127](https://github.com/elvezjp/spec-code-ai-reviewer/pull/127)（baseUrl / maxTokens の md2map 引き継ぎ）
- [md2map#37](https://github.com/elvezjp/md2map/pull/37) / [md2map#39](https://github.com/elvezjp/md2map/pull/39)
- [Kimi K3 Quickstart](https://platform.kimi.ai/docs/guide/kimi-k3-quickstart) / [Thinking Effort](https://platform.kimi.ai/docs/guide/thinking-effort)
- [OpenAI Reasoning models ガイド](https://developers.openai.com/api/docs/guides/reasoning)
