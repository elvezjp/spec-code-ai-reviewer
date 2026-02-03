# マッピングモード実装計画書

## 概要

設計書の項目とソースコードの実装箇所（ファイル、クラス、関数、行番号）を対応付ける「マッピングモード」を追加する。

既存の「突合モード」が設計書とコードの整合性検証に焦点を当てているのに対し、マッピングモードは「設計書のどの項目が、ソースコードのどこで実装されているか」を明確にすることに特化する。

## 要件

### 機能要件

1. **モード切り替え**
   - 画面上部でタブによる切り替え（突合モード / マッピングモード）
   - 初期表示は突合モード

2. **入力**
   - 入力ファイルは既存と同一（設計書Excel、ソースコード）
   - 前処理も同一（Markdown変換、行番号付与）

3. **処理**
   - システムプロンプトはマッピング専用のものを使用
   - APIは既存の `/api/review` を使用（モードパラメータ追加）
   - 2回実行のロジックも同一

4. **出力**
   - マッピング結果の専用表示画面
   - 一式ダウンロード機能は同一

### 非機能要件

- v0.7.0 をコピーして v0.8.0 として実装
- 既存の突合モードは変更なし（後方互換維持）

---

## 実装計画

### Phase 1: バージョン準備

#### 1.1 v0.8.0 ディレクトリ作成

```bash
# v0.7.0 をコピー
cp -r versions/v0.7.0 versions/v0.8.0

# latest シンボリックリンク更新
rm latest
ln -s versions/v0.8.0 latest
```

#### 1.2 バージョン番号更新

| ファイル | 変更内容 |
|---------|---------|
| `versions/v0.8.0/backend/pyproject.toml` | `version = "0.8.0"` |
| `versions/v0.8.0/frontend/package.json` | `"version": "0.8.0"` |
| `versions/v0.8.0/spec.md` | バージョン番号更新 |

#### 1.3 設定ファイル更新

| ファイル | 変更内容 |
|---------|---------|
| `docker-compose.yml` | v0.8.0 の設定追加（port: 8080） |
| `nginx/version-map.conf` | v0.8.0 ルーティング追加、default更新 |
| `ecosystem.config.js` | v0.8.0 追加 |
| `dev.ecosystem.config.js` | v0.8.0 追加 |
| `versions/README.md` | v0.8.0 情報追加 |
| `README.md` | ポートテーブル、ディレクトリ構造更新 |
| `CHANGELOG.md` | v0.8.0 変更履歴追加 |

---

### Phase 2: フロントエンド実装

#### 2.1 型定義の追加

**ファイル**: `versions/v0.8.0/frontend/src/core/types/index.ts`

```typescript
// モード定義
export type ReviewMode = 'review' | 'mapping'

// モード設定
export interface ModeConfig {
  mode: ReviewMode
  label: string
  description: string
}
```

**ファイル**: `versions/v0.8.0/frontend/src/features/reviewer/types/index.ts`

```typescript
// ReviewRequest にモード追加
export interface ReviewRequest {
  // 既存フィールド...
  mode: ReviewMode  // 追加
}

// マッピング結果の型
export interface MappingItem {
  designSection: string      // 設計書の項目（見出し番号/項目名）
  designContent: string      // 設計書の内容要約
  codeLocation: string       // 実装箇所（ファイル名:行番号）
  codeElement: string        // 実装要素（クラス名/関数名）
  confidence: 'high' | 'medium' | 'low'  // 確信度
  notes?: string             // 備考
}

export interface MappingResult {
  items: MappingItem[]
  unmappedDesignItems: string[]  // マッピングできなかった設計項目
  summary: string                 // サマリー
}
```

#### 2.2 マッピング用プリセット追加

**ファイル**: `versions/v0.8.0/frontend/src/core/data/presetCatalog.ts`

```typescript
// マッピング用プリセットを追加
export const MAPPING_PRESET: Preset = {
  id: 'design-code-mapping',
  name: '設計書-コードマッピング',
  description: '設計書の各項目がソースコードのどこで実装されているかを特定します。',
  tags: ['マッピング', '設計書', 'トレーサビリティ'],
  systemPrompt: {
    role: 'あなたは設計書とソースコードのマッピングを行う専門家です。',
    purpose: `設計書の各項目（機能、要件、処理ロジックなど）がソースコードのどこで実装されているかを特定し、マッピング表を作成してください。

以下の情報を特定してください：
1. 設計書の項目（見出し番号、項目名）
2. 実装箇所（ファイル名、行番号範囲）
3. 実装要素（クラス名、関数名、メソッド名）
4. マッピングの確信度（高/中/低）`,
    format: `マークダウン形式で、以下の順に出力してください：

