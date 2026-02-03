# マッピングモード実装計画書

## 概要

設計書の項目とソースコードの実装箇所（ファイル、クラス、関数、行番号）を対応付ける「マッピングモード」を追加する。

既存の「突合モード」が設計書とコードの整合性検証に焦点を当てているのに対し、マッピングモードは「設計書のどの項目が、ソースコードのどこで実装されているか」を明確にすることに特化する。

## 要件

### 機能要件

1. **モード切り替え**
   - 画面上部でタブによる切り替え（突合モード / マッピングモード）
   - 選択中のモードはlocalStorageに保存（既存のLLMモデル・プリセット選択と同様）
   - 初期表示はlocalStorageから復元、未設定時は突合モード

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

// マッピング用簡易判定の型
export type MappingStatus = 'ok' | 'warning' | 'ng'

export interface SimpleMappingJudgment {
  status: MappingStatus
  designItemCount: number   // 設計書項目件数
  mappedCount: number       // マッピングできた件数
  unmappedCount: number     // 未マッピング件数
  coveragePercent: number   // カバレッジ率（0-100）
}

// ※ 以下は将来の拡張用（AIレスポンスをパースして構造化する場合）
// export interface MappingItem {
//   designSection: string      // 設計書の項目（見出し番号/項目名）
//   designContent: string      // 設計書の内容要約
//   codeLocation: string       // 実装箇所（ファイル名:行番号）
//   codeElement: string        // 実装要素（クラス名/関数名）
//   confidence: 'high' | 'medium' | 'low'  // 確信度
//   notes?: string             // 備考
// }
```

#### 2.2 プリセットカタログの再構成

**ファイル**: `versions/v0.8.0/frontend/src/core/data/presetCatalog.ts`

既存の `PRESET_CATALOG` を突合用・マッピング用に分離し、統合したカタログを提供する。

```typescript
import type { Preset } from '../types'

// デフォルトプリセットのID
export const DEFAULT_REVIEW_PRESET_ID = 'standard-review'
export const DEFAULT_MAPPING_PRESET_ID = 'standard-mapping'

// 後方互換のため維持
export const DEFAULT_PRESET_ID = DEFAULT_REVIEW_PRESET_ID

// ========================================
// 突合用プリセットカタログ
// ========================================
export const REVIEW_PRESET_CATALOG: Preset[] = [
  {
    id: 'standard-review',
    name: '標準レビュープリセット',
    description:
      '設計書とプログラムコードを突合し、整合性を検証する汎用的なレビューを行います。',
    tags: ['突合', '汎用', '設計書'],  // '突合' タグを追加
    systemPrompt: {
      // 既存の standard-review と同一
      role: 'あなたは設計書とプログラムコードを突合し、整合性を検証するレビュアーです。',
      purpose: `設計書の内容がプログラムに正しく実装されているかを検証し、差異や問題点を報告してください。
...（既存の内容）`,
      format: `...（既存の内容）`,
      notes: `...（既存の内容）`,
    },
    specTypes: [
      // 既存の specTypes と同一
    ],
  },
  {
    id: 'react-component',
    name: 'React/TypeScript コンポーネント',
    description: '...',
    tags: ['突合', 'React', 'TypeScript', 'フロントエンド'],  // '突合' タグを追加
    // ...既存の内容
  },
  // ... 他の既存プリセット（すべてのtagsに '突合' を追加）
]

