# プリセットライブラリ実装計画

## 目的
- システムプロンプト/設定の「プリセット集」を提供し、ワンクリックで適用可能にする。
- 自由度とシンプルさを両立し、学習効果も得られる体験を作る。

## スコープ
- **対象**: v0.6.0 フロントエンド（React + Vite）
- **対象外**: ユーザープリセット保存機能（製品版で実装）

## 成果物
- プリセットの型定義と初期カタログ
- プリセット選択UI（専用ページ）
- 選択したプリセットの即時適用
- タグ/フィルタリング、プレビュー

## データ構造定義

### Preset 型

```typescript
interface Preset {
  id: string                        // 一意識別子（例: 'spring-boot-api'）
  name: string                      // 表示名（例: 'Spring Boot REST API'）
  description: string               // 説明文（1-2行）
  tags: string[]                    // タグ（例: ['Java', 'Spring', 'Web']）
  systemPrompt: PresetPrompt        // システムプロンプト（プリセット専用型）
  specTypes: SpecType[]             // 設計書種別リスト（既存型）
}
```

**既存型との関係**:
- `PresetPrompt` は `SystemPromptPreset` とは別の簡易型（`name` なし）
- `SpecType`: `src/core/types/index.ts` で既に定義済み
- `Preset` は `PresetPrompt` + `SpecType[]` を組み合わせた上位構造

```typescript
interface PresetPrompt {
  role: string
  purpose: string
  format: string
  notes: string
}
```

## フェーズ構成

### Phase 1: データ構造とプリセット定義
**目的**: プリセットの表現と初期データを確立する。

- 追加: 型定義（`src/core/types/index.ts`）
  - `Preset` 型（id, name, description, tags, systemPrompt, specTypes など）
  - `PresetPrompt` 型の追加（`SystemPromptPreset` とは別型）
  - 既存 `SpecType` との関係整理

- 追加: プリセットカタログ（新規ファイル）
  - **配置場所**: `src/core/data/presetCatalog.ts`
  - 初期プリセット（3-5個）を定義:
    - Spring Boot REST API
    - React/TypeScript コンポーネント
    - セキュリティレビュー
    - パフォーマンスレビュー

**成果物**
- `Preset` 型定義（`src/core/types/index.ts`）
- `PRESET_CATALOG` 定義（`src/core/data/presetCatalog.ts`）

### Phase 2: プリセット管理機能
**目的**: UIからプリセットを選び、設定に反映できるようにする。

- 追加: プリセット用Hook（`src/core/hooks/usePresetCatalog.ts`）
  - プリセット一覧の取得
  - タグ/キーワードによるフィルタリング
  - 検索機能

- 変更: `useReviewerSettings` に以下を追加（`src/features/reviewer/hooks/useReviewerSettings.ts`）
  - `applyPreset(preset: Preset): void` メソッド
    - `preset.systemPrompt` を `SystemPromptPreset` に変換して適用
    - `preset.specTypes` を適用
    - localStorage に保存（既存の保存ロジックを利用）

- 変更: ルーティング（`App.tsx`）
  - `/presets` ルートを追加
  - 対応ページ: `src/pages/PresetsPage.tsx`

- 変更: ナビゲーション（`src/core/components/ui/Header.tsx`）
  - 「プリセット」リンクをヘッダーに追加
  - アイコン: `BookOpen` (lucide-react)

- 追加: プリセット選択UI（`src/pages/PresetsPage.tsx`）
  - プリセット一覧をカード形式で表示
  - 各カードに「このプリセットを使う」ボタン

**UXフロー**:
1. ユーザーが `/presets` でプリセットを選択
2. 「このプリセットを使う」ボタンをクリック
3. 設定に即反映（`useSettings.applyPreset()` 呼び出し）
4. トースト通知「プリセット "○○" を適用しました」（オプション）
5. `/` (レビュー画面) に自動遷移

**成果物**
- `usePresetCatalog` Hook
- `useReviewerSettings.applyPreset()` メソッド
- `/presets` ページ（PresetsPage.tsx）
- ヘッダーナビゲーション追加

### Phase 3: UX改善
**目的**: 探しやすく、適用前に理解できる体験を追加する。

- タグ/キーワードによるフィルタリング
- プレビュー表示（systemPrompt/specTypes の概要）

**成果物**
- フィルタUI
- プレビューUI

## 影響範囲
- **型定義**: `src/core/types/index.ts` - `Preset` 型追加
- **データ**: `src/core/data/presetCatalog.ts` - プリセット定義（新規ファイル）
- **Hooks**:
  - `src/core/hooks/usePresetCatalog.ts` - プリセット管理（新規）
  - `src/features/reviewer/hooks/useReviewerSettings.ts` - `applyPreset()` メソッド追加
- **ルーティング**: `src/App.tsx` - `/presets` ルート追加
- **ページ**: `src/pages/PresetsPage.tsx` - プリセット選択画面（新規）
- **ナビゲーション**: `src/core/components/ui/Header.tsx` - プリセットリンク追加
- **UI部品（Phase 3）**: タグコンポーネント、フィルタUI追加の可能性

## 非機能要件
- 既存のレビュー機能を壊さない
- 既存の設定ファイル生成フローに干渉しない

