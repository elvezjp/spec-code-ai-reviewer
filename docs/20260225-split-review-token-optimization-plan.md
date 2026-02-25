# 分割レビュー: トークン最適化と要約リトライ機能

- 作成日: 2026/02/25
- 対象バージョン: v0.8.2
- ステータス: 計画
- 関連: `20260225-prompt-caching-plan.md`（プロンプトキャッシング）

## 背景

分割レビューでは3つのフェーズ（構造マッチング → グループレビュー → 結果統合）でLLMを呼び出す。グループレビュー（Phase 2）や結果統合（Phase 3）で、入力トークンがモデルの上限を超過してエラーになるケースがある。

現在の対応:
- 一括レビューで上限超過 → 分割レビューを案内（既存方針で十分）
- 分割レビューで上限超過 → リトライ/スキップのみ。リトライしても同じ入力のため同じエラーになる

## ゴール

1. **全体構造情報をINDEX.mdに統一**し、不要なトークン消費を削減する
2. **トークン超過エラー時に、設計書/コードを要約してリトライ**できるUIを提供する
3. ユーザーが要約結果をプレビュー・確認してからリトライを実行できる

## 非ゴール

- 一括レビューのトークン最適化（分割レビューへの誘導で対応）
- Phase 1（構造マッチング）のトークン最適化（INDEX.md/MAP.jsonのみで通常小さい）
- 自動要約の品質保証（ユーザーによるプレビュー確認を前提とする）

---

## 施策1: 全体構造情報をINDEX.mdに統一（常時適用）

### 概要

Phase 2（グループレビュー）とPhase 3（結果統合）の全体構造コンテキストで、現在INDEX.mdとMAP.jsonの両方を送信しているが、INDEX.mdのみに統一する。

### INDEX.mdを採用する理由

INDEX.mdはMAP.jsonの構造情報（ID、セクション名、行範囲、パートファイルパス）を全て含んでおり、さらにMAP.jsonに含まれない追加情報も保持している:

| 情報 | INDEX.md | MAP.json |
|------|----------|----------|
| ID・セクション名・行範囲・partファイルパス | あり | あり |
| 設計書の `summary`（内容概要） | あり | **なし** |
| コードの `role`（メソッドの役割） | あり | **なし** |
| コードの `calls`（呼び出し先） | あり | **なし** |
| コードの `side effects`（副作用） | あり | **なし** |
| `word_count` | **なし** | あり（レビューに不要） |
| `checksum` | **なし** | あり（レビューに不要） |

INDEX.mdはMAP.jsonの上位互換であり、MAP.jsonを併送する必要がない。

Phase 1（構造マッチング）ではMAP.jsonが主要入力のため変更なし。

### 削減効果の見積り

サンプルデータ（`md2map/docs/examples/v0.2/output-ai`, `code2map/docs/examples/java/output`）での比較:

| 項目 | 現在（INDEX.md + MAP.json） | 変更後（INDEX.mdのみ） | 削減率 |
|------|--------------------------|---------------------|-------|
| 設計書（12セクション） | INDEX.md 73行 + MAP.json 167行 | 73行 | 約70% |
| コード（27シンボル） | INDEX.md 58行 + MAP.json 272行 | 58行 | 約82% |

### Step 1-a. Phase 2 のMAP.json送信を除外

対象: `versions/v0.8.2/backend/app/routers/review.py:438-469`（グループレビューの全体構造コンテキスト構築）

現在:
```python
# 全体構造コンテキスト（他グループの存在を把握するため、参考情報として末尾に配置）
if request.documentIndexMd or request.codeIndexMd or request.allGroups:
    user_parts.append("\n## 全体構造情報（参考）\n")
    user_parts.append("以下は設計書・コード全体の構造です。このグループではこの一部をレビューしています。\n")
    if request.documentIndexMd:
        user_parts.extend([...])
    if request.documentMapJson:        # ← MAP.json送信
        user_parts.extend([
            "### 設計書全体の構造 (MAP.json)\n",
            "```json",
            json.dumps(request.documentMapJson, ensure_ascii=False, indent=2),
            "```",
            "",
        ])
    if request.codeIndexMd:
        user_parts.extend([...])
    if request.codeMapJson:            # ← MAP.json送信
        user_parts.extend([...])
    if request.allGroups:
        user_parts.extend([...])
```

変更後:
```python
# 全体構造コンテキスト（他グループの存在を把握するため、参考情報として末尾に配置）
if request.documentIndexMd or request.codeIndexMd or request.allGroups:
    user_parts.append("\n## 全体構造情報（参考）\n")
    user_parts.append("以下は設計書・コード全体の構造です。このグループではこの一部をレビューしています。\n")
    if request.documentIndexMd:
        user_parts.extend([
            "### 設計書全体の構造 (INDEX.md)\n",
            request.documentIndexMd,
            "",
        ])
    # MAP.jsonはINDEX.mdと情報が重複するため送信しない
    if request.codeIndexMd:
        user_parts.extend([
            "### コード全体の構造 (INDEX.md)\n",
            request.codeIndexMd,
            "",
        ])
    # MAP.jsonはINDEX.mdと情報が重複するため送信しない
    if request.allGroups:
        user_parts.extend([...])  # 変更なし
```

### Step 1-b. Phase 3 のMAP.json送信を除外

対象: `versions/v0.8.2/backend/app/routers/review.py:595-626`（結果統合の全体構造コンテキスト構築）

Step 1-a と同様に、`documentMapJson` と `codeMapJson` のブロックを削除する。

### Step 1-c. プロンプトキャッシング計画との整合

`20260225-prompt-caching-plan.md` ではPhase 2で全体構造情報をキャッシュ対象としている。MAP.json除外によりキャッシュ対象テキストが小さくなるが、INDEX.mdと全グループ一覧は引き続きキャッシュ対象として有効。キャッシング計画の実装時にMAP.jsonが除外済みであることを前提とする。

---

## 施策2: トークン超過エラーの検出と構造化レスポンス

### 概要

LLM APIからのトークン超過エラーを検出し、フロントエンドが適切なUIを表示できるよう構造化されたエラー情報を返す。

### Step 2-a. トークン超過エラー判定関数の追加

対象: `versions/v0.8.2/backend/app/routers/review.py`（ユーティリティ関数）

```python
def _is_token_limit_error(error_message: str) -> bool:
    """LLM APIエラーがトークン上限超過かどうかを判定する"""
    keywords = [
        "too long",          # Anthropic: "prompt is too long"
        "context length",    # OpenAI: "maximum context length"
        "input is too long", # Bedrock
        "token",             # 共通キーワード
        "maximum",           # 共通キーワード
    ]
    msg_lower = error_message.lower()
    return any(kw in msg_lower for kw in keywords)
