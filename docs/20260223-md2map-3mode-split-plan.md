# md2map 3モード対応 修正計画

- 作成日: 2026-02-23
- バージョン: v0.8.2
- 関連: md2map AI モード マルチプロバイダー対応（md2map/docs/20260218ai-mode-multi-provider-plan.md 付録A）

## 背景

md2map ライブラリは3つの分割モードを持つ（heading / nlp / ai）。
現在、AIレビュアーは heading モードのみで `MarkdownParser()` を引数なしで呼び出している。
本修正により、フロントエンドから分割モードを選択し、AIモード時にはLLM設定を渡せるようにする。

## ゴール

1. 分割APIで3モード（heading / nlp / ai）に対応する
2. フロントエンドの「分割設定」に分割モード選択UIを追加する
3. AIモード時、フロントエンドのLLM設定を md2map に渡す

## 非ゴール

- code2map の分割モード追加（code2map は現状1モードのみ）
- md2map 上流リポジトリへの変更

## 現状整理

### バックエンド（split.py）

```python
# 現在の呼び出し（headingモード固定）
parser = MarkdownParser()
sections, warnings = parser.parse(input_path, request.maxDepth)
```

### md2map の MarkdownParser

```python
def __init__(
    self,
    split_mode: str = "heading",      # "heading", "nlp", "ai"
    split_threshold: int = 500,
    max_subsections: int = 5,
    llm_config: Optional["LLMConfig"] = None,
    llm_provider: Optional["BaseLLMProvider"] = None,
) -> None
```

### フロントエンド（SplitSettingsSection.tsx）

- 「レビュー方式」: 一括 / 分割 のラジオボタン
- 「分割オプション > 設計書」: 見出しレベル（H2/H3/H4）のラジオボタン
- 分割モード選択は未実装

## 実装ステップ

### Step 1: バックエンド - スキーマ拡張

**対象**: `versions/v0.8.2/backend/app/models/schemas.py`

`SplitMarkdownRequest` に以下フィールドを追加:

```python
class SplitMarkdownRequest(BaseModel):
    content: str
    filename: str
    maxDepth: int = Field(default=2, ge=1, le=6)
    splitMode: Literal["ai", "heading", "nlp"] = "ai"  # 追加
    llmConfig: LLMConfig | None = None                  # 追加（AIモード用）
```

### Step 2: バックエンド - split.py の修正

**対象**: `versions/v0.8.2/backend/app/routers/split.py`

LLMConfig 変換ヘルパー関数を追加し、MarkdownParser 呼び出しを修正する。

```python
def _convert_to_md2map_llm_config(llm_config: LLMConfig | None):
    """バックエンドの LLMConfig を md2map の LLMConfig に変換する"""
    from md2map.llm.config import LLMConfig as Md2mapLLMConfig

    if llm_config is None:
        # システムLLM（環境変数）を使用
        from md2map.llm.factory import build_llm_config_from_env
        return build_llm_config_from_env()

    return Md2mapLLMConfig(
        provider=llm_config.provider,
        model=llm_config.model,
        api_key=llm_config.apiKey,
        access_key_id=llm_config.accessKeyId,
        secret_access_key=llm_config.secretAccessKey,
        region=llm_config.region,
        max_tokens=800,  # md2map の分割用途では固定
    )
```

MarkdownParser 呼び出しの変更:

```python
# AIモードの場合のみ LLMConfig を変換
md2map_llm_config = None
if request.splitMode == "ai":
    md2map_llm_config = _convert_to_md2map_llm_config(request.llmConfig)

parser = MarkdownParser(
    split_mode=request.splitMode,
    llm_config=md2map_llm_config,
)
```

### Step 3: フロントエンド - 型定義の拡張

**対象**: `versions/v0.8.2/frontend/src/features/reviewer/types/index.ts`

```typescript
// 分割モード型を追加
export type DocumentSplitMode = 'ai' | 'heading' | 'nlp'

// SplitSettings に documentSplitMode を追加
export interface SplitSettings {
  reviewMode: SplitMode
  documentMaxDepth: number
  documentSplitMode: DocumentSplitMode  // 追加
}

// SplitMarkdownRequest に splitMode と llmConfig を追加
export interface SplitMarkdownRequest {
  content: string
  filename: string
  maxDepth: number
  splitMode?: DocumentSplitMode  // 追加
  llmConfig?: LlmConfig          // 追加
}
```

