# AI モード マルチプロバイダー対応 計画書

**d3e9822b5a67054ad4e7a4b86017a51381611315 で対応完了。今後は新しい仕様書、計画書を参照してください。**

作成日: 2026-02-18

## 1. 背景と目的

現在の md2map AI モード（`--split-mode ai`）は OpenAI API にハードコードされており、以下の課題がある。

### 現状の課題

1. **OpenAI 専用**: `_select_chunks_ai` 内で `from openai import OpenAI` が直接呼ばれており、Bedrock / Anthropic は利用不可
2. **認証が環境変数固定**: `OPENAI_API_KEY` 環境変数のみ対応。外部アプリから認証情報を渡す手段がない
3. **外部連携の制約**: AI レビュアー（spec-code-ai-reviewer）が md2map を subtree で取り込んで利用しているが、AI レビュアー側で設定済みの LLM 認証情報を md2map に渡す方法がない（`split.py` の `MarkdownParser()` 呼び出し時に LLM 設定を注入できない）
4. **LLM ロジックがパーサーに密結合**: `MarkdownParser` クラス内に API 呼び出し・プロンプト構築・レスポンスパースがすべて含まれており、テスタビリティと拡張性が低い

### 目的

- Bedrock / Anthropic / OpenAI の 3 プロバイダーに対応する
- LLM 実行のベースクラスを作成して共通化する（AI レビュアーの `LLMProvider` パターンを参考）
- 外部アプリから LLM 認証情報とモード指定を渡せるようにする
- AI レビュアー側で設定されている LLM 設定をそのまま md2map に流用できるようにする

---

## 2. 現状分析

### 2.1 md2map 側（現在の AI モード実装）

| 項目 | 現状 |
|------|------|
| LLM 呼び出し箇所 | `md2map/parsers/markdown_parser.py` の `_select_chunks_ai()` (L560-657) |
| 対応プロバイダー | OpenAI のみ |
| 認証方式 | `OPENAI_API_KEY` 環境変数 |
| モデル指定 | `MD2MAP_AI_MODEL` / `OPENAI_MODEL` 環境変数 or `gpt-4o-mini` |
| max_tokens | 800 固定 |
| パーサーへの渡し方 | `MarkdownParser(split_mode="ai")` のみ。認証情報の注入不可 |

**問題のあるコード（`markdown_parser.py`）**:

```python
# コンストラクタ: OpenAI 前提のチェック
if split_mode == "ai":
    import openai  # OpenAI 固定
    if not os.getenv("OPENAI_API_KEY"):  # 環境変数固定
        raise RuntimeError(...)

# _select_chunks_ai: OpenAI クライアント直接利用
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(...)
```

### 2.2 AI レビュアー側（参考パターン）

**`llm_service.py` の設計**:
- `LLMProvider` 抽象基底クラスに `send_message(system_prompt, user_message) -> (text, input_tokens, output_tokens)` を定義
- `BedrockProvider` / `AnthropicProvider` / `OpenAIProvider` がそれぞれ実装
- `LLMConfig` データクラスで `provider`, `model`, `apiKey`, `accessKeyId`, `secretAccessKey`, `region`, `maxTokens` を保持
- `get_llm_provider(llm_config)` ファクトリ関数でプロバイダーを選択

**`split.py`（外部からの md2map 呼び出し）**:

```python
# 現在: LLM設定を渡す手段がない
parser = MarkdownParser()
sections, warnings = parser.parse(input_path, request.maxDepth)
```

---

## 3. 設計方針

### 3.1 LLM プロバイダー抽象化レイヤーの新設

md2map 内に軽量な LLM プロバイダー抽象化レイヤーを新設する。AI レビュアーの `LLMProvider` をそのまま取り込むのではなく、md2map の用途（セグメンテーションのみ）に特化したシンプルなインターフェースとする。

