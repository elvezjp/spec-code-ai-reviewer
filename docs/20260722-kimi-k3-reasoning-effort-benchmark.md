# Kimi K3 reasoning_effort による一括レビューの速度・品質測定結果

> **ステータス**: 測定完了（2026-07-22）
> **対象バージョン**: v0.10.0

## 概要

OpenAI互換API経由で Kimi K3（Moonshot AI）を使用した一括レビューにおいて、
`reasoning_effort` パラメータ（K3の思考量制御）が処理時間とレビュー品質に与える影響を測定した。

**結論: `low` は `max`（デフォルト）の約4.1倍高速で、本リポジトリのサンプルに対する検出力の低下は見られなかった。**

## 背景

- Kimi K3 は思考（reasoning）常時有効のモデルで、思考の強度はリクエストの
  トップレベルフィールド `reasoning_effort`（`"low"` / `"high"` / `"max"`、デフォルト `"max"`）でのみ調整できる
  （[Kimi K3 Quickstart](https://platform.kimi.ai/docs/guide/kimi-k3-quickstart) /
  [Thinking Effort](https://platform.kimi.ai/docs/guide/thinking-effort)）
- デフォルトの `max` では一括レビュー1回に3分以上かかっており、体感を大きく損ねていた
- なお、思考トークンも `max_tokens` を消費するため、出力上限が小さいと
  可視コンテンツが空になる（`OpenAI API returned empty response`）点に注意
  （分割サマリーの `max_tokens=800` 固定で発生し、設定値の引き継ぎに修正済み）

## 測定条件

| 項目 | 内容 |
|---|---|
| アプリ | AIレビュアー v0.10.0（一括レビューモード） |
| モデル | `kimi-k3`（OpenAI互換API / baseUrl: Moonshot AI） |
| 入力 | [docs/sample](./sample/README.md) の注文キャンセル設計書.xlsx（excel2md_mermaid変換）+ CancelOrderService.java |
| 入力トークン数 | 約6,611 |
| 測定方法 | `OpenAIProvider._create_chat_completion` に一時的な計測ログを挿入し、API呼び出しの所要時間を記録 |
| 実行回数 | 各effort 2回（アプリの標準動作） |

## 測定結果

### 処理時間

| reasoning_effort | 1回目 | 2回目 | 平均 | 出力トークン数 |
|---|---|---|---|---|
| `low` | 51.2秒 | 47.2秒 | **約49秒** | 1,673 |
| `high` | 96.1秒 | 93.8秒 | **約95秒** | 3,450 |
| `max`（明示指定） | 216.1秒 | 187.9秒 | **約202秒** | 7,353 |
| （参考）未指定 | 3分以上（体感） | — | — | 5,783 |

- **low は max の約4.1倍、high は max の約2.1倍高速**（low : high : max ≒ 1 : 2 : 4）
- 出力トークン数もほぼ同じ比率（1,673 : 3,450 : 7,353）で増加しており、所要時間は生成トークン量にほぼ比例
- 未指定時の所要時間・出力量は `max` とほぼ同等であり、ドキュメント記載どおり「デフォルト = max」を裏付け

### レビュー品質（docs/sample のアンサーキーとの突合）

[docs/sample/README.md](./sample/README.md) に記載された「仕込んである不整合」9件に対する検出状況:

| 観点 | low | high | max |
|---|---|---|---|
| アンサーキー9件の検出 | **9/9 全件検出** | **9/9 全件検出** | **9/9 全件検出** |
| 正解側コントロール（REQ-001 / REQ-009）の OK 判定 | 正しく OK | 正しく OK | 正しく OK |
| 偽陽性（実装済み機能への誤指摘） | なし | なし | なし |
| 行番号・要件引用の事実誤認 | なし | なし | なし |
| システムプロンプトの出力形式への準拠 | 準拠 | 準拠 | 準拠 |

`high` は突合結果一覧を15行（REQ-003を3行に分解、E-400/E-500/フローの行を追加）に構成し、
low より整理された表になった一方、max の1回目が出した境界値指摘（後述）は出していない。

### effort による差分

`max` のみが出した追加指摘（アンサーキー外・いずれも事実として正しい）:

- `elapsed.toHours()` の切り捨てによる期限判定の境界値問題（24時間59分でも期限内と判定される）
- エラー一覧の E-409 に二重キャンセル用メッセージが未定義という設計書側への差し戻し
- E-500 の用途相違に加えて、返金・在庫解放失敗時の try-catch 欠如の指摘
- 理由コード null 時の扱いが設計書に未記載という確認事項の明示

一方 `low` は同じ11項目の突合を約1/3.5の出力量で簡潔にまとめており、
コアの突合結果に不足はなかった。

### 実行間の揺らぎ（重要な知見）

`max` を2セット実行したところ、境界値の論点で**実行ごとに結論が反転**した:

- 1回目（19:16）: 「`toHours()` は切り捨てのため24時間59分でも期限超過と判定されない」→ **正しい指摘**
- 2回目（19:49）: 「ちょうど24時間は許可であり仕様と整合するため現行ロジックで可」→ 端数切り捨てを見落とした**不正確な結論**

つまり `max` の付加価値である深掘り指摘は**毎回安定して得られるわけではなく**、
約4倍のコスト（時間・トークン）に対してリターンが不確実である。

## 考察と推奨

- この規模（入力約6.6Kトークン）の突合レビューでは、**`low` を既定値とするのが合理的**
  - コア検出力は effort（low / high / max）・実行回によらず安定
  - `max` の優位は境界値解析等の「一歩踏み込んだ」領域に限られ、かつ再現性が低い
- `high` は時間・出力とも low と max のほぼ中間（約2倍）で、表構成の整理など体裁面の向上は
  見られたが、このサンプルでは検出内容の実質的な上積みはなかった
- リリース前の最終レビュー等、深掘りが欲しい場面でのみ `max`（または中間の `high`）に切り替える運用が現実的
- 分割レビューのAIサマリー生成（セクション単位の短文要約）は思考の恩恵がさらに小さいため、
  `low` 固定でも問題ない可能性が高い

## 今後の対応候補

1. 設定ファイル（`llm` セクション）に `reasoningEffort` を追加し、レビュー系API・分割API（md2map）へ引き継ぐ
2. md2map 側の `LLMConfig` / `OpenAIProvider` に `reasoning_effort` 対応を追加
   （[md2map#37](https://github.com/elvezjp/md2map/pull/37) の base_url 対応、
   [md2map#38](https://github.com/elvezjp/md2map/pull/38) のAI呼び出し並列化に続く改修）
3. 分割サマリーの高速化は「並列化（md2map#38）× reasoning_effort low」の組み合わせで大きな効果が見込める

## 関連

- [Kimi K3 Quickstart](https://platform.kimi.ai/docs/guide/kimi-k3-quickstart)
- [Thinking Effort - Kimi API Platform](https://platform.kimi.ai/docs/guide/thinking-effort)
- [Chat API リファレンス - Kimi API Platform](https://platform.kimi.ai/docs/api/chat)
- [spec-code-ai-reviewer#124](https://github.com/elvezjp/spec-code-ai-reviewer/pull/124)（Kimi API対応 / baseUrl追加）
- [md2map#34](https://github.com/elvezjp/md2map/issues/34)（AI呼び出し並列化 Issue）
- [docs/sample/README.md](./sample/README.md)（測定に使用したサンプルとアンサーキー）