```

### Step 2-b. GroupReviewResponse にエラー詳細フィールドを追加

対象: `versions/v0.8.2/backend/app/models/schemas.py`（GroupReviewResponse）

```python
class GroupReviewResponse(BaseModel):
    success: bool
    groupId: str = ""
    reviewResult: GroupReviewResult | None = None
    tokensUsed: dict | None = None
    error: str | None = None
    errorCode: str | None = None  # 追加: "token_limit" | "api_error" | None
```

同様に `IntegrateResponse` にも追加:
```python
class IntegrateResponse(BaseModel):
    success: bool
    report: str | None = None
    integratedReport: IntegratedReport | None = None
    reviewMeta: ReviewMeta | None = None
    tokensUsed: dict | None = None
    error: str | None = None
    errorCode: str | None = None  # 追加
```

### Step 2-c. グループレビューのエラーハンドリングを更新

対象: `versions/v0.8.2/backend/app/routers/review.py:500-511`

現在:
```python
except RuntimeError as e:
    return GroupReviewResponse(
        success=False,
        groupId=request.groupId,
        error=str(e),
    )
except Exception as e:
    return GroupReviewResponse(
        success=False,
        groupId=request.groupId,
        error=f"グループレビュー中にエラーが発生しました: {str(e)}",
    )
```

変更後:
```python
except RuntimeError as e:
    error_msg = str(e)
    return GroupReviewResponse(
        success=False,
        groupId=request.groupId,
        error=error_msg,
        errorCode="token_limit" if _is_token_limit_error(error_msg) else "api_error",
    )
except Exception as e:
    error_msg = str(e)
    return GroupReviewResponse(
        success=False,
        groupId=request.groupId,
        error=f"グループレビュー中にエラーが発生しました: {error_msg}",
        errorCode="token_limit" if _is_token_limit_error(error_msg) else None,
    )
```

### Step 2-d. 結果統合のエラーハンドリングを更新

対象: `versions/v0.8.2/backend/app/routers/review.py:671-680`

Step 2-c と同様に `errorCode` を付与する。

### Step 2-e. TypeScript型定義を更新

対象: `versions/v0.8.2/frontend/src/features/reviewer/types/index.ts`

```typescript
export interface GroupReviewResponse {
  success: boolean
  groupId: string
  reviewResult?: GroupReviewResult
  tokensUsed?: { input: number; output: number }
  error?: string
  errorCode?: 'token_limit' | 'api_error'  // 追加
}

export interface IntegrateResponse {
  success: boolean
  report?: string
  integratedReport?: IntegratedReport
  reviewMeta?: ReviewMeta
  tokensUsed?: { input: number; output: number }
  error?: string
  errorCode?: 'token_limit' | 'api_error'  // 追加
}
```

### Step 2-f. GroupReviewState にエラー詳細を追加

対象: `versions/v0.8.2/frontend/src/features/reviewer/types/index.ts`

```typescript
export interface GroupReviewState {
  groupId: string
  groupName: string
  status: GroupReviewStatus
  result?: GroupReviewResult
  tokensUsed?: { input: number; output: number }
  error?: string
  errorCode?: 'token_limit' | 'api_error'  // 追加
}
```

---

## 施策3: 要約API

### 概要

設計書テキスト・コードテキスト・レビュー結果を要約する汎用APIエンドポイントを追加する。フロントエンドからの呼び出し（方式B）で、ユーザーが要約結果をプレビューしてからリトライに使用する。

### Step 3-a. リクエスト/レスポンスのスキーマ定義

対象: `versions/v0.8.2/backend/app/models/schemas.py`

```python
class SummarizeRequest(BaseModel):
    """要約APIのリクエスト"""
    text: str                          # 要約対象テキスト
    targetType: str                    # "design" | "code" | "review_result"
    llmConfig: LLMConfig | None = None # LLM設定

class SummarizeResponse(BaseModel):
    """要約APIのレスポンス"""
    success: bool
    summarizedText: str | None = None
    originalTokens: int | None = None    # 元テキストの推定トークン数
    summarizedTokens: int | None = None  # 要約後の推定トークン数
    tokensUsed: dict | None = None       # LLM消費トークン
    error: str | None = None
```

### Step 3-b. 要約プロンプトの定義

対象: `versions/v0.8.2/backend/app/routers/review.py`（新規関数）

```python
def _build_summarize_prompt(target_type: str) -> tuple[str, str]:
    """要約のシステムプロンプトとユーザーメッセージプレフィックスを構築する"""

    if target_type == "design":
        system = (
            "あなたは設計書を要約する専門家です。\n"
            "設計書の内容を、突合レビューに必要な情報を保ちながら要約してください。"
        )
        instruction = (
            "以下の設計書テキストを要約してください。\n\n"
            "【必ず保持する情報】\n"
            "- 仕様の具体的な値（数値、文字数制限、範囲、閾値）\n"
            "- 条件分岐・判定条件\n"
            "- エラーケース・例外条件\n"
            "- 制約・前提条件\n"
            "- 入出力の項目名と型\n"
            "- 元の行番号参照（Lxx-Lyy）\n\n"
            "【省略してよい情報】\n"
            "- 書式設定や見た目に関する説明\n"
            "- 同じ内容の繰り返し・冗長な説明\n"
            "- 例の詳細展開（代表例1つに集約可）\n\n"
            "【設計書テキスト】\n"
        )
    elif target_type == "code":
        system = (
            "あなたはソースコードを要約する専門家です。\n"
            "コードの内容を、突合レビューに必要な情報を保ちながら要約してください。"
        )
        instruction = (
            "以下のソースコードを要約してください。\n\n"
            "【必ず保持する情報】\n"
            "- 関数/メソッドのシグネチャ（名前、引数、戻り値の型）\n"
            "- バリデーション条件と閾値\n"
            "- 条件分岐のロジック\n"
            "- エラーハンドリング\n"
            "- 重要なビジネスロジック\n"
            "- 元の行番号コメント（// lines: X-Y）\n\n"
            "【省略してよい情報】\n"
            "- import文\n"
            "- getter/setterなどの定型コード\n"
            "- ログ出力\n"
            "- 自明なコメント\n\n"
            "【ソースコード】\n"
        )
    else:  # review_result
        system = (
            "あなたはレビュー結果を要約する専門家です。\n"
            "レビュー結果の内容を、指摘事項を漏れなく保ちながら要約してください。"
        )
        instruction = (
            "以下のレビュー結果を要約してください。\n\n"
            "【必ず保持する情報】\n"
            "- 全ての指摘事項（設計書箇所、コード箇所、問題の内容）\n"
            "- 重要度・深刻度\n"
            "- 対応推奨事項\n"
            "- 申し送り事項\n\n"
            "【省略してよい情報】\n"
            "- 「問題なし」の項目の詳細\n"
            "- 詳細な背景説明\n"
            "- 重複する指摘の2つ目以降\n\n"
            "【レビュー結果】\n"
        )

    return system, instruction