// ========================================
// マッピング用プリセットカタログ
// ========================================
export const MAPPING_PRESET_CATALOG: Preset[] = [
  {
    id: 'standard-mapping',
    name: '標準マッピングプリセット',
    description: '設計書の各項目がソースコードのどこで実装されているかを特定します。',
    tags: ['マッピング', '汎用', '設計書', 'トレーサビリティ'],
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
  },
  {
    id: 'api-mapping',
    name: 'API エンドポイントマッピング',
    description: 'API仕様書とコントローラー/ルーター実装のマッピングを行います。',
    tags: ['マッピング', 'API', 'REST', 'OpenAPI'],
    systemPrompt: {
      role: 'あなたはAPI仕様とバックエンド実装のマッピングを行う専門家です。',
      purpose: `API仕様書（OpenAPI/Swagger等）の各エンドポイント定義がソースコードのどこで実装されているかを特定してください。

以下の情報を特定してください：
1. APIエンドポイント（HTTPメソッド + パス）
2. 実装箇所（コントローラー/ルーターファイル、行番号）
3. ハンドラー関数名
4. 関連するミドルウェア・バリデーション`,
      format: `マークダウン形式で、以下の順に出力してください：

1. **APIマッピングサマリー**
   - 対象API数
   - 実装済み/未実装の内訳

2. **エンドポイントマッピング一覧**
| メソッド | パス | 実装ファイル:行 | ハンドラー | ミドルウェア | 備考 |
|---------|-----|----------------|-----------|-------------|------|

3. **未実装エンドポイント**
   - 仕様書にあるが実装が見つからないエンドポイント`,
      notes: `- HTTPメソッド（GET/POST/PUT/DELETE等）を明示してください
- ルーティング定義とハンドラー実装の両方を特定してください
- 認証・認可ミドルウェアの適用状況も記載してください`,
    },
    specTypes: [
      { type: 'OpenAPI仕様書', note: '各エンドポイントの実装箇所を特定してください' },
      { type: 'API設計書', note: '各APIの実装箇所を特定してください' },
    ],
  },
  {
    id: 'database-mapping',
    name: 'データベーススキーママッピング',
    description: 'ER図/テーブル定義とモデル/エンティティ実装のマッピングを行います。',
    tags: ['マッピング', 'データベース', 'SQL', 'ORM'],
    systemPrompt: {
      role: 'あなたはデータベース設計と実装のマッピングを行う専門家です。',
      purpose: `データベース設計書（ER図、テーブル定義）の各テーブル/カラムがソースコードのモデル/エンティティとしてどこで定義されているかを特定してください。`,
      format: `マークダウン形式で、以下の順に出力してください：

1. **テーブルマッピング一覧**
| テーブル名 | モデル/エンティティ | 実装ファイル:行 | 備考 |
|-----------|-------------------|----------------|------|

2. **カラムマッピング詳細**（テーブルごと）

3. **リレーション実装状況**`,
      notes: `- ORM（Prisma/TypeORM/SQLAlchemy等）の定義形式を考慮してください
- マイグレーションファイルとの対応も確認してください`,
    },
    specTypes: [
      { type: 'ER図', note: '各テーブルの実装箇所を特定してください' },
      { type: 'テーブル定義書', note: '各カラムの実装箇所を特定してください' },
    ],
  },
]

// ========================================
// 統合プリセットカタログ（突合 + マッピング）
// ========================================
export const PRESET_CATALOG: Preset[] = [
  ...REVIEW_PRESET_CATALOG,
  ...MAPPING_PRESET_CATALOG,
]

// ========================================
// ヘルパー関数
// ========================================

/**
 * モードに応じたプリセットカタログを取得
 */
export function getPresetCatalogByMode(mode: ReviewMode): Preset[] {
  if (mode === 'mapping') {
    return MAPPING_PRESET_CATALOG
  }
  return REVIEW_PRESET_CATALOG
}

/**
 * モードに応じたデフォルトプリセットIDを取得
 */