1. **マッピングサマリー**
   - マッピング実行日時
   - 対象ファイル
   - マッピング件数（高確信/中確信/低確信）

2. **マッピング一覧**（テーブル形式）
| 設計書項目 | 設計内容 | 実装ファイル:行 | 実装要素 | 確信度 | 備考 |
|-----------|---------|----------------|---------|-------|------|

3. **未マッピング項目**
   - 実装箇所を特定できなかった設計書項目のリスト

4. **マッピング詳細**
   - 各マッピングの根拠説明（必要に応じて）`,
    notes: `- 設計書の見出し番号や項目番号を必ず明示してください
- ソースコードの行番号を必ず添えてください
- 1つの設計項目が複数箇所で実装されている場合はすべて列挙してください
- 確信度は以下の基準で判定してください：
  - 高: 設計書の記述とコードが明確に対応
  - 中: 対応関係は推測できるが完全一致ではない
  - 低: 関連性はあるが確証がない
- 実装箇所が特定できない項目は「未マッピング項目」に記載してください`,
  },
  specTypes: [
    { type: '設計書', note: '各機能の実装箇所を特定してください' },
    { type: '要件定義書', note: '各要件の実装箇所を特定してください' },
    { type: '処理ロジック', note: '各処理の実装箇所を特定してください' },
    { type: '処理フロー', note: '各処理ステップの実装箇所を特定してください' },
    { type: 'インターフェース仕様', note: 'API/関数の実装箇所を特定してください' },
  ],
}
```

#### 2.3 モード切り替えUI

**ファイル**: `versions/v0.8.0/frontend/src/features/reviewer/components/ModeSelector.tsx`（新規）

```typescript
import type { ReviewMode } from '@core/types'

interface ModeSelectorProps {
  currentMode: ReviewMode
  onModeChange: (mode: ReviewMode) => void
}

export function ModeSelector({ currentMode, onModeChange }: ModeSelectorProps) {
  const modes = [
    { mode: 'review' as const, label: '突合モード', description: '設計書とコードの整合性を検証' },
    { mode: 'mapping' as const, label: 'マッピングモード', description: '設計項目と実装箇所を対応付け' },
  ]

  return (
    <div className="bg-white rounded-lg shadow-md p-4 mb-6">
      <div className="flex gap-2">
        {modes.map(({ mode, label, description }) => (
          <button
            key={mode}
            onClick={() => onModeChange(mode)}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition ${
              currentMode === mode
                ? 'text-white bg-blue-500'
                : 'text-gray-600 bg-gray-100 hover:bg-gray-200'
            }`}
          >
            <div>{label}</div>
            <div className="text-xs opacity-75">{description}</div>
          </button>
        ))}
      </div>
    </div>
  )
}
```

#### 2.4 マッピング結果表示コンポーネント

**ファイル**: `versions/v0.8.0/frontend/src/features/reviewer/components/MappingResult.tsx`（新規）

- 既存の `ReviewResult.tsx` をベースに作成
- マッピング一覧をテーブル形式で表示
- 確信度によるフィルタリング機能
- 未マッピング項目のハイライト表示
- 既存と同様のダウンロード機能

#### 2.5 状態管理の拡張

**ファイル**: `versions/v0.8.0/frontend/src/features/reviewer/hooks/useReviewerSettings.ts`

```typescript
// モード状態の追加
const [currentMode, setCurrentMode] = useState<ReviewMode>('review')

// モード変更時のプリセット自動切り替え
const handleModeChange = (mode: ReviewMode) => {
  setCurrentMode(mode)
  if (mode === 'mapping') {
    // マッピング用プリセットを自動適用
    applyPreset(MAPPING_PRESET)
  } else {
    // デフォルトプリセットに戻す
    applyPreset(getPresetById(DEFAULT_PRESET_ID))
  }
}
```

**ファイル**: `versions/v0.8.0/frontend/src/features/reviewer/hooks/useReviewExecution.ts`

```typescript
// executeReview にモードを渡す
const executeReview = async (mode: ReviewMode) => {
  // ...
  const response = await api.executeReview({
    ...request,
    mode,  // モードを追加
  })
  // ...
}
```

#### 2.6 メインコンポーネント更新

**ファイル**: `versions/v0.8.0/frontend/src/features/reviewer/index.tsx`

- `ModeSelector` コンポーネントを追加
- モードに応じた結果表示コンポーネントの切り替え
- プリセット選択UIの表示/非表示制御（マッピングモード時は非表示）

---

### Phase 3: バックエンド実装

#### 3.1 スキーマ更新

**ファイル**: `versions/v0.8.0/backend/app/models/schemas.py`

```python
from enum import Enum

