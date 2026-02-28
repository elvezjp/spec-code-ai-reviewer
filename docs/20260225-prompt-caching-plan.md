# プロンプトキャッシング導入計画

- 作成日: 2026/02/25
- 対象バージョン: v0.8.2（分割レビュー機能）
- ステータス: 調査・計画

** 本件は調査のみで対応は見送り **

## 1. 背景と目的

### 課題

分割レビューでは3つのフェーズ（構造マッチング→グループレビュー→結果統合）でLLMを呼び出すが、特にフェーズ2（グループレビュー）では**複数のグループに対して同じシステムプロンプトと全体構造コンテキストを繰り返し送信**しており、トークン消費とコストが増大している。

また、一部のグループレビューや統合レビューがLLMモデルの入力トークン上限に達してしまうことがある。

### 目的

プロンプトキャッシングを導入し、以下を実現する:

1. **コスト削減**: キャッシュ読取は通常入力の10%のコスト（最大90%割引）
2. **レイテンシ改善**: キャッシュヒット時はプレフィル処理をスキップ

### 入力トークン上限に関する調査結果

プロンプトキャッシングはコストとレイテンシの最適化であり、**入力トークン上限（コンテキストウィンドウ）の問題は解決しない**。キャッシュの有無に関わらず、全てのトークンがモデルに送信され、コンテキストウィンドウに対してはキャッシュされたトークンも通常通りカウントされる。

入力トークン上限の問題を解決するには、キャッシングとは別に以下のようなアプローチが必要:

- グループレビュー時に渡す全体構造情報の量を削減・要約する
- 全体構造情報のうち、対象グループに関連性の高い部分のみを選択的に含める
- より大きなコンテキストウィンドウを持つモデルを使用する

## 2. 分割レビューにおけるキャッシュ対象分析

### キャッシュの前提: プレフィックス一致

全プロバイダー共通で、キャッシュは**先頭からのトークン列の連続一致（プレフィックス一致）**で動作する。途中で1トークンでも異なると、そこから先は全てキャッシュが使えない。

```
リクエスト1: [A][B][C][D][E][F]
リクエスト2: [A][B][C][X][Y][Z]
                       ↑ ここで不一致
             ├─一致──┤├─不一致─┤
             キャッシュ可  通常処理
```

このため、キャッシュの恩恵を受けるには**全グループ共通の内容をプロンプトの先頭に配置**する必要がある。

現在の実装では全体構造情報がユーザーメッセージの**末尾**にあるため、先頭がグループ固有の内容となり、1トークン目から不一致となってキャッシュが一切効かない。順序を入れ替える必要がある。

```
現在（キャッシュ不可）:  [グループ固有の内容][全体構造情報（共通）]
                        ↑ 先頭から異なるため全て通常処理

変更後（キャッシュ可能）: [全体構造情報（共通）][グループ固有の内容]
                        ├──キャッシュ読取──┤├──通常処理──┤
```

### フェーズ2（グループレビュー）— 最も効果が大きい

グループレビューでは、N個のグループに対して以下が**全グループ共通**:

| 項目 | 内容 | 推定トークン |
|------|------|-------------|
| システムプロンプト | role, purpose, output_format, notes | 500〜2,000 |
| 全体構造（INDEX.md / MAP.json） | documentIndexMd, codeIndexMd, documentMapJson, codeMapJson | 2,000〜20,000 |
| 全グループ一覧テーブル | allGroups | 500〜2,000 |

**グループ固有**の部分（キャッシュ対象外）:
- グループ名・ID
- documentContent（設計書の実際の内容）
- codeContent（コードの実際の内容）

**キャッシュ効果の試算**（例: 5グループ、共通コンテキスト10,000トークンの場合）:
- キャッシュなし: 5 × 10,000 = 50,000トークン（通常料金）
- キャッシュあり: 10,000（書込1.25倍）+ 4 × 10,000（読取0.1倍）= 12,500 + 4,000 = 16,500トークン相当のコスト
- **約67%のコスト削減**

### フェーズ3（結果統合）— 効果は限定的

統合は1回の呼び出しのため、フェーズ2でキャッシュした内容の一部（全体構造情報）が再利用できる可能性はあるが、システムプロンプトが異なるため効果は限定的。

### フェーズ1（構造マッチング）— 効果なし

1回の呼び出しのためキャッシュの恩恵なし。

## 3. プロバイダー別 プロンプトキャッシング仕様

### 3.1 Anthropic API