### Step 4: フロントエンド - useSplitSettings フック修正

**対象**: `versions/v0.8.2/frontend/src/features/reviewer/hooks/useSplitSettings.ts`

- `DEFAULT_SETTINGS` に `documentSplitMode: 'ai'` を追加
- `executePreview` の引数に `llmConfig` を追加
- `api.splitMarkdown` 呼び出しに `splitMode` と `llmConfig` を渡す

```typescript
const response = await api.splitMarkdown({
  content: designMarkdown,
  filename: designFilename,
  maxDepth: settings.documentMaxDepth,
  splitMode: settings.documentSplitMode,
  llmConfig: settings.documentSplitMode === 'ai' ? llmConfig : undefined,
})
```

### Step 5: フロントエンド - SplitSettingsSection UI修正

**対象**: `versions/v0.8.2/frontend/src/features/reviewer/components/SplitSettingsSection.tsx`

「分割オプション > 設計書」セクションに分割モード選択を追加（見出しレベルの上に配置）。
ラジオボタンを縦に並べ、右側に簡単な説明を付ける:

```
設計書
  分割モード:
    ◉ AI（推奨）    AIが文脈を考慮して最適な分割を行います
    ○ 見出し        見出し（H2/H3等）の区切りで機械的に分割します
    ○ NLP          自然言語処理で文章の意味的な区切りを検出します
    ※AIモードでは、設計書が大きい場合は、処理に時間が掛かったり、
      タイムアウトや制限等でエラーになる可能性があります。

  見出しレベル:
    ○ H2(##)まで（推奨）  ○ H3(###)まで  ○ H4(####)まで
```

- デフォルト: AI
- 注意文は分割モード選択の下に常時表示

### Step 6: フロントエンド - index.tsx の接続

**対象**: `versions/v0.8.2/frontend/src/features/reviewer/index.tsx`

- `handleSplitPreviewExecute` で `llmConfig` を `executeSplitPreview` に渡す

### Step 7: バックエンド - MAP.json生成とレスポンス拡張

**目的**: 構造マッチングに渡す MAP.json を、md2map が生成した内容をそのまま渡す

**現状の問題**:
- バックエンドの split.py は MAP.json を生成していない
- フロントエンドの index.tsx が `documentParts` から手動で `documentMapJson` を構築している
- そのため `is_subsplit`, `subsplit_title`, `note` 等の情報が構造マッチングに渡されない

**対象**: `versions/v0.8.2/backend/app/routers/split.py`, `versions/v0.8.2/backend/app/models/schemas.py`

1. split.py で md2map の `generate_map()` を呼び出し MAP.json を生成・読み取る
2. `SplitMarkdownResponse` に `mapJson` フィールドを追加（md2map生成のMAP.jsonをそのまま返す）

```python
# split.py に追加
from md2map.generators.map_generator import generate_map as md2map_generate_map

# MAP.json生成
map_path = os.path.join(out_dir, "MAP.json")
md2map_generate_map(sections, out_dir, map_path)

# MAP.json読み取り
with open(map_path, "r", encoding="utf-8") as f:
    import json
    map_json = json.load(f)
```

```python
# schemas.py
class SplitMarkdownResponse(BaseModel):
    success: bool
    parts: list[DocumentPart] = []
    indexContent: str | None = None
    mapJson: list[dict] | None = None  # 追加: md2map生成のMAP.json
    error: str | None = None
```

### Step 8: フロントエンド - MAP.json をそのまま構造マッチングに渡す

**対象**: `versions/v0.8.2/frontend/src/features/reviewer/types/index.ts`, `versions/v0.8.2/frontend/src/features/reviewer/index.tsx`

1. `SplitMarkdownResponse` に `mapJson` を追加
2. `SplitPreviewResult` に `documentMapJson` を追加
3. index.tsx の `executeSplitReviewFlow` で、手動構築の `documentMapJson` の代わりにバックエンドから返された `mapJson` を使用

```typescript
// 現在（手動構築）
const documentMapJson = {
  sections: splitPreviewResult.documentParts?.map((p) => ({
    id: p.id, title: p.section, level: p.level, ...
  })) || [],
}

// 修正後（md2map生成のMAP.jsonをそのまま使用）
const documentMapJson = {
  sections: splitPreviewResult.documentMapJson || [],
}
```