```

### Step 3-c. 要約APIエンドポイントの実装

対象: `versions/v0.8.2/backend/app/routers/review.py`

```python
@router.post("/review/summarize", response_model=SummarizeResponse)
async def summarize_text(request: SummarizeRequest):
    """
    テキスト要約API

    設計書、コード、レビュー結果を要約する。
    トークン上限超過時のリトライで使用される。
    """
    try:
        provider = get_llm_provider(request.llmConfig)

        system_prompt, instruction = _build_summarize_prompt(request.targetType)
        user_message = instruction + request.text

        response_text, input_tokens, output_tokens = provider.send_message(
            system_prompt, user_message
        )

        original_tokens = _estimate_tokens(request.text)
        summarized_tokens = _estimate_tokens(response_text)

        return SummarizeResponse(
            success=True,
            summarizedText=response_text,
            originalTokens=original_tokens,
            summarizedTokens=summarized_tokens,
            tokensUsed={"input": input_tokens, "output": output_tokens},
        )
    except Exception as e:
        return SummarizeResponse(
            success=False,
            error=f"要約中にエラーが発生しました: {str(e)}",
        )
```

### Step 3-d. TypeScript型定義の追加

対象: `versions/v0.8.2/frontend/src/features/reviewer/types/index.ts`

```typescript
export interface SummarizeRequest {
  text: string
  targetType: 'design' | 'code' | 'review_result'
  llmConfig?: LlmConfig
}