export function getDefaultPresetIdByMode(mode: ReviewMode): string {
  if (mode === 'mapping') {
    return DEFAULT_MAPPING_PRESET_ID
  }
  return DEFAULT_REVIEW_PRESET_ID
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

#### 2.4 結果表示コンポーネントの共通化

既存の `ReviewResult.tsx` をベースに、突合モード・マッピングモード両対応の共通コンポーネントとして拡張する。

**共通化方針**:

- **見出しの共通化**: モードによらず同じ見出しを使用
  - 「レビュー情報」「マッピング情報」→「実行情報」
  - 「レビュー実行データ一式ダウンロード」「マッピング実行データ一式ダウンロード」→「実行データ一式ダウンロード」

- **各セクションの共通化方針**:
  | セクション | 共通化 | カスタマイズ内容 |
  |-----------|-------|----------------|
  | ヘッダー + タブ切り替え | 完全共通 | なし |
  | 簡易判定 | 構造共通 | 判定ロジックとステータス表示内容のみモード別 |
  | 実行情報 | 完全共通 | なし（見出しを共通化） |
  | 詳細レポート | 完全共通 | なし |
  | 実行データ一式ダウンロード | ほぼ共通 | ZIPファイル名のみモード別（`review-result.md` / `mapping-result.md`） |

- **簡易判定のモード別表示**:
  - 突合モード: 既存の `ng`/`warning`/`ok` 判定（不整合キーワード検索）
  - マッピングモード: カバレッジ率による `ng`/`warning`/`ok` 判定

```typescript
// 簡易判定のステータス定義（マッピング用）
// 突合モードと同じステータス名・色を使用
const mappingStatusConfig = {
  ok: {
    label: '問題なし',
    icon: <CheckCircle className="w-6 h-6 text-green-600" />,
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-700',
    iconBg: 'bg-green-100',
  },
  warning: {
    label: '確認が必要',
    icon: <AlertTriangle className="w-6 h-6 text-yellow-600" />,
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    textColor: 'text-yellow-700',
    iconBg: 'bg-yellow-100',
  },
  ng: {
    label: '問題あり',
    icon: <XCircle className="w-6 h-6 text-red-600" />,
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    textColor: 'text-red-700',
    iconBg: 'bg-red-100',
  },
}

// 簡易判定の表示
const renderSimpleMappingJudgment = (judgment: SimpleMappingJudgment) => {
  const config = mappingStatusConfig[judgment.status]
  return (
    <div className={`${config.bgColor} ${config.borderColor} border rounded-lg p-4`}>
      <div className="flex items-center gap-3">
        <span className={`${config.iconBg} rounded-full p-2`}>{config.icon}</span>
        <div>
          <div className={`font-bold ${config.textColor} text-lg`}>
            マッピングカバレッジ: {judgment.coveragePercent}%
          </div>
          <div className="text-sm text-gray-600">
            設計書項目: {judgment.designItemCount}件 /
            マッピング: {judgment.mappedCount}件 /
            未マッピング: {judgment.unmappedCount}件
          </div>
        </div>
      </div>
    </div>
  )
}
```

#### 2.5 状態管理の拡張

**ファイル**: `versions/v0.8.0/frontend/src/core/hooks/useSettings.ts`

localStorageにモードを保存する機能を追加（既存のLLMモデル・プリセット選択と同様の方式）。

```typescript
// ストレージキーの定義
const STORAGE_KEY = 'reviewer-config'

interface ReviewerConfig {
  // 既存フィールド
  llmConfig?: LlmConfig
  selectedModel?: string
  selectedPresetId?: string
  // 新規追加
  reviewMode?: ReviewMode  // 'review' | 'mapping'
}

export function useSettings() {
  // 既存のstate...

  // モード状態をlocalStorageから復元
  const [reviewMode, setReviewMode] = useState<ReviewMode>(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const config = JSON.parse(saved) as ReviewerConfig
      return config.reviewMode ?? 'review'
    }
    return 'review'
  })

  // モード変更時にlocalStorageに保存
  const updateReviewMode = useCallback((mode: ReviewMode) => {
    setReviewMode(mode)
    const saved = localStorage.getItem(STORAGE_KEY)
    const config = saved ? JSON.parse(saved) : {}
    config.reviewMode = mode
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config))
  }, [])

  return {
    // 既存の返却値...
    reviewMode,
    updateReviewMode,
  }
}
```

**ファイル**: `versions/v0.8.0/frontend/src/features/reviewer/hooks/useReviewerSettings.ts`

モード変更時のプリセット自動切り替えロジック。

```typescript
import {
  getPresetCatalogByMode,
  getDefaultPresetIdByMode
} from '@core/data/presetCatalog'

// useSettings から reviewMode, updateReviewMode を取得
const { reviewMode, updateReviewMode, ...settings } = useSettings()

// モードに応じたプリセットカタログを取得
const availablePresets = useMemo(
  () => getPresetCatalogByMode(reviewMode),
  [reviewMode]
)

// モード変更ハンドラー
const handleModeChange = useCallback((mode: ReviewMode) => {
  updateReviewMode(mode)

  // モードに応じたデフォルトプリセットを自動適用
  const defaultPresetId = getDefaultPresetIdByMode(mode)
  const defaultPreset = getPresetById(defaultPresetId)
  if (defaultPreset) {
    applyPreset(defaultPreset)
  }
}, [updateReviewMode, applyPreset])

return {
  // 既存の返却値...
  reviewMode,
  handleModeChange,
  availablePresets,  // モードに応じたプリセット一覧
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
- **プリセット選択UIは両モードで表示**（モードに応じたプリセット一覧を表示）

```typescript
export function Reviewer() {
  const {
    reviewMode,
    handleModeChange,
    availablePresets,  // モードに応じたプリセット一覧
    selectedPreset,
    applyPreset,
    // ...
  } = useReviewerSettings()

  return (
    <div>
      {/* モード切り替えUI */}
      <ModeSelector
        currentMode={reviewMode}
        onModeChange={handleModeChange}
      />

      {/* 設計書・プログラムアップロード（共通） */}
      {/* ... */}

      {/* プリセット選択（両モードで表示、モードに応じたプリセット一覧） */}
      <PresetSelector
        presets={availablePresets}
        selectedPreset={selectedPreset}
        onSelect={applyPreset}
      />

      {/* システムプロンプト編集（共通） */}
      {/* ... */}

      {/* 実行ボタン（共通） */}
      {/* ... */}
    </div>
  )
}
```

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
| `frontend/src/features/reviewer/components/__tests__/ModeSelector.test.tsx` | テスト |

### 変更

| ファイルパス | 変更内容 |
|-------------|---------|
| `frontend/src/core/types/index.ts` | `ReviewMode` 型追加 |
| `frontend/src/core/data/presetCatalog.ts` | 突合用/マッピング用カタログ分離、タグ追加、ヘルパー関数追加 |
| `frontend/src/core/hooks/useSettings.ts` | `reviewMode` のlocalStorage永続化追加 |
| `frontend/src/features/reviewer/types/index.ts` | マッピング関連型追加 |
| `frontend/src/features/reviewer/hooks/useReviewerSettings.ts` | モード切り替え、モード別プリセット一覧取得追加 |
| `frontend/src/features/reviewer/hooks/useReviewExecution.ts` | モードパラメータ対応 |
| `frontend/src/features/reviewer/services/api.ts` | リクエストにモード追加 |
| `frontend/src/features/reviewer/components/ReviewResult.tsx` | 両モード対応化（見出し共通化、簡易判定のモード別切り替え） |
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
│  │ プリセット選択（モードに応じたプリセット一覧を表示）   │   │
│  │ 突合モード時: 突合用プリセット一覧                    │   │
│  │ マッピングモード時: マッピング用プリセット一覧        │   │
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

### マッピング結果画面（突合モードと同一構成）

```
┌─────────────────────────────────────────────────────────────┐
│ マッピング結果                                    ← 戻る    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┬─────────────┐                              │
│  │   1回目     │    2回目    │                              │
│  └─────────────┴─────────────┘                              │
│  ※ 同じ設定で2回マッピングを実行しました                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 簡易判定                                                     │
│  ┌───────────────────────────────────────────────┐         │
│  │ [✓/△/✗] マッピングカバレッジ: 85%              │         │
│  │                                               │         │
│  │ 設計書項目: 20件                               │         │
│  │ マッピング: 17件 / 未マッピング: 3件            │         │
│  └───────────────────────────────────────────────┘         │
│  ※ キーワード検索による簡易的な判定です。                    │
│    詳細レポートを確認してください。                          │
│  ※ 設計書項目件数はAIの判定ごとに異なる場合があります。      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 実行情報                                                     │
│  バージョン:        v0.8.0                                  │
│  モデルID:          claude-haiku-...                        │
│  実行日時:          2026-02-03 12:34:56                     │
│  トークン数:        入力 1,234 / 出力 567                    │
│                                                             │
│  設計書:                                                     │
│  ┌──────────┬──────┬──────┬────────────┐                   │
│  │ファイル名 │ 役割 │ 種別 │   ツール   │                   │
│  ├──────────┼──────┼──────┼────────────┤                   │
│  │spec.xlsx │メイン│設計書│MarkItDown │                   │
│  └──────────┴──────┴──────┴────────────┘                   │
│                                                             │
│  プログラム:                                                 │
│  ┌──────────────────────────────────────┐                   │
│  │ファイル名                             │                   │
│  ├──────────────────────────────────────┤                   │
│  │main.ts                               │                   │
│  └──────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 📄 詳細レポート                                              │
│  ┌───────────────────────────────────────────────┐         │
│  │ (Markdownプレビュー: max-h-96でスクロール)     │         │
│  │ # マッピングサマリー                           │         │
│  │ ## マッピング一覧                              │         │
│  │ | 設計書項目 | 実装ファイル:行 | 実装要素 | ... │         │
│  │ ...                                           │         │
│  └───────────────────────────────────────────────┘         │
│                                                             │
│  ┌─────────────┐ ┌─────────────────┐                       │
│  │ 📋 コピー   │ │ 💾 ダウンロード │                       │
│  └─────────────┘ └─────────────────┘                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 📦 実行データ一式ダウンロード                                │
│                                                             │
│  実行の入出力データを一式ダウンロードできます                 │
│                                                             │
│  ダウンロード内容:                                           │
│  ┌────────────────────┬──────────────────────────┐         │
│  │ README.md          │ 実行情報と同梱説明     │         │
│  │ system-prompt.md   │ システムプロンプト       │         │
│  │ spec-markdown.md   │ 変換後の設計書           │         │
│  │ code-numbered.txt  │ 行番号付きプログラム     │         │
│  │ mapping-result.md  │ AIマッピング結果         │         │
│  └────────────────────┴──────────────────────────┘         │
│                                                             │
│  ┌─────────────────────────────────────────────┐           │
│  │       📥 一式ダウンロード（ZIP）            │           │
│  └─────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### マッピング用簡易判定のステータス

| ステータス | アイコン | 表示ラベル | 色 | 判定条件 |
|-----------|---------|-----------|-----|---------|
| `ok` | ✓ | 問題なし | 緑 | カバレッジ100%（未マッピング0件） |
| `warning` | △ | 確認が必要 | 黄 | カバレッジ1%〜99% |
| `ng` | ✗ | 問題あり | 赤 | カバレッジ0%、設計書項目0件、または判定不能 |

**判定ロジック（`getSimpleMappingJudgment`）**:
```typescript
interface SimpleMappingJudgment {
  status: 'ok' | 'warning' | 'ng'
  designItemCount: number   // 設計書項目件数
  mappedCount: number       // マッピングできた件数
  unmappedCount: number     // 未マッピング件数
  coveragePercent: number   // カバレッジ率（0-100）
}

function getSimpleMappingJudgment(reportText: string): SimpleMappingJudgment {
  // レポート内のキーワードからカウントを抽出
  // 1. 設計書項目件数: マッピング一覧テーブルの行数 + 未マッピング項目リストの件数
  // 2. マッピング件数: マッピング一覧テーブルの行数
  // 3. 未マッピング件数: 「未マッピング」セクションの項目数
  // 4. カバレッジ率: マッピング件数 / 設計書項目件数 * 100

  // ステータス判定:
  // - 判定不能（パース失敗等） → 'ng'
  // - 設計書項目件数が0 → 'ng'
  // - カバレッジ0% → 'ng'
  // - カバレッジ100% → 'ok'
  // - カバレッジ1-99% → 'warning'
}
```

**注記事項**:
- キーワード検索による簡易的な判定のため、AIの出力形式によっては正確に判定できない場合があります
- 判定できない場合は「問題あり」として表示されます
- 設計書項目件数はAIが設計書を解析して抽出するため、実行ごとに異なる場合があります
- 詳細な確認は「詳細レポート」セクションで行ってください

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

---

## プリセットカタログ設計の要点

### 定数名の変更

| 変更前 | 変更後 | 説明 |
|-------|-------|------|
| `PRESET_CATALOG` | `REVIEW_PRESET_CATALOG` | 突合用プリセットのみ |
| （新規） | `MAPPING_PRESET_CATALOG` | マッピング用プリセットのみ |
| （新規） | `PRESET_CATALOG` | 両カタログを結合（後方互換） |

### タグの追加

- **突合用プリセット**: 各プリセットの `tags` 配列に `'突合'` を追加
- **マッピング用プリセット**: 各プリセットの `tags` 配列に `'マッピング'` を追加

### ヘルパー関数

| 関数名 | 引数 | 返却値 | 説明 |
|-------|------|-------|------|
| `getPresetCatalogByMode(mode)` | `ReviewMode` | `Preset[]` | モードに応じたプリセット一覧 |
| `getDefaultPresetIdByMode(mode)` | `ReviewMode` | `string` | モードに応じたデフォルトプリセットID |

### localStorage永続化

| キー | フィールド | 型 | 説明 |
|-----|-----------|-----|------|
| `reviewer-config` | `reviewMode` | `'review' \| 'mapping'` | 選択中のモード |

既存の `llmConfig`, `selectedModel`, `selectedPresetId` と同じストレージキーを使用し、一貫した永続化方式を維持。

---

## コンポーネント共通化設計

### 見出しの共通化

結果画面の見出しを突合モード・マッピングモードで共通化し、コンポーネントの再利用性を高める。

| 変更前（突合） | 変更前（マッピング） | 変更後（共通） |
|--------------|-------------------|--------------|
| レビュー情報 | マッピング情報 | 実行情報 |
| レビュー実行データ一式ダウンロード | マッピング実行データ一式ダウンロード | 実行データ一式ダウンロード |

### セクション別の共通化方針

| セクション | 共通化レベル | 備考 |
|-----------|------------|------|
| ヘッダー + タブ切り替え | 完全共通 | 1回目/2回目の切り替えは両モード同一 |
| 簡易判定 | 構造共通・内容別 | 判定ロジックと表示内容のみモード別に切り替え |
| 実行情報 | 完全共通 | バージョン、モデルID、実行日時、トークン数、ファイル一覧 |
| 詳細レポート | 完全共通 | Markdownプレビュー、コピー、ダウンロード |
| 実行データ一式ダウンロード | ほぼ共通 | ZIPファイル名のみモード別 |

### 実装方針

- 既存の `ReviewResult.tsx` を拡張し、モードをpropsで受け取る形式に変更
- 簡易判定のみモードに応じた判定関数・表示コンポーネントを切り替え
- 新規ファイル `MappingResult.tsx` は作成せず、`ReviewResult.tsx` で両モード対応
- ファイル名は `ReviewResult.tsx` のまま維持（または `ExecutionResult.tsx` へリネーム検討）

---

## 参考

- [v0.7.0 spec.md](../versions/v0.7.0/spec.md)
- [プリセットカタログ](../versions/v0.7.0/frontend/src/core/data/presetCatalog.ts)
- [レビュー結果コンポーネント](../versions/v0.7.0/frontend/src/features/reviewer/components/ReviewResult.tsx)
- [useSettings.ts](../versions/v0.7.0/frontend/src/core/hooks/useSettings.ts)