### Step 9: 表示名の改善（displayName の追加）

**目的**: subsplit されたセクションの表示名を正しく表示する

**方針**: バックエンド側で `DocumentPart` に `displayName` フィールドを追加し、
md2map の `section.display_name()` を使用する。
フロントエンドでは `section` の代わりに `displayName` を表示に使う。

**対象**: バックエンド `schemas.py`, `split.py` / フロントエンド `types/index.ts`, 表示箇所

1. バックエンド: `DocumentPart` に `displayName` を追加

```python
class DocumentPart(BaseModel):
    id: str
    section: str          # 元のセクション名（title）
    displayName: str      # 表示用名称（subsplit時はsubsplit_title）
    level: int
    ...
```

```python
# split.py での設定
DocumentPart(
    ...
    section=section.title,
    displayName=section.display_name(),  # md2mapの既存メソッドを使用
    ...
)
```

2. フロントエンド: `DocumentPart` 型に `displayName` を追加

```typescript
export interface DocumentPart {
  id: string
  section: string
  displayName: string   // 追加
  ...
}
```

3. 表示箇所で `section` の代わりに `displayName` を使用:
   - `SplitSettingsSection.tsx` のプレビューテーブル
   - `index.tsx` のグループレビュー時の見出し構築
   - 結果画面・DLマークダウンでのセクション名表示

## 影響ファイル一覧

| ファイル | 変更内容 |
|---------|---------|
| `versions/v0.8.2/backend/app/models/schemas.py` | `SplitMarkdownRequest` に `splitMode`, `llmConfig` 追加。`SplitMarkdownResponse` に `mapJson` 追加。`DocumentPart` に `displayName` 追加 |
| `versions/v0.8.2/backend/app/routers/split.py` | LLMConfig変換関数追加、MarkdownParser呼び出し修正、MAP.json生成・返却、displayName設定 |
| `versions/v0.8.2/frontend/src/features/reviewer/types/index.ts` | `DocumentSplitMode` 型追加、`SplitSettings`・`SplitMarkdownRequest` 拡張、`SplitMarkdownResponse` に `mapJson` 追加、`DocumentPart` に `displayName` 追加、`SplitPreviewResult` に `documentMapJson` 追加 |
| `versions/v0.8.2/frontend/src/features/reviewer/hooks/useSplitSettings.ts` | デフォルト設定追加、executePreview引数拡張、`documentMapJson` の保持 |
| `versions/v0.8.2/frontend/src/features/reviewer/components/SplitSettingsSection.tsx` | 分割モード選択UI追加、注意文追加、プレビューテーブルで `displayName` 使用 |
| `versions/v0.8.2/frontend/src/features/reviewer/index.tsx` | llmConfig の引き回し、構造マッチングでバックエンド生成 `mapJson` を使用、表示名に `displayName` を使用 |

## 既存パターンの再利用

| 再利用対象 | ファイル | 用途 |
|-----------|---------|------|
| `schemas.LLMConfig` | `backend/app/models/schemas.py` | レビューAPIで使用中、分割APIでも同一クラスを使用 |
| `md2map.llm.config.LLMConfig` | `md2map/md2map/llm/config.py` | md2map側のLLM設定データクラス |
| `build_llm_config_from_env()` | `md2map/md2map/llm/factory.py` | システムLLMフォールバック用 |
| `MarkdownParser(split_mode=, llm_config=)` | `md2map/md2map/parsers/markdown_parser.py` | 既存コンストラクタパラメータ |

## 検証方法

1. バックエンドテスト: `pytest` で既存テスト通過確認
2. フロントエンドテスト: `vitest` で既存テスト通過確認
3. 手動確認:
   - 分割設定で AI / 見出し / NLP モードを切替え可能
   - 見出しモードで分割プレビュー実行 → 従来通り動作
   - AIモード選択時、LLM設定が分割APIに渡される
   - NLPモード選択時、sudachipy で分割される
   - AIモードで subsplit が発生した場合、プレビューテーブルで subsplit_title（例: "概要: part-1"）が表示される
   - 構造マッチングに渡される MAP.json に is_subsplit, subsplit_title が含まれる