| 項目 | 内容 |
|------|------|
| 有効化方法 | `cache_control: {"type": "ephemeral"}` を content block に付与 |
| 対象 | system, messages, tools の content blocks |
| 最小トークン数 | Opus 4.5/4.6: 4,096 / Sonnet: 1,024 / Haiku 4.5: 4,096 / Haiku 3.5: 2,048 |
| TTL | 5分（デフォルト）/ 1時間（`ttl: "1h"`） |
| 最大ブレークポイント | 4個/リクエスト |
| キャッシュ書込コスト | 通常入力の1.25倍 |
| キャッシュ読取コスト | 通常入力の0.1倍（90%割引） |
| 条件 | 完全なプレフィックス一致が必要 |

#### 現在の実装（anthropic_service.py）

```python
# 現在
response = self._client.messages.create(
    model=self._model_id,
    max_tokens=self._max_tokens,
    system=system_prompt,  # 文字列
    messages=[{"role": "user", "content": user_message}],  # 文字列
)
```

#### キャッシング対応後

```python
# キャッシング対応
response = self._client.messages.create(
    model=self._model_id,
    max_tokens=self._max_tokens,
    system=[
        {
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        }
    ],
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": shared_context,  # 全体構造情報（キャッシュ対象）
                    "cache_control": {"type": "ephemeral"},
                },
                {
                    "type": "text",
                    "text": group_specific_content,  # グループ固有の内容
                },
            ],
        }
    ],
)
```

#### レスポンスのトークン情報

```python
response.usage.cache_creation_input_tokens  # キャッシュ書込トークン
response.usage.cache_read_input_tokens       # キャッシュ読取トークン
response.usage.input_tokens                   # キャッシュされなかった入力トークン
```

### 3.2 AWS Bedrock（Converse API）

| 項目 | 内容 |
|------|------|
| 有効化方法 | `{"cachePoint": {"type": "default"}}` を content に挿入 |
| 対象 | system, messages, toolConfig の content blocks |
| 最小トークン数 | Claude Opus 4.5: 4,096 / Claude Sonnet: 1,024 / Claude Haiku 4.5: 4,096 |
| TTL | 5分（デフォルト）/ 1時間（`ttl: "1h"`、Opus 4.5/Sonnet 4.5/Haiku 4.5のみ） |
| 最大チェックポイント | 4個/リクエスト |
| キャッシュ書込コスト | 通常入力の約1.25倍 |
| キャッシュ読取コスト | 通常入力の約0.1倍 |
| 注意 | クロスリージョン推論プロファイル使用時はキャッシュヒット率が低下 |

#### 現在の実装（bedrock_service.py）

```python
# 現在
response = self._client.converse(
    modelId=self._model_id,
    messages=[{
        "role": "user",
        "content": [{"text": user_message}],
    }],
    system=[{"text": system_prompt}],
    inferenceConfig={"maxTokens": self._max_tokens},
)
```

#### キャッシング対応後

```python
# キャッシング対応
response = self._client.converse(
    modelId=self._model_id,
    messages=[{
        "role": "user",
        "content": [
            {"text": shared_context},        # 全体構造情報
            {"cachePoint": {"type": "default"}},  # ← キャッシュポイント
            {"text": group_specific_content},  # グループ固有の内容
        ],
    }],
    system=[
        {"text": system_prompt},
        {"cachePoint": {"type": "default"}},  # ← システムプロンプトをキャッシュ
    ],
    inferenceConfig={"maxTokens": self._max_tokens},
)
```

#### レスポンスのトークン情報

```python
usage = response.get("usage", {})
usage.get("cacheReadInputTokens", 0)   # キャッシュ読取トークン
usage.get("cacheWriteInputTokens", 0)  # キャッシュ書込トークン
```

#### Bedrock固有の注意事項

- `global.` プレフィックス付きのクロスリージョン推論プロファイル（例: `global.anthropic.claude-haiku-4-5-20251001-v1:0`）を使用している場合、リクエストが異なるリージョンにルーティングされるとキャッシュミスになる
- 最大キャッシュ可能トークン: 32,000（Claudeモデル）
- boto3の最新バージョンが必要（`cachePoint`パラメータ対応）

### 3.3 OpenAI API

| 項目 | 内容 |
|------|------|
| 有効化方法 | **完全自動**（コード変更不要） |
| 対象 | プロンプト全体のプレフィックス |
| 最小トークン数 | 1,024トークン |
| マッチング粒度 | 最初の1,024トークン後、128トークン単位で一致を判定 |
| TTL | 5〜10分（デフォルト）/ 最大24時間（`prompt_cache_retention="24h"`） |
| キャッシュ書込コスト | **追加コストなし** |
| キャッシュ読取コスト | モデルにより50%〜90%割引 |
| 条件 | プレフィックスの完全一致が必要 |

#### 現在の実装（openai_service.py）

```python
# 現在（変更不要で自動キャッシュが有効）
response = self._client.chat.completions.create(
    model=self._model_id,
    max_completion_tokens=self._max_tokens,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ],
)
```

#### キャッシング対応後