## 受け入れ条件
- `/presets` からプリセットを選び、レビュー画面の設定に即反映される
- 既存の手動設定も引き続き可能
- フィルタとプレビューで内容確認ができる

## テスト戦略

### Phase 1
- 型定義の TypeScript コンパイル確認
- プリセットデータの完全性検証（必須フィールド有無、スキーマ一致）

### Phase 2
- **Hook テスト**（Vitest）:
  - `usePresetCatalog`: フィルタリング、検索機能のテスト
  - `useSettings.applyPreset()`: 設定への反映、localStorage保存のテスト
- **UI動作テスト**（React Testing Library）:
  - プリセット選択 → 適用フロー
  - ルーティング動作（`/presets` → `/`）

### Phase 3
- フィルタ/プレビューUI の動作テスト

## 今回の除外
- ユーザープリセット保存機能（localStorage/設定ファイルへの保存）
- プリセットの編集・削除機能
- プリセットのインポート/エクスポート機能


## 試験項目

### 1. プリセット選択機能テスト

- [ ] **1-1: プリセットドロップダウン表示**
  - 手順: レビュー画面で「システムプロンプト設定」を展開
  - 期待結果: プリセットドロップダウンにカタログのプリセットが表示される

- [ ] **1-2: プリセット選択時のプロンプト更新**
  - 手順: ドロップダウンからプリセットを選択
  - 期待結果: 役割・目的・出力形式・注意事項が選択したプリセットの内容に更新される

- [ ] **1-3: プリセット選択時の設計書種別**
  - 手順: ドロップダウンからプリセットを選択
  - 期待結果: 設計書種別は変更されない（システムプロンプトのみ更新）

- [ ] **1-4: プリセット選択のlocalStorage保存**
  - 手順: プリセットを選択後、ブラウザを更新
  - 期待結果: 選択したプリセットが復元される

### 2. 設定クリア機能テスト

- [ ] **2-1: 設定クリアの確認ダイアログ**
  - 手順: 設定モーダルで「保存した設定をクリア」をクリック
  - 期待結果: 確認ダイアログが表示される

- [ ] **2-2: 設定クリア実行**
  - 手順: 確認ダイアログで「OK」をクリック
  - 期待結果: 以下がクリアされる: `reviewer-config`, `selected-model`, `selected-system-prompt`

- [ ] **2-3: クリア後のプリセット状態**
  - 手順: 設定クリア後
  - 期待結果: デフォルトプリセット（標準レビュープリセット）が選択状態になる

- [ ] **2-4: クリア後のプロンプト値**
  - 手順: 設定クリア後
  - 期待結果: 役割・目的・出力形式・注意事項がデフォルトプリセットの値になる

### 3. プリセット画面からの適用テスト

- [ ] **3-1: プリセット適用ボタン**
  - 手順: `/presets` でプリセットの「このプリセットを使う」をクリック
  - 期待結果: レビュー画面に遷移し、トースト「プリセット「〇〇」を適用しました」が表示される

- [ ] **3-2: 適用後のシステムプロンプト**
  - 手順: プリセット適用後、レビュー画面でシステムプロンプト設定を確認
  - 期待結果: 適用したプリセットのプロンプトが設定されている

- [ ] **3-3: 適用後の設計書種別**
  - 手順: プリセット適用後、設定モーダルで設計書種別を確認
  - 期待結果: 適用したプリセットの設計書種別が設定されている

- [ ] **3-4: 適用後のlocalStorage**
  - 手順: プリセット適用後
  - 期待結果: `reviewer-config` と `selected-system-prompt` がlocalStorageに保存される

### 4. 設定ファイル読み込みとの併用テスト

- [ ] **4-1: 設定ファイルのプリセット表示**
  - 手順: 設定ファイル（SystemPrompts定義あり）を読み込み
  - 期待結果: プリセットドロップダウンに「〇〇 (設定ファイル)」形式で表示される

- [ ] **4-2: 設定ファイルプリセットの選択**
  - 手順: 設定ファイルのプリセットを選択
  - 期待結果: プロンプトが設定ファイルの内容に更新される

### 5. ブラウザ更新・再訪問テスト

- [ ] **5-1: 設定保存後の再訪問**
  - 手順: 設定を保存してブラウザを更新
  - 期待結果: 保存した設定（LLM、設計書種別、プロンプト選択）が復元される

- [ ] **5-2: プリセット選択のみの再訪問**
  - 手順: 設定ファイルなしでプリセットを選択し、ブラウザを更新
  - 期待結果: 選択したプリセットが復元される

- [ ] **5-3: 存在しないプリセットの復元**
  - 手順: localStorageに存在しないプリセット名を設定し、画面を開く
  - 期待結果: デフォルトプリセットにフォールバックする

### 6. レビュー実行・結果ダウンロードテスト

- [ ] **6-1: プリセット適用後のレビュー実行**
  - 手順: プリセットを選択し、設計書とコードをアップロードしてレビューを実行
  - 期待結果: レビューが正常に実行され、結果が表示される

- [ ] **6-2: ダウンロード結果にシステムプロンプトが含まれる**
  - 手順: レビュー実行後、結果をダウンロード（Markdown形式）
  - 期待結果: ダウンロードしたファイルに選択したプリセットのシステムプロンプト（役割・目的・出力形式・注意事項）が含まれている