class ReviewMode(str, Enum):
    REVIEW = "review"
    MAPPING = "mapping"

class ReviewRequest(BaseModel):
    # 既存フィールド...
    mode: ReviewMode = ReviewMode.REVIEW  # デフォルトは突合モード
```

#### 3.2 プロンプトビルダー拡張

**ファイル**: `versions/v0.8.0/backend/app/services/prompt_builder.py`

```python
def build_user_message(
    request: ReviewRequest,
    mode: ReviewMode = ReviewMode.REVIEW
) -> str:
    """ユーザーメッセージを構築"""

    # 既存のファイル情報構築ロジック...

    if mode == ReviewMode.MAPPING:
        return _build_mapping_user_message(request, file_info)
    else:
        return _build_review_user_message(request, file_info)

def _build_mapping_user_message(request: ReviewRequest, file_info: str) -> str:
    """マッピング用ユーザーメッセージ"""
    return f"""以下の設計書とソースコードについて、設計書の各項目がどこで実装されているかマッピングしてください。

{file_info}

# 指示
1. 設計書の各項目（見出し、要件、機能など）を抽出してください
2. 各項目に対応するソースコードの実装箇所を特定してください
3. マッピング結果を指定のフォーマットで出力してください
4. 実装箇所が特定できない項目は「未マッピング項目」として報告してください

# 設計書詳細
{request.designs_content}

# ソースコード詳細
{request.codes_content}
"""

def _build_review_user_message(request: ReviewRequest, file_info: str) -> str:
    """突合用ユーザーメッセージ（既存ロジック）"""
    # 既存の実装...
```

#### 3.3 レビューAPI更新

**ファイル**: `versions/v0.8.0/backend/app/routers/review.py`

```python
@router.post("/review")
async def execute_review(request: ReviewRequest) -> ReviewResponse:
    # ...

    # モードに応じたユーザーメッセージ構築
    user_message = build_user_message(request, mode=request.mode)

    # 以降は既存ロジックと同一
    # ...
```

---

### Phase 4: テスト

#### 4.1 フロントエンドテスト

**ファイル**: `versions/v0.8.0/frontend/src/features/reviewer/components/__tests__/ModeSelector.test.tsx`

- モード切り替えの動作確認
- 初期状態の確認
- コールバック呼び出しの確認

**ファイル**: `versions/v0.8.0/frontend/src/features/reviewer/components/__tests__/MappingResult.test.tsx`

- マッピング結果の表示確認
- フィルタリング機能の確認
- ダウンロード機能の確認

#### 4.2 バックエンドテスト

**ファイル**: `versions/v0.8.0/backend/tests/test_review.py`

```python
def test_review_mode_parameter():
    """モードパラメータのテスト"""
    # 突合モード（デフォルト）
    response = client.post("/api/review", json={...})
    assert response.status_code == 200

    # マッピングモード
    response = client.post("/api/review", json={..., "mode": "mapping"})
    assert response.status_code == 200

def test_mapping_user_message():
    """マッピング用ユーザーメッセージの生成テスト"""
    request = ReviewRequest(..., mode=ReviewMode.MAPPING)
    message = build_user_message(request, mode=request.mode)
    assert "マッピング" in message