```
md2map/
  llm/                          # 新規ディレクトリ
    __init__.py
    config.py                   # LLMConfig データクラス
    base_provider.py            # BaseLLMProvider 抽象基底クラス
    openai_provider.py          # OpenAI 実装
    anthropic_provider.py       # Anthropic 実装
    bedrock_provider.py         # Bedrock 実装
    factory.py                  # get_llm_provider ファクトリ関数
```

### 3.2 インターフェース設計

#### LLMConfig

```python
@dataclass
class LLMConfig:
    """LLM 設定（外部アプリからの注入に対応）"""
    provider: str               # "openai" | "anthropic" | "bedrock"
    model: str                  # モデルID
    api_key: Optional[str]      # Anthropic / OpenAI 用
    access_key_id: Optional[str]    # Bedrock 用
    secret_access_key: Optional[str] # Bedrock 用
    region: Optional[str]       # Bedrock 用
    max_tokens: int = 800       # 最大出力トークン数
```

#### BaseLLMProvider

```python
class BaseLLMProvider(ABC):
    """LLM プロバイダーの抽象基底クラス"""

    @abstractmethod
    def send_message(
        self, system_prompt: str, user_message: str
    ) -> str:
        """メッセージを送信してレスポンステキストを返す"""
        pass
```

- AI レビュアーと異なり、トークン数は返さない（md2map ではトークン課金管理が不要なため）
- レビュー固有のメソッド (`execute_review` 等) は含めない

#### ファクトリ関数

```python
def get_llm_provider(config: LLMConfig) -> BaseLLMProvider:
    """LLMConfig に基づいて適切なプロバイダーを返す"""
```

### 3.3 MarkdownParser への注入方式

`MarkdownParser` のコンストラクタに `LLMConfig` または `BaseLLMProvider` インスタンスを渡せるようにする。

```python
class MarkdownParser(BaseParser):
    def __init__(
        self,
        split_mode: str = "heading",
        split_threshold: int = 500,
        max_subsections: int = 5,
        llm_config: Optional[LLMConfig] = None,        # 新規追加
        llm_provider: Optional[BaseLLMProvider] = None, # 新規追加
    ) -> None:
```

**優先順位**:
1. `llm_provider` が渡された場合 → そのまま使用（外部アプリが独自プロバイダーを注入するケース）
2. `llm_config` が渡された場合 → `get_llm_provider(llm_config)` でプロバイダーを生成
3. どちらも渡されない場合 → 環境変数からフォールバック（現在の動作との後方互換性を維持）

### 3.4 CLI オプションの拡張

```
--ai-provider {openai,anthropic,bedrock}   AIプロバイダー（デフォルト: openai）
--ai-model MODEL_ID                        AIモデルID
--ai-region REGION                         Bedrock用リージョン
```

認証情報は環境変数から取得する（CLI での直接入力はセキュリティ上避ける）。