export interface SummarizeResponse {
  success: boolean
  summarizedText?: string
  originalTokens?: number
  summarizedTokens?: number
  tokensUsed?: { input: number; output: number }
  error?: string
}
```

### Step 3-e. API呼び出し関数の追加

対象: `versions/v0.8.2/frontend/src/features/reviewer/services/api.ts`

```typescript
export async function executeSummarize(
  request: SummarizeRequest
): Promise<SummarizeResponse> {
  const response = await fetch(`${API_URL}/review/summarize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  return response.json()
}
```

---

## 施策4: Phase 2（グループレビュー）の要約リトライUI

### 概要

グループレビューでエラーが発生した場合に、エラー内容を全体進捗エリアに表示し、要約してからリトライできるUIを提供する。要約結果はStepCardに保持され、リトライ後も参照できる。

### 画面イメージ

#### 全体構成

SplitExecutingScreenは以下の3つのCardで構成される:

```
┌─ Card 1: ヘッダー ─────────────────────────────────────────────────────┐
│  分割レビュー実行中                                           ← 戻る  │
└────────────────────────────────────────────────────────────────────────┘

┌─ Card 2: 全体進捗 + エラー表示 + リトライ設定 ─────────────────────────┐
│  （以下の画面イメージで詳述）                                           │
└────────────────────────────────────────────────────────────────────────┘

┌─ Card 3: 実行ステップ（StepCard一覧）──────────────────────────────────┐
│  （以下の画面イメージで詳述）                                           │
└────────────────────────────────────────────────────────────────────────┘
```

#### Card 2: エラー発生時の全体進捗エリア

エラー内容（APIから返されたエラーメッセージ）をそのまま表示する。
エラー内容の解析は行わない（token_limit判定はerrorCodeで行い、エラー文の解析は不要）。

ラジオボタンには各選択肢のトークン数を表示する:
- 「そのまま」: 元テキストの推定トークン数
- 「要約」: 要約済みなら要約後トークン数、未実行なら「未実行」

```
┌─ Card 2 ───────────────────────────────────────────────────────────────┐
│                                                                        │
│        ✓ 1. 構造マッチング                                             │
│        ⟳ 2. グループレビュー (1/5)                                      │
│        ○ 3. 結果統合                                                   │
│                                                                        │
│  ┌─ エラー ────────────────────────────────────────────────────────┐   │
│  │ グループ「ユーザー管理」のレビューでエラーが発生しました。         │   │
│  │                                                                  │   │
│  │ Anthropic API エラー: prompt is too long: 150000 tokens >        │   │
│  │ 100000 maximum                                                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  [🔄 リトライ]  [⏭ スキップ]                                          │
│    (blue)         (gray)                                               │
│                                                                        │
│  ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──     │
│                                                                        │
│  入力トークン上限で停止した場合、リトライしても同様の結果になる          │
│  可能性があります。先に要約してからリトライしてください。               │
│                                                                        │
│  ┌─ リトライ設定 ──────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │  ⚠ 注意: 要約によって微妙なニュアンスや制約が失われることがある   │   │
│  │  ため、品質検証が必要です。本番投入前に出力の比較テストを行うこと │   │
│  │  を強くお勧めします。                                             │   │
│  │                                                                  │   │
│  │  設計書                                                           │   │
│  │  ◉ そのまま（~15,000 トークン）  ○ 要約（未実行）                │   │
│  │                                                                  │   │
│  │  プログラム                                                       │   │
│  │  ◉ そのまま（~25,000 トークン）  ○ 要約（未実行）                │   │
│  │                                                                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

#### 「要約」を選択した場合（要約未実行）

「要約」を選択した項目がある場合、リトライ設定パネル内に「選択した要約を実行」ボタンが表示される。
リトライボタンの下に注意メッセージを表示する。

```
│  ┌─ リトライ設定 ──────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │  ⚠ 注意: ...                                                    │   │
│  │                                                                  │   │
│  │  設計書                                                           │   │
│  │  ○ そのまま（~15,000 トークン）  ◉ 要約（未実行）                │   │
│  │                                                                  │   │
│  │  プログラム                                                       │   │
│  │  ◉ そのまま（~25,000 トークン）  ○ 要約（未実行）                │   │
│  │                                                                  │   │
│  │  [選択した要約を実行]  ← 未要約の「要約」選択項目をまとめて実行   │   │
│  │   (blue/small)                                                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  [🔄 リトライ] ← disabled  [⏭ スキップ]                               │
│  ⚠ 要約が選択されていますが未実行です。要約を実行してください。         │
```

#### 要約実行中

```
│  │  設計書                                                           │   │
│  │  ○ そのまま（~15,000 トークン）  ◉ 要約（⟳ 要約中...）          │   │
│  │                                                                  │   │
│  │  プログラム                                                       │   │
│  │  ◉ そのまま（~25,000 トークン）  ○ 要約（未実行）                │   │
│  │                                                                  │   │
│  │  [選択した要約を実行] ← disabled（実行中）                        │   │
```

#### 要約完了（プレビュー表示）

要約結果はアコーディオンで展開表示する。トークン数が要約後の値に更新される。

```
│  ┌─ リトライ設定 ──────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │  ⚠ 注意: ...                                                    │   │
│  │                                                                  │   │
│  │  設計書                                                           │   │
│  │  ○ そのまま（~15,000 トークン）  ◉ 要約（~5,200 トークン 65%削減）│   │
│  │  ▼ 要約結果を表示                                                │   │
│  │  ┌────────────────────────────────────────────────────────────┐ │   │
│  │  │ # チェック条件表                                            │ │   │
│  │  │                                                              │ │   │
│  │  │ ## 入力項目 (L6-L18)                                        │ │   │
│  │  │ - ユーザーID: 必須、20文字以内、半角英数字                    │ │   │
│  │  │ - メールアドレス: 必須、RFC5322形式                           │ │   │
│  │  │ - 年齢: 0以上150以下                                         │ │   │
│  │  │ ...                                                          │ │   │
│  │  └────────────────────────────────────────────────────────────┘ │   │
│  │   (max-height: 200px, overflow-y: auto, bg-gray-50, border)      │   │
│  │                                                                  │   │
│  │  プログラム                                                       │   │
│  │  ◉ そのまま（~25,000 トークン）  ○ 要約（未実行）                │   │
│  │                                                                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  [🔄 リトライ]  [⏭ スキップ]                                          │
│    (blue)         (gray)                                               │
```

#### 両方要約完了

```
│  ┌─ リトライ設定 ──────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │  ⚠ 注意: ...                                                    │   │
│  │                                                                  │   │
│  │  設計書                                                           │   │
│  │  ○ そのまま（~15,000 トークン）  ◉ 要約（~5,200 トークン 65%削減）│   │
│  │  ▶ 要約結果を表示                                                │   │
│  │                                                                  │   │
│  │  プログラム                                                       │   │
│  │  ○ そのまま（~25,000 トークン）  ◉ 要約（~9,800 トークン 61%削減）│   │
│  │  ▶ 要約結果を表示                                                │   │
│  │                                                                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  [🔄 リトライ]  [⏭ スキップ]                                          │
│    (blue)         (gray)                                               │
```

#### 「そのまま」に戻した場合

要約済みでも「そのまま」に切り替えられる。要約結果は保持される（再度「要約」に切り替えると再表示）。

```
│  │  設計書                                                           │   │
│  │  ◉ そのまま（~15,000 トークン）  ○ 要約（~5,200 トークン 65%削減）│   │
```

### 画面イメージ: StepCard内のエラーと要約結果の保持

リトライ実行後も、StepCardに要約結果を保持する。ステータスが `error` → `in_progress` → `completed` と変わっても、要約情報は消えない。

#### リトライ後に完了した場合

```
┌─ 2.1  ユーザー管理 ────────────────── ✓ 完了 ──────────── ▼ ─┐
│                                                                │
│  設計書: チェック条件表、入力仕様                                  │
│  プログラム: UserManagementService#registerUser、...              │
│                                                                │
│  ──────────────────────────────────────────                    │
│  レビュー結果（要約版の設計書でレビュー実施）:                     │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ ## サマリー                                              │   │
│  │ ...（レビュー結果のプレビュー）                            │   │
│  └────────────────────────────────────────────────────────┘   │
│   (max-height: 160px, overflow-y: auto)                        │
│                                                                │
│  ▶ 使用した設計書の要約を表示                                    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

#### エラー中のStepCard

```
┌─ 2.1  ユーザー管理 ────────────────── ⚠ エラー ──────────── ▼ ─┐
│                                                                  │
│  設計書: チェック条件表、入力仕様                                    │
│  プログラム: UserManagementService#registerUser、...                │
│                                                                  │
│  ──────────────────────────────────────────                      │
│  エラー: Anthropic API エラー: prompt is too long:                 │
│  150000 tokens > 100000 maximum                                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Step 4-a. フロントエンドにトークン推定関数を追加

対象: `versions/v0.8.2/frontend/src/features/reviewer/utils/`（新規ファイル `tokenEstimate.ts`）

```typescript
/**
 * 簡易トークン数推定（バックエンドの _estimate_tokens と同じロジック）
 */
export function estimateTokens(text: string): number {
  let japaneseChars = 0
  for (const char of text) {
    if (char.codePointAt(0)! > 0x3000) {
      japaneseChars++
    }
  }
  const otherChars = text.length - japaneseChars
  return Math.floor(japaneseChars * 1.5 + otherChars * 0.25)
}
```

### Step 4-b. GroupReviewState に要約状態を追加

対象: `versions/v0.8.2/frontend/src/features/reviewer/types/index.ts`

```typescript
export interface GroupSummarizeState {
  documentSummarized?: string   // 設計書の要約結果テキスト
  codeSummarized?: string       // コードの要約結果テキスト
  documentOriginalTokens?: number
  documentSummarizedTokens?: number
  codeOriginalTokens?: number
  codeSummarizedTokens?: number
}

export interface GroupReviewState {
  groupId: string
  groupName: string
  status: GroupReviewStatus
  result?: GroupReviewResult
  tokensUsed?: { input: number; output: number }
  error?: string
  errorCode?: 'token_limit' | 'api_error'
  summarizeState?: GroupSummarizeState  // 追加: 要約情報（リトライ後も保持）
  usedSummarizedDoc?: boolean  // 追加: 要約版設計書でレビューしたか
  usedSummarizedCode?: boolean // 追加: 要約版コードでレビューしたか
}
```

### Step 4-c. SplitExecutingScreen のエラー表示を拡張

対象: `versions/v0.8.2/frontend/src/features/reviewer/components/SplitExecutingScreen.tsx:184-212`

変更後:
```tsx
{isErrorPaused && (() => {
  const errorGroup = state.groupReviews.find((g) => g.status === 'error')
  if (!errorGroup) return null
  return (
    <>
      {/* エラー内容をそのまま表示 */}
      <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md text-left">
        <p className="text-sm font-medium text-red-800">
          グループ「{errorGroup.groupName}」のレビューでエラーが発生しました。
        </p>
        <p className="text-sm text-red-700 mt-1">{errorGroup.error}</p>
      </div>

      {/* リトライ / スキップ ボタン */}
      <div className="flex items-center justify-center gap-3 mt-3">
        <button onClick={() => onRetryGroup(errorGroup.groupId)} disabled={retryDisabled}>
          リトライ
        </button>
        <button onClick={() => onSkipGroup(errorGroup.groupId)}>
          スキップ
        </button>
      </div>

      {/* 要約未実行の注意メッセージ（リトライボタンの下に表示） */}
      {retryDisabled && hasPendingSummarize && (
        <p className="text-sm text-amber-600 mt-2 text-center">
          ⚠ 要約が選択されていますが未実行です。要約を実行してください。
        </p>
      )}

      {/* 要約案内 + リトライ設定 */}
      <div className="mt-4 pt-4 border-t">
        <p className="text-sm text-gray-600">
          入力トークン上限で停止した場合、リトライしても同様の結果になる
          可能性があります。先に要約してからリトライしてください。
        </p>
        <RetrySettingsPanel
          groupId={errorGroup.groupId}
          documentContent={currentDocumentContent}
          codeContent={currentCodeContent}
          summarizeState={errorGroup.summarizeState}
          llmConfig={llmConfig}
          onSummarizeComplete={onSummarizeComplete}
        />
      </div>
    </>
  )
})()}
```

### Step 4-d. RetrySettingsPanel コンポーネントの新規作成

対象: `versions/v0.8.2/frontend/src/features/reviewer/components/RetrySettingsPanel.tsx`（新規）

設計書・コードそれぞれの「そのまま/要約」選択、一括要約実行ボタン、要約結果プレビューを管理するコンポーネント。パネル先頭に注意文を表示する。

```tsx
{/* 注意文 */}
<div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-md">
  <p className="text-sm text-amber-800">
    <span className="font-medium">⚠ 注意:</span>{' '}
    要約によって微妙なニュアンスや制約が失われることがあるため、品質検証が必要です。
    本番投入前に出力の比較テストを行うことを強くお勧めします。
  </p>
</div>
```

```typescript
interface RetrySettingsPanelProps {
  groupId: string
  documentContent: string
  codeContent: string
  summarizeState?: GroupSummarizeState
  llmConfig?: LlmConfig
  onSummarizeComplete: (groupId: string, state: GroupSummarizeState) => void
}
```

内部状態:
```typescript
// 設計書: 'original' | 'summarize'
const [docMode, setDocMode] = useState<'original' | 'summarize'>('original')
// コード: 'original' | 'summarize'
const [codeMode, setCodeMode] = useState<'original' | 'summarize'>('original')
// 要約実行中フラグ（設計書・コードそれぞれ）
const [docSummarizing, setDocSummarizing] = useState(false)
const [codeSummarizing, setCodeSummarizing] = useState(false)
// 要約結果プレビューの開閉
const [docPreviewOpen, setDocPreviewOpen] = useState(false)
const [codePreviewOpen, setCodePreviewOpen] = useState(false)
```

「選択した要約を実行」ボタンの処理:
```typescript
const handleExecuteSummarize = async () => {
  // 「要約」選択かつ未要約の項目のみ対象
  const targets: Array<{ type: 'design' | 'code'; text: string }> = []
  if (docMode === 'summarize' && !summarizeState?.documentSummarized) {
    targets.push({ type: 'design', text: documentContent })
  }
  if (codeMode === 'summarize' && !summarizeState?.codeSummarized) {
    targets.push({ type: 'code', text: codeContent })
  }

  // 並列でAPI呼び出し
  await Promise.all(targets.map(async (t) => {
    if (t.type === 'design') setDocSummarizing(true)
    else setCodeSummarizing(true)

    const response = await executeSummarize({
      text: t.text,
      targetType: t.type,
      llmConfig: llmConfig || undefined,
    })
    // summarizeState を更新...

    if (t.type === 'design') setDocSummarizing(false)
    else setCodeSummarizing(false)
  }))
}
```

「選択した要約を実行」ボタンの表示条件:
- `docMode === 'summarize'` かつ未要約、または `codeMode === 'summarize'` かつ未要約の場合に表示

リトライボタンのdisabled判定:
- `docMode === 'summarize'` かつ要約未完了 → disabled
- `codeMode === 'summarize'` かつ要約未完了 → disabled

リトライボタン下の注意メッセージ表示条件:
- 上記 disabled 条件に該当する場合のみ「⚠ 要約が選択されていますが未実行です。要約を実行してください。」を表示

### Step 4-e. index.tsx のリトライハンドラーを拡張

対象: `versions/v0.8.2/frontend/src/features/reviewer/index.tsx`

グループレビューのエラー処理ループに「要約情報付きリトライ」を追加する。

```typescript
// エラーアクション型の拡張
type ErrorAction =
  | { action: 'retry'; groupId: string }
  | { action: 'skip'; groupId: string }

// リトライ時: GroupReviewState.summarizeState と docMode/codeMode を参照
// docMode === 'summarize' && summarizeState.documentSummarized → 要約版で差替え
// codeMode === 'summarize' && summarizeState.codeSummarized → 要約版で差替え
```

`retry` アクション時に、SplitExecutingScreen から現在の docMode/codeMode と要約結果を受け取り、適宜差し替えてリトライする:

```typescript
// リトライ時のコンテンツ決定
const retryDocContent = (docMode === 'summarize' && summarizeState?.documentSummarized)
  ? summarizeState.documentSummarized
  : documentContent
const retryCodeContent = (codeMode === 'summarize' && summarizeState?.codeSummarized)
  ? summarizeState.codeSummarized
  : codeContent

// GroupReviewState に使用した要約情報を記録
groupReviewResults[i] = {
  ...groupReviewResults[i],
  usedSummarizedDoc: docMode === 'summarize',
  usedSummarizedCode: codeMode === 'summarize',
}
```

### Step 4-f. SplitExecutingScreen の StepCard に要約情報を表示

対象: `versions/v0.8.2/frontend/src/features/reviewer/components/SplitExecutingScreen.tsx`（StepCard内のcompletedステータス表示）

レビュー完了時に、要約版を使用したことを表示する:

```tsx
{status === 'completed' && result && (
  <div className="mt-2 pt-2 border-t">
    {(reviewState?.usedSummarizedDoc || reviewState?.usedSummarizedCode) && (
      <p className="text-xs text-amber-600 mb-2">
        {reviewState.usedSummarizedDoc && reviewState.usedSummarizedCode
          ? '要約版の設計書・コードでレビューを実施しました'
          : reviewState.usedSummarizedDoc
            ? '要約版の設計書でレビューを実施しました'
            : '要約版のコードでレビューを実施しました'}
      </p>
    )}
    <div className="text-gray-700 text-xs whitespace-pre-wrap max-h-40 overflow-y-auto">
      {result.report}
    </div>
    {/* 使用した要約テキストのプレビュー（アコーディオン） */}
    {reviewState?.usedSummarizedDoc && reviewState?.summarizeState?.documentSummarized && (
      <SummarizedTextPreview
        label="使用した設計書の要約を表示"
        text={reviewState.summarizeState.documentSummarized}
      />
    )}
    {reviewState?.usedSummarizedCode && reviewState?.summarizeState?.codeSummarized && (
      <SummarizedTextPreview
        label="使用したコードの要約を表示"
        text={reviewState.summarizeState.codeSummarized}
      />
    )}
  </div>
)}
```

### Step 4-g. SplitExecutingScreen のプロパティ拡張

対象: `versions/v0.8.2/frontend/src/features/reviewer/components/SplitExecutingScreen.tsx`

```typescript
interface SplitExecutingScreenProps {
  state: SplitReviewState
  onBack: () => void
  onRetryStructureMatching: () => void
  onRetryGroup: (groupId: string) => void
  onSkipGroup: (groupId: string) => void
  onRetryIntegrate: () => void
  // 追加
  currentDocumentContent?: string  // エラー中のグループの設計書内容
  currentCodeContent?: string      // エラー中のグループのコード内容
  llmConfig?: LlmConfig
  onSummarizeComplete?: (groupId: string, state: GroupSummarizeState) => void
  retryDocMode?: 'original' | 'summarize'  // リトライ時に参照
  retryCodeMode?: 'original' | 'summarize' // リトライ時に参照
}
```

---

## 施策5: Phase 3（結果統合）の要約リトライUI

### 概要

Phase 3（結果統合）でトークン超過エラーが発生した場合、各グループのレビュー結果を要約してからリトライできるようにする。

### 画面イメージ

Phase 3 の入力は「各グループのレビュー結果（Markdown）」であるため、Phase 2 とは要約対象が異なる。各グループごとに「そのまま/要約」を選択し、「選択した要約を実行」で一括要約する。

#### 統合エラー発生時

```
┌─ Card 2 ───────────────────────────────────────────────────────────────┐
│                                                                        │
│        ✓ 1. 構造マッチング                                             │
│        ✓ 2. グループレビュー (5/5)                                      │
│        ⚠ 3. 結果統合                                                   │
│                                                                        │
│  ┌─ エラー ────────────────────────────────────────────────────────┐   │
│  │ 結果統合でエラーが発生しました。                                   │   │
│  │                                                                  │   │
│  │ Bedrock API エラー: Input is too long for requested model.       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  [🔄 リトライ]                                                         │
│    (blue)                                                              │
│                                                                        │
│  ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──     │
│                                                                        │
│  入力トークン上限で停止した場合、リトライしても同様の結果になる          │
│  可能性があります。先に各グループのレビュー結果を要約してから            │
│  リトライしてください。                                                │
│                                                                        │
│  ┌─ リトライ設定 ──────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │  ⚠ 注意: 要約によって微妙なニュアンスや制約が失われることがある   │   │
│  │  ため、品質検証が必要です。本番投入前に出力の比較テストを行うこと │   │
│  │  を強くお勧めします。                                             │   │
│  │                                                                  │   │
│  │  ユーザー管理                                                     │   │
│  │  ◉ そのまま（~8,000 トークン）  ○ 要約（未実行）                 │   │
│  │                                                                  │   │
│  │  認証処理                                                         │   │
│  │  ◉ そのまま（~12,000 トークン）  ○ 要約（未実行）                │   │
│  │                                                                  │   │
│  │  データアクセス                                                    │   │
│  │  ◉ そのまま（~6,000 トークン）  ○ 要約（未実行）                 │   │
│  │                                                                  │   │
│  │  バリデーション                                                    │   │
│  │  ◉ そのまま（~4,000 トークン）  ○ 要約（未実行）                 │   │
│  │                                                                  │   │
│  │  エラーハンドリング                                                │   │
│  │  ◉ そのまま（~7,000 トークン）  ○ 要約（未実行）                 │   │
│  │                                                                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

#### 「要約」を選択した場合（要約未実行）

「要約」を選択したグループがある場合、「選択した要約を実行」ボタンが表示される。
リトライボタンは要約完了まで disabled。注意メッセージはリトライボタンの下に表示。

```
│  │  ユーザー管理                                                     │   │
│  │  ○ そのまま（~8,000 トークン）  ◉ 要約（未実行）                 │   │
│  │                                                                  │   │
│  │  認証処理                                                         │   │
│  │  ○ そのまま（~12,000 トークン）  ◉ 要約（未実行）                │   │
│  │                                                                  │   │
│  │  データアクセス                                                    │   │
│  │  ◉ そのまま（~6,000 トークン）  ○ 要約（未実行）                 │   │
│  │                                                                  │   │
│  │  バリデーション                                                    │   │
│  │  ◉ そのまま（~4,000 トークン）  ○ 要約（未実行）                 │   │
│  │                                                                  │   │
│  │  エラーハンドリング                                                │   │
│  │  ○ そのまま（~7,000 トークン）  ◉ 要約（未実行）                 │   │
│  │                                                                  │   │
│  │  [選択した要約を実行]  ← 未要約の「要約」選択グループをまとめて実行 │   │
│  │   (blue/small)                                                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  [🔄 リトライ] ← disabled                                              │
│  ⚠ 要約が選択されていますが未実行です。要約を実行してください。         │
```

#### 要約実行中

APIは1グループごとに呼び出す（並列実行可）。

```
│  │  ユーザー管理                                                     │   │
│  │  ○ そのまま（~8,000 トークン）  ◉ 要約（⟳ 要約中...）           │   │
│  │                                                                  │   │
│  │  認証処理                                                         │   │
│  │  ○ そのまま（~12,000 トークン）  ◉ 要約（⟳ 要約中...）          │   │
│  │                                                                  │   │
│  │  データアクセス                                                    │   │
│  │  ◉ そのまま（~6,000 トークン）  ○ 要約（未実行）                 │   │
│  │                                                                  │   │
│  │  ...                                                              │   │
│  │                                                                  │   │
│  │  エラーハンドリング                                                │   │
│  │  ○ そのまま（~7,000 トークン）  ◉ 要約（⟳ 要約中...）           │   │
│  │                                                                  │   │
│  │  [選択した要約を実行] ← disabled（実行中）                        │   │
```

#### 要約完了（プレビュー表示）

要約結果はアコーディオンで展開表示する。トークン数が要約後の値に更新される。

```
│  ┌─ リトライ設定 ──────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │  ⚠ 注意: ...                                                    │   │
│  │                                                                  │   │
│  │  ユーザー管理                                                     │   │
│  │  ○ そのまま（~8,000 トークン）  ◉ 要約（~3,200 トークン 60%削減）│   │
│  │  ▶ 要約結果を表示                                                │   │
│  │                                                                  │   │
│  │  認証処理                                                         │   │
│  │  ○ そのまま（~12,000 トークン）  ◉ 要約（~4,500 トークン 63%削減）│   │
│  │  ▶ 要約結果を表示                                                │   │
│  │                                                                  │   │
│  │  データアクセス                                                    │   │
│  │  ◉ そのまま（~6,000 トークン）  ○ 要約（未実行）                 │   │
│  │                                                                  │   │
│  │  バリデーション                                                    │   │
│  │  ◉ そのまま（~4,000 トークン）  ○ 要約（未実行）                 │   │
│  │                                                                  │   │
│  │  エラーハンドリング                                                │   │
│  │  ○ そのまま（~7,000 トークン）  ◉ 要約（~2,800 トークン 60%削減）│   │
│  │  ▶ 要約結果を表示                                                │   │
│  │                                                                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  [🔄 リトライ]  ← 「要約」選択グループが全て要約済みなので active       │
```

#### 追加で別のグループも要約する場合

要約済みグループの選択を変更しても、要約結果は保持される。
新たに「要約」を選択したグループがある場合のみ「選択した要約を実行」ボタンが再表示される。
既に要約済みのグループは再実行しない。

```
│  │  バリデーション                                                    │   │
│  │  ○ そのまま（~4,000 トークン）  ◉ 要約（未実行）  ← 新たに変更   │   │
│  │                                                                  │   │
│  │  [選択した要約を実行]  ← バリデーションのみ実行（他は要約済み）     │   │
│  │   (blue/small)                                                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  [🔄 リトライ] ← disabled                                              │
│  ⚠ 要約が選択されていますが未実行です。要約を実行してください。         │
```

### Step 5-a. IntegrateSummarizeState の型定義

対象: `versions/v0.8.2/frontend/src/features/reviewer/types/index.ts`

```typescript
export interface IntegrateGroupSummarizeEntry {
  groupId: string
  mode: 'original' | 'summarize'
  summarizedReport?: string       // 要約結果テキスト
  originalTokens?: number
  summarizedTokens?: number
}

export interface IntegrateSummarizeState {
  groups: IntegrateGroupSummarizeEntry[]
}
```

### Step 5-b. IntegrateRetrySettingsPanel コンポーネントの新規作成

対象: `versions/v0.8.2/frontend/src/features/reviewer/components/IntegrateRetrySettingsPanel.tsx`（新規）

Phase 2 の RetrySettingsPanel と同様の構成だが、要約対象が複数グループの `report` になる。

```typescript
interface IntegrateRetrySettingsPanelProps {
  groupReviews: GroupReviewState[]       // 完了済みグループ一覧
  summarizeState: IntegrateSummarizeState
  llmConfig?: LlmConfig
  onSummarizeComplete: (state: IntegrateSummarizeState) => void
}
```

内部状態:
```typescript
// 各グループのモード（初期値: 全て 'original'）
const [groupModes, setGroupModes] = useState<Record<string, 'original' | 'summarize'>>({})
// 要約実行中のグループID
const [summarizingGroupIds, setSummarizingGroupIds] = useState<Set<string>>(new Set())
// 要約結果プレビューの開閉
const [previewOpen, setPreviewOpen] = useState<Record<string, boolean>>({})
```

「選択した要約を実行」ボタンの処理:
```typescript
const handleExecuteSummarize = async () => {
  // 「要約」選択かつ未要約のグループのみ対象
  const targets = groupReviews.filter((g) =>
    groupModes[g.groupId] === 'summarize' &&
    !summarizeState.groups.find((s) => s.groupId === g.groupId)?.summarizedReport
  )

  setSummarizingGroupIds(new Set(targets.map((g) => g.groupId)))

  // 並列でAPI呼び出し（1グループ1リクエスト）
  const results = await Promise.all(
    targets.map(async (g) => {
      const response = await executeSummarize({
        text: g.result!.report,
        targetType: 'review_result',
        llmConfig: llmConfig || undefined,
      })
      return {
        groupId: g.groupId,
        summarizedReport: response.summarizedText,
        originalTokens: response.originalTokens,
        summarizedTokens: response.summarizedTokens,
      }
    })
  )

  // summarizeState を更新（既存の要約結果は保持）
  // ...
  setSummarizingGroupIds(new Set())
}
```

リトライボタンの disabled 判定:
- `mode === 'summarize'` かつ `summarizedReport` が未設定のグループが1つでもあれば disabled

### Step 5-c. SplitExecutingScreen の統合エラー表示を拡張

対象: `versions/v0.8.2/frontend/src/features/reviewer/components/SplitExecutingScreen.tsx:214-229`（統合エラー表示部分）

グループレビュー（施策4）と同様のパターンで、エラー内容 + リトライボタン + 案内文 + IntegrateRetrySettingsPanel を表示する。

### Step 5-d. index.tsx の統合リトライハンドラーを拡張

対象: `versions/v0.8.2/frontend/src/features/reviewer/index.tsx`（`handleRetryIntegrate`）

リトライ時に、各グループの `mode` に応じて `report` を差し替える:

```typescript
const groupReviewSummaries = completedGroupReviews.map((g) => {
  const entry = integrateSummarizeState.groups.find((s) => s.groupId === g.groupId)
  const useSummarized = entry?.mode === 'summarize' && entry?.summarizedReport
  return {
    groupId: g.groupId,
    groupName: g.groupName,
    report: useSummarized ? entry.summarizedReport! : g.result!.report,
  }
})

// 統合APIを再呼び出し
await executeIntegrate({
  structureMatching: structureMatchingResult,
  groupReviews: groupReviewSummaries,
  // ...
})
```

---

## 影響ファイル一覧

| ファイル | 施策 | 変更内容 |
|---------|------|---------|
| `versions/v0.8.2/backend/app/routers/review.py` | 1, 2, 3 | MAP.json送信除外、トークン超過判定、要約APIエンドポイント追加 |
| `versions/v0.8.2/backend/app/models/schemas.py` | 2, 3 | errorCode追加、SummarizeRequest/Response追加 |
| `versions/v0.8.2/frontend/src/features/reviewer/types/index.ts` | 2, 3, 4, 5 | errorCode追加、Summarize型追加、ErrorAction拡張、IntegrateSummarizeState追加 |
| `versions/v0.8.2/frontend/src/features/reviewer/services/api.ts` | 3 | executeSummarize関数追加 |
| `versions/v0.8.2/frontend/src/features/reviewer/utils/tokenEstimate.ts` | 4 | トークン推定関数（新規） |
| `versions/v0.8.2/frontend/src/features/reviewer/components/RetrySettingsPanel.tsx` | 4 | Phase 2 リトライ設定パネル（新規） |
| `versions/v0.8.2/frontend/src/features/reviewer/components/IntegrateRetrySettingsPanel.tsx` | 5 | Phase 3 リトライ設定パネル（新規） |
| `versions/v0.8.2/frontend/src/features/reviewer/components/SplitExecutingScreen.tsx` | 4, 5 | エラー表示拡張、リトライ設定パネル組み込み |
| `versions/v0.8.2/frontend/src/features/reviewer/index.tsx` | 4, 5 | リトライハンドラー拡張 |
| `versions/v0.8.2/spec.md` | 1, 2, 3 | 仕様更新 |

---

## 品質への影響と注意事項

### 施策1（MAP.json除外）の影響

- **影響: 低** — INDEX.mdが同等の情報を含むため、AIの構造把握能力に変化なし
- 検証: MAP.json除外前後で、同一入力に対するグループレビュー結果を比較する

### 施策3-4（設計書/コードの要約）の影響

- **影響: 中〜高** — 突合レビューの片方または両方が要約版になるため、以下の指摘が減少する可能性がある:
  - 数値条件・境界値の不一致
  - エッジケースの未実装
  - エラーハンドリングの漏れ

- **ユーザーへの注意表示**（RetrySettingsPanelの先頭に表示）:
  ```
  ⚠ 注意: 要約によって微妙なニュアンスや制約が失われることがあるため、
  品質検証が必要です。本番投入前に出力の比較テストを行うことを強くお勧めします。
  ```

### 施策5（レビュー結果の要約）の影響

- **影響: 低〜中** — レビュー結果の要約は指摘事項のリストを保持する方針のため、主要な指摘は維持される
- 詳細な文脈やニュアンスは失われる可能性がある

---

## 実装順序

1. **施策1**（MAP.json除外） — 単独で完結。即効性がありリスクが低い
2. **施策2**（エラー検出） — 施策4/5の前提
3. **施策3**（要約API） — 施策4/5の前提
4. **施策4**（Phase 2 リトライUI） — 主要機能
5. **施策5**（Phase 3 リトライUI） — Phase 2と同パターンのため追加コストは小さい

---

## 試験項目表

### A. 施策1: 全体構造情報のスリム化

- [ ] Phase 2 で全体構造コンテキストにMAP.jsonが含まれないこと（バックエンドログで確認）
- [ ] Phase 2 で全体構造コンテキストにINDEX.mdと全グループ一覧が引き続き含まれること
- [ ] Phase 3 で全体構造コンテキストにMAP.jsonが含まれないこと
- [ ] MAP.json除外前後で、同一入力のレビュー結果に大きな品質差がないこと
- [ ] Phase 1（構造マッチング）のMAP.json入力は変更されていないこと

### B. 施策2: トークン超過エラー検出

- [ ] Anthropicのトークン超過エラーで `errorCode: "token_limit"` が返ること
- [ ] OpenAIのトークン超過エラーで `errorCode: "token_limit"` が返ること
- [ ] Bedrockのトークン超過エラーで `errorCode: "token_limit"` が返ること
- [ ] トークン超過以外のエラー（ネットワーク、認証等）で `errorCode` が `"token_limit"` にならないこと

### C. 施策3: 要約API

- [ ] 設計書テキストの要約が正常に実行されること
- [ ] コードテキストの要約が正常に実行されること
- [ ] レビュー結果の要約が正常に実行されること
- [ ] 要約結果に元テキストの行番号参照が保持されていること
- [ ] originalTokens / summarizedTokens が正しく計算されること
- [ ] LLM設定（provider/model）が正しく適用されること

### D. 施策4: Phase 2 リトライUI

- [ ] トークン超過エラー時に「要約してリトライ」ボタンが表示されること
- [ ] トークン超過以外のエラー時は「要約してリトライ」が表示されないこと
- [ ] トークンの内訳（設計書/コード）が正しく表示されること
- [ ] 設計書のみ要約してリトライできること
- [ ] コードのみ要約してリトライできること
- [ ] 両方要約してリトライできること
- [ ] 要約結果のプレビューが表示されること
- [ ] 要約後のトークン削減率が表示されること
- [ ] 「そのままリトライ」が従来通り動作すること
- [ ] 「スキップ」が従来通り動作すること
- [ ] 注意事項（精度低下の可能性）が表示されること

### E. 施策5: Phase 3 リトライUI

- [ ] 統合でトークン超過エラー時に「各結果を要約してリトライ」ボタンが表示されること
- [ ] 各グループのトークン内訳が表示されること
- [ ] 要約済みレビュー結果で統合が正常に完了すること

### F. 回帰テスト

- [ ] 一括レビューが従来通り動作すること
- [ ] 分割レビューの正常フロー（エラーなし）が従来通り動作すること
- [ ] 構造マッチングが従来通り動作すること（MAP.json入力は変更なし）
- [ ] グループレビューのリトライ・スキップが従来通り動作すること