```

---

## ファイル変更一覧

### 新規作成

| ファイルパス | 説明 |
|-------------|------|
| `versions/v0.8.0/` | v0.7.0からコピー |
| `frontend/src/features/reviewer/components/ModeSelector.tsx` | モード切り替えUI |
| `frontend/src/features/reviewer/components/MappingResult.tsx` | マッピング結果表示 |
| `frontend/src/features/reviewer/components/__tests__/ModeSelector.test.tsx` | テスト |
| `frontend/src/features/reviewer/components/__tests__/MappingResult.test.tsx` | テスト |

### 変更

| ファイルパス | 変更内容 |
|-------------|---------|
| `frontend/src/core/types/index.ts` | `ReviewMode` 型追加 |
| `frontend/src/core/data/presetCatalog.ts` | `MAPPING_PRESET` 追加 |
| `frontend/src/features/reviewer/types/index.ts` | マッピング関連型追加 |
| `frontend/src/features/reviewer/hooks/useReviewerSettings.ts` | モード状態管理追加 |
| `frontend/src/features/reviewer/hooks/useReviewExecution.ts` | モードパラメータ対応 |
| `frontend/src/features/reviewer/services/api.ts` | リクエストにモード追加 |
| `frontend/src/features/reviewer/index.tsx` | モード切り替えUI統合 |
| `backend/app/models/schemas.py` | `ReviewMode` enum追加 |
| `backend/app/services/prompt_builder.py` | マッピング用メッセージ構築 |
| `backend/app/routers/review.py` | モードパラメータ対応 |
| `backend/tests/test_review.py` | マッピングモードテスト追加 |

### 設定ファイル更新

| ファイルパス | 変更内容 |
|-------------|---------|
| `versions/v0.8.0/backend/pyproject.toml` | version = "0.8.0" |
| `versions/v0.8.0/frontend/package.json` | version: "0.8.0" |
| `docker-compose.yml` | v0.8.0 追加 |
| `nginx/version-map.conf` | v0.8.0 ルーティング追加 |
| `ecosystem.config.js` | v0.8.0 追加 |
| `dev.ecosystem.config.js` | v0.8.0 追加 |
| `versions/README.md` | v0.8.0 情報追加 |
| `README.md` | ポートテーブル更新 |
| `CHANGELOG.md` | v0.8.0 変更履歴追加 |
| `latest` シンボリックリンク | v0.8.0 へ更新 |

---

## UI設計

### メイン画面（モード切り替え追加）

```
┌─────────────────────────────────────────────────────────────┐
│ [Settings]                          spec-code-ai-reviewer   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┬─────────────────────┐             │
│  │    突合モード        │   マッピングモード    │  ← 新規追加 │
│  │ 設計書とコードの     │ 設計項目と実装箇所   │             │
│  │ 整合性を検証        │ を対応付け          │             │
│  └─────────────────────┴─────────────────────┘             │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 設計書アップロード                                    │   │
│  │ ...                                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ プログラムアップロード                                │   │
│  │ ...                                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ プリセット選択（突合モード時のみ表示）                │   │
│  │ ...                                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ システムプロンプト（編集可能）                        │   │
│  │ ...                                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│              [ 実行 ]                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### マッピング結果画面

```
┌─────────────────────────────────────────────────────────────┐
│ マッピング結果                                    ← 戻る    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┬─────────────┐                              │
│  │   1回目     │    2回目    │                              │
│  └─────────────┴─────────────┘                              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ マッピングサマリー                                    │   │
│  │ ┌───────────────────────────────────────────────┐   │   │
│  │ │ 総件数: 25件                                   │   │   │
│  │ │ 高確信: 18件 | 中確信: 5件 | 低確信: 2件        │   │   │
│  │ │ 未マッピング: 3件                              │   │   │
│  │ └───────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ フィルタ: [全て] [高確信] [中確信] [低確信] [未マッピング] │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ マッピング一覧                                        │   │
│  │ ┌──────────┬──────────┬────────────┬────────┬──────┐│   │
│  │ │設計書項目 │設計内容   │実装ファイル:行│実装要素 │確信度││   │
│  │ ├──────────┼──────────┼────────────┼────────┼──────┤│   │
│  │ │1.1 ログイン│ユーザー認証│auth.ts:45-80│login() │ 高  ││   │
│  │ │1.2 ログアウト│セッション破棄│auth.ts:82-95│logout()│ 高 ││   │
│  │ │...        │...       │...         │...     │...   ││   │
│  │ └──────────┴──────────┴────────────┴────────┴──────┘│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 詳細レポート                                          │   │
│  │ ...（Markdownプレビュー）                             │   │
│  │                            [ コピー ] [ ダウンロード ] │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 一式ダウンロード (ZIP)                                │   │
│  │                            [ 一式ダウンロード ]        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 実装順序

1. **Phase 1**: バージョン準備（v0.8.0作成、設定ファイル更新）
2. **Phase 2**: バックエンド実装（スキーマ、プロンプトビルダー、API）
3. **Phase 3**: フロントエンド実装（型定義、コンポーネント、状態管理）
4. **Phase 4**: テスト実装・動作確認
5. **Phase 5**: ドキュメント更新（README、CHANGELOG）

---

## 今後の拡張案

1. **マッピング結果のエクスポート形式追加**
   - CSV形式でのエクスポート
   - Excel形式でのエクスポート（トレーサビリティマトリクス）

2. **マッピングの可視化**
   - 設計書項目とコード位置の関係図（Mermaid等）
   - コードカバレッジ風の表示

3. **差分マッピング**
   - 前回マッピング結果との差分表示
   - 設計変更・コード変更の影響分析

4. **双方向マッピング**
   - 「このコードはどの設計項目に対応するか」の逆引き機能

---

## 参考

- [v0.7.0 spec.md](../versions/v0.7.0/spec.md)
- [プリセットカタログ](../versions/v0.7.0/frontend/src/core/data/presetCatalog.ts)
- [レビュー結果コンポーネント](../versions/v0.7.0/frontend/src/features/reviewer/components/ReviewResult.tsx)