OpenAIの自動キャッシングはトークン列のプレフィックス一致で判定されるため、content配列に分割してもキャッシュ効率には影響しない。ただし、Anthropic/Bedrockと実装構造を統一し、キャッシュ対象と動的部分の意図を明確にするため、**content配列に分割する**:

```python
# キャッシング対応（Anthropic/Bedrockと構造を統一）
response = self._client.chat.completions.create(
    model=self._model_id,
    max_completion_tokens=self._max_tokens,
    messages=[
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": shared_context,  # 全体構造情報（キャッシュ対象相当）
                },
                {
                    "type": "text",
                    "text": group_specific_content,  # グループ固有の内容
                },
            ],
        },
    ],
)
```

#### レスポンスのトークン情報

```python
usage = response.usage
if usage and usage.prompt_tokens_details:
    cached_tokens = usage.prompt_tokens_details.cached_tokens  # キャッシュヒットトークン
```

## 4. 実装方針

### 4.1 `send_message` のインターフェース拡張

現在の `send_message` は `(system_prompt, user_message)` の2引数だが、キャッシングを活用するには**キャッシュ可能な部分とキャッシュ不可の部分を分離**する必要がある。

#### 案A: 新メソッド `send_message_with_cache` を追加（推奨）

```python
class LLMProvider(ABC):
    # 既存（変更なし）
    @abstractmethod
    def send_message(self, system_prompt: str, user_message: str) -> tuple[str, int, int]:
        pass

    # 新規追加
    def send_message_with_cache(
        self,
        system_prompt: str,
        cached_context: str,      # キャッシュ対象の共通コンテキスト
        dynamic_content: str,     # グループ固有の動的コンテンツ
    ) -> tuple[str, int, int]:
        """キャッシュ対応メッセージ送信（デフォルトはキャッシュなしにフォールバック）"""
        return self.send_message(system_prompt, cached_context + "\n\n" + dynamic_content)
```

**メリット**:
- 既存の `send_message` は変更なし（後方互換性）
- `send_message_with_cache` をオーバーライドしないプロバイダーは自動的にフォールバック
- フェーズ1（構造マッチング）やフェーズ3（統合）は既存の `send_message` をそのまま使用可能

#### 案B: `send_message` にオプション引数を追加

```python
def send_message(
    self, system_prompt: str, user_message: str,
    cache_prefix: str | None = None,  # キャッシュ対象プレフィックス
) -> tuple[str, int, int]:
```

**デメリット**: 既存の全プロバイダー実装を変更する必要がある。

### 4.2 戻り値のトークン情報拡張

キャッシュの効果を測定するため、戻り値にキャッシュ関連トークン情報を追加する。

```python
# 現在
tuple[str, int, int]  # (text, input_tokens, output_tokens)

# 拡張案: dataclass を使用
@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0    # キャッシュ読取トークン
    cache_write_tokens: int = 0   # キャッシュ書込トークン
```

### 4.3 review.py（グループレビュー）の修正

```python
@router.post("/review/group", response_model=GroupReviewResponse)
async def review_group(request: GroupReviewRequest):
    # ... 既存のシステムプロンプト構築 ...

    # ユーザーメッセージを2つに分離:
    # 1. cached_context: 全グループ共通の全体構造情報
    # 2. dynamic_content: グループ固有のレビュー対象内容

    # キャッシュ対象（全グループ共通）
    cached_parts = []
    if request.documentIndexMd or request.codeIndexMd or request.allGroups:
        cached_parts.append("## 全体構造情報（参考）\n")
        # ... 全体構造情報の構築（現在の実装と同じ） ...

    cached_context = "\n".join(cached_parts)

    # 動的コンテンツ（グループ固有）
    dynamic_parts = [
        f"## レビュー対象グループ: {request.groupName}\n",
        f"- グループID: {request.groupId}\n",
        "## 設計書内容\n",
        request.documentContent,
        "\n## コード内容\n",
        request.codeContent,
    ]
    dynamic_content = "\n".join(dynamic_parts)

    # キャッシュ対応呼び出し
    response_text, input_tokens, output_tokens = provider.send_message_with_cache(
        system_prompt, cached_context, dynamic_content
    )
```

### 4.4 プロンプト構造の変更（重要）

現在のグループレビューのユーザーメッセージ構造:

```
[グループ情報]      ← 動的
[設計書内容]        ← 動的
[コード内容]        ← 動的
[全体構造情報]      ← 共通（キャッシュ対象）
```

キャッシュを効果的に使うためには、**共通部分を先頭に移動**する必要がある:

```
[全体構造情報]      ← 共通（キャッシュ対象）★先頭に移動
--- キャッシュブレークポイント ---
[グループ情報]      ← 動的
[設計書内容]        ← 動的
[コード内容]        ← 動的
```