| プロバイダー | 認証用環境変数 |
|-------------|---------------|
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Bedrock | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`（または IAM ロール） |

---

## 4. md2map 側の修正計画

### Phase 1: LLM プロバイダー抽象化レイヤーの作成

| # | 作業内容 | 対象ファイル |
|---|---------|-------------|
| 1-1 | `LLMConfig` データクラスの作成 | `md2map/llm/config.py`（新規） |
| 1-2 | `BaseLLMProvider` 抽象基底クラスの作成 | `md2map/llm/base_provider.py`（新規） |
| 1-3 | `OpenAIProvider` の実装（既存ロジックの移植） | `md2map/llm/openai_provider.py`（新規） |
| 1-4 | `AnthropicProvider` の実装 | `md2map/llm/anthropic_provider.py`（新規） |
| 1-5 | `BedrockProvider` の実装 | `md2map/llm/bedrock_provider.py`（新規） |
| 1-6 | `get_llm_provider` ファクトリ関数の作成 | `md2map/llm/factory.py`（新規） |

**実装の注意点**:

- 各プロバイダーの `send_message` は、system / user メッセージを受け取り、レスポンステキストのみを返す
- OpenAI は `openai` パッケージ、Anthropic は `anthropic` パッケージ、Bedrock は `boto3` を使用
- すべて optional dependency とし、未インストール時は明確なエラーメッセージを表示

### Phase 2: MarkdownParser のリファクタリング

| # | 作業内容 | 対象ファイル |
|---|---------|-------------|
| 2-1 | コンストラクタに `llm_config` / `llm_provider` パラメータを追加 | `md2map/parsers/markdown_parser.py` |
| 2-2 | `_select_chunks_ai` から OpenAI 直接呼び出しを削除し、`BaseLLMProvider.send_message` 経由に変更 | 同上 |
| 2-3 | コンストラクタの OpenAI 固有チェック（`import openai`, `OPENAI_API_KEY`）を削除し、プロバイダー生成ロジックに置換 | 同上 |
| 2-4 | プロンプト構築とレスポンスパースのロジックは `_select_chunks_ai` 内に維持（パーサーの責務） | 同上 |

**変更後の `_select_chunks_ai` イメージ**:

```python
def _select_chunks_ai(self, section, lines, paragraphs, target_parts):
    # プロンプト構築（従来通り）
    system_text = "You are a document segmentation assistant. ..."
    user_text = f"Target sections: {target_parts}. ..."

    # LLM 呼び出し（プロバイダー経由に変更）
    try:
        response_text = self._llm_provider.send_message(system_text, user_text)
    except Exception as exc:
        logger.warning(f"AI API call failed: {exc}")
        return [], None

    # レスポンスパース（従来通り）
    data = json.loads(response_text)
    ...
```

### Phase 3: CLI の拡張

| # | 作業内容 | 対象ファイル |
|---|---------|-------------|
| 3-1 | `--ai-provider`, `--ai-model`, `--ai-region` オプションの追加 | `md2map/cli.py` |
| 3-2 | 環境変数からの認証情報取得と `LLMConfig` 構築ロジック | 同上 |
| 3-3 | `MarkdownParser` への `llm_config` 受け渡し | 同上 |

### Phase 4: pyproject.toml の更新

| # | 作業内容 | 対象ファイル |
|---|---------|-------------|
| 4-1 | `[project.optional-dependencies]` の更新 | `pyproject.toml` |

```toml
[project.optional-dependencies]
ai = ["openai>=1.0"]                                      # 既存
ai-anthropic = ["anthropic>=0.18"]                         # 新規
ai-bedrock = ["boto3>=1.28"]                               # 新規
ai-all = ["openai>=1.0", "anthropic>=0.18", "boto3>=1.28"] # 新規（全プロバイダー）
```

### Phase 5: テスト

| # | 作業内容 |
|---|---------|
| 5-1 | `LLMConfig` のバリデーションテスト |
| 5-2 | 各プロバイダーの `send_message` のモックテスト |
| 5-3 | `MarkdownParser` への `llm_config` / `llm_provider` 注入テスト |
| 5-4 | `llm_provider` 注入時に環境変数不要であることの確認テスト |
| 5-5 | CLI の新オプションの統合テスト |
| 5-6 | 後方互換性テスト（引数なし `MarkdownParser()` が従来通り動作すること） |

---

## 5. 後方互換性の保証

| 利用パターン | 修正後の動作 |
|-------------|------------|
| `MarkdownParser()` （引数なし） | 従来通り `heading` モードで動作。LLM 不要 |
| `MarkdownParser(split_mode="ai")` （`llm_config` なし） | 環境変数 `OPENAI_API_KEY` 等からフォールバック（現在の動作を維持） |
| `MarkdownParser(split_mode="ai", llm_config=config)` | 渡された設定でプロバイダーを生成 |
| `MarkdownParser(split_mode="ai", llm_provider=provider)` | 渡されたプロバイダーをそのまま使用 |
| CLI `md2map build file.md` | 従来通り |
| CLI `md2map build file.md -m ai --ai-provider anthropic` | Anthropic で AI 分割 |

---

## 6. 実装優先順位

| 優先度 | 内容 | 理由 |
|--------|------|------|
| **P1** | Phase 1-2: LLM 抽象化 + パーサーリファクタリング | 他の全作業の前提 |
| **P1** | Phase 5: テスト | 品質保証 |
| **P2** | Phase 3: CLI 拡張 | CLI ユーザー向け |
| **P3** | Phase 4: pyproject.toml | リリース前に必須 |

---

## 付録 A. AI レビュアー側（呼び出し元）の修正案

> 本付録は今回の実装範囲外である。md2map 側の対応完了後、AI レビュアー側で別途対応する際の参考資料として記載する。

AI レビュアー（spec-code-ai-reviewer）は md2map を subtree で取り込んでおり、`split.py` から `MarkdownParser` を直接呼び出している。md2map のマルチプロバイダー対応が完了すれば、AI レビュアー側で設定済みの `LLMConfig` を md2map に渡せるようになる。

### A.1 現状の呼び出しコード（`split.py`）

```python
# 現在: LLM設定を渡す手段がない
parser = MarkdownParser()
sections, warnings = parser.parse(input_path, request.maxDepth)
```

### A.2 SplitMarkdownRequest スキーマの拡張

`split.py` のリクエストスキーマに分割モードと LLM 設定を追加する。

```python
class SplitMarkdownRequest(BaseModel):
    content: str
    filename: str | None = None
    maxDepth: int = 2
    # --- 以下を新規追加 ---
    splitMode: str | None = None                # "heading" | "nlp" | "ai"（None時はheading）
    splitThreshold: int | None = None           # 再分割閾値
    maxSubsections: int | None = None           # 最大仮想見出し数
    llmConfig: LLMConfig | None = None          # AI レビュアー側の LLM 設定を流用