**注意**: プロンプトの順序を変更するとLLMの出力品質に影響する可能性があるため、変更後のレビュー品質を検証する必要がある。

## 5. 実装ステップ

### Step 1: LLMProvider インターフェース拡張

- [ ] `LLMResponse` dataclass の定義（`app/models/schemas.py` または `app/services/llm_service.py`）
- [ ] `LLMProvider` に `send_message_with_cache` メソッドを追加（デフォルト実装付き）

### Step 2: Anthropic プロバイダーのキャッシング対応

- [ ] `AnthropicProvider.send_message_with_cache` の実装
  - systemをcontent block配列に変換し `cache_control` を付与
  - user messageを `cached_context`（`cache_control`付き）+ `dynamic_content` のcontent block配列に変換
- [ ] キャッシュ関連トークン数の取得（`cache_creation_input_tokens`, `cache_read_input_tokens`）

### Step 3: Bedrock プロバイダーのキャッシング対応

- [ ] `BedrockProvider.send_message_with_cache` の実装
  - system配列に `cachePoint` を追加
  - messages配列のcontent内に `cachePoint` を挿入
- [ ] キャッシュ関連トークン数の取得（`cacheReadInputTokens`, `cacheWriteInputTokens`）
- [ ] boto3バージョンの確認（`cachePoint`対応バージョンが必要）
- [ ] クロスリージョン推論プロファイル使用時の注意事項をドキュメント化

### Step 4: OpenAI プロバイダーのキャッシング対応

- [ ] `OpenAIProvider.send_message_with_cache` の実装
  - Anthropic/Bedrockと同様にuser messageをcontent block配列に分割（`cached_context` + `dynamic_content`）
  - キャッシュ効率への影響はないが、3プロバイダーで実装構造を統一する
- [ ] キャッシュトークン数の取得（`prompt_tokens_details.cached_tokens`）

### Step 5: review.py グループレビューの修正

- [ ] ユーザーメッセージの構造変更（共通コンテキストを先頭に移動）
- [ ] `send_message` → `send_message_with_cache` への切替
- [ ] レスポンスの `tokensUsed` にキャッシュ情報を追加

### Step 6: テスト・検証

- [ ] 各プロバイダーのキャッシュ動作確認
- [ ] キャッシュヒット率の計測
- [ ] レビュー品質の検証（プロンプト順序変更の影響確認）
- [ ] コスト削減効果の計測

## 6. リスクと考慮事項

### プロンプト順序変更による品質への影響

全体構造情報をユーザーメッセージの先頭に移動することで、LLMが「参考情報」と「レビュー対象」の区別を誤る可能性がある。セクションヘッダーや指示を明確にすることで対策する。

### 最小トークン数の未達

全体構造情報が少ない場合（設計書・コードが小さい場合）、キャッシュの最小トークン数（1,024〜4,096）に達しない可能性がある。この場合はキャッシュなしで処理されるが、エラーにはならない。

### Bedrock クロスリージョン推論

現在のデフォルトモデルID `global.anthropic.claude-haiku-4-5-20251001-v1:0` はクロスリージョン推論プロファイルであり、キャッシュヒット率が低下する可能性がある。リージョン固定のモデルID（例: `anthropic.claude-haiku-4-5-20251001-v1:0`）への変更を検討するか、キャッシュヒット率をモニタリングする。

### キャッシュTTL（5分）の制約

グループレビューはフロントエンドから1グループずつ順次呼び出されるため、ユーザーの操作速度によっては5分のTTL内に次のグループのリクエストが到達しない可能性がある。ただし、通常のレビューフローではグループ間の間隔は数秒〜数十秒であるため、問題になるケースは少ないと想定。

### 後方互換性

`send_message_with_cache` はデフォルト実装で `send_message` にフォールバックするため、既存の呼び出しコードは変更不要。一括レビュー（`execute_review`）にも影響なし。

## 7. プロバイダー別対応サマリー

| 項目 | Anthropic | Bedrock | OpenAI |
|------|-----------|---------|--------|
| コード変更 | 必要（content block配列化 + cache_control付与） | 必要（cachePoint挿入） | 必要（content block配列化で構造統一、キャッシュは自動） |
| キャッシュ制御 | 明示的（cache_control） | 明示的（cachePoint） | 自動（プレフィックス一致） |
| 書込コスト | 1.25倍 | 1.25倍 | なし |
| 読取割引 | 90% | 90% | 50%〜90%（モデルによる） |
| 最小トークン | モデル依存（1,024〜4,096） | モデル依存（1,024〜4,096） | 1,024 |
| TTL | 5分 or 1時間 | 5分 or 1時間 | 5〜10分 or 24時間 |
| 実装難易度 | 中 | 中 | 低 |