```

### A.3 split.py の修正

```python
@router.post("/split/markdown", response_model=SplitMarkdownResponse)
async def split_markdown(request: SplitMarkdownRequest):
    # ...

    # md2map の LLMConfig に変換
    md2map_llm_config = None
    if request.llmConfig and request.splitMode == "ai":
        from md2map.llm.config import LLMConfig as Md2mapLLMConfig
        md2map_llm_config = Md2mapLLMConfig(
            provider=request.llmConfig.provider,
            model=request.llmConfig.model,
            api_key=request.llmConfig.apiKey,
            access_key_id=request.llmConfig.accessKeyId,
            secret_access_key=request.llmConfig.secretAccessKey,
            region=request.llmConfig.region,
            max_tokens=800,
        )

    # パーサー生成（LLM 設定を注入）
    parser = MarkdownParser(
        split_mode=request.splitMode or "heading",
        split_threshold=request.splitThreshold or 500,
        max_subsections=request.maxSubsections or 5,
        llm_config=md2map_llm_config,
    )
    sections, warnings = parser.parse(input_path, request.maxDepth)
```

### A.4 フロントエンド側の対応

AI レビュアーのフロントエンドで分割モードを選択する UI を追加し、`splitMode` と `llmConfig`（フロントエンド側で既に保持している LLM 設定）をリクエストに含める。

| # | 作業内容 | 対象 |
|---|---------|------|
| A-4a | 分割 API リクエストに `splitMode` / `llmConfig` を追加 | フロントエンド API クライアント |
| A-4b | 分割モード選択 UI（heading / nlp / ai のセレクタ）の追加 | 分割設定画面 |
| A-4c | AI モード選択時に、レビュー設定で使用中の LLM 設定を自動的に `llmConfig` に設定 | 分割設定画面 |

### A.5 DocumentPart の拡張（任意）

`split.py` のレスポンスに仮想セクション情報を含める。

```python
class DocumentPart(BaseModel):
    # ... 既存フィールド ...
    isVirtual: bool = False             # 新規
    splitReason: str | None = None      # 新規
```
