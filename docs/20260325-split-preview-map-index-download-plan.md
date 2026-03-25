# 分割プレビュー画面でのMAP.json・INDEX.mdダウンロード機能 修正計画書

## 概要

分割レビューの分割プレビュー実行後、レビュー開始前の分割設定画面で設計書・コードの **MAP.json** と **INDEX.md** を個別にダウンロードできるようにする。

対応 Issue: [#73](https://github.com/elvezjp/spec-code-ai-reviewer/issues/73)

## 背景

現状、MAP.json と INDEX.md の内容を確認できるのは **レビュー完了後にダウンロードできるzip一式**（`split/spec-MAP.json`, `split/spec-INDEX.md`, `split/code-MAP.json`, `split/code-INDEX.md`）のみである。

分割プレビューの段階でこれらのファイルを確認したいケース（INDEX.md の構造やサマリーの確認、MAP.json のセクション情報の検証など）があるが、レビューを最後まで実行してzipをダウンロードする必要があり、手間がかかる。

`SplitPreviewResult` には既に `documentIndex`, `documentMapJson`, `codeIndex`, `codeMapJson` が保持されているため、フロントエンド側にダウンロードボタンを追加するだけで実現可能。

## UX フロー

### 現状のフロー（v0.9.4）

```
分割プレビュー実行
→ プレビュー結果表示
  ■ 設計書: N パート
    [重要/要約/除外テーブル]
  ■ プログラム: N パート
    [シンボル一覧テーブル]
→ レビュー実行 → zip ダウンロード（ここで初めてMAP.json/INDEX.mdを確認可能）
```

### 改善後のフロー（v0.9.4）

```
分割プレビュー実行
→ プレビュー結果表示
  ■ 設計書: N パート  [INDEX.md ↓] [MAP.json ↓]     ← ダウンロードボタン追加
    [重要/要約/除外テーブル]
  ■ プログラム: N パート  [INDEX.md ↓] [MAP.json ↓]  ← ダウンロードボタン追加
    [シンボル一覧テーブル]
→ レビュー実行
```

### 変更後の画面イメージ

#### プレビュー結果: 設計書パーツ

```
│ ■ 設計書: 20 パート                  [INDEX.md ↓] [MAP.json ↓]  │
│                                                                   │
│ 重要 要約 除外  #  セクション名             行範囲  推定トークン    │
│ ┌──┬──┬──┬───┬────────────────────────┬────────┬──────────┐       │
│ │☐ │☐ │☐ │  1│ 概要                   │L1-L5   │    ~104  │       │
│ │☑ │☐ │☐ │  2│ 常駐処理設計書         │L8-L48  │    ~961  │       │
│ │  │  │  │   │ ...                    │        │          │       │
│ └──┴──┴──┴───┴────────────────────────┴────────┴──────────┘       │
```

#### プレビュー結果: コードパーツ

```
│ ■ プログラム: 8 パート (Python)      [INDEX.md ↓] [MAP.json ↓]   │
│                                                                   │
│  #  シンボル名                  種別       行範囲  推定トークン     │
│ ┌───┬──────────────────────────┬─────────┬────────┬──────────┐    │
│ │ 1 │ UserService              │ class   │L1-L50  │    ~800  │    │
│ │ 2 │ UserService#create_user  │ method  │L10-L30 │    ~300  │    │
│ └───┴──────────────────────────┴─────────┴────────┴──────────┘    │
```

- ダウンロードボタンはパーツ見出し（`■ 設計書: N パート`）の右側にインラインで配置
- 小さめのテキストリンクまたはアイコンボタンとして表示し、テーブルの視認性を妨げない
- ファイル名は zip ダウンロード時と同じ命名（`spec-INDEX.md`, `spec-MAP.json`, `code-INDEX.md`, `code-MAP.json`）

---

## 前提

- 現在の実装: `versions/v0.9.4`
- 同一バージョン（v0.9.4）上で修正を行う（新バージョンの作成は不要）
- バックエンド変更は不要（`SplitPreviewResult` に必要なデータは既に含まれている）
- 既存の zip ダウンロード機能（`useZipExport.ts`）には影響しない

---

## Step 1: フロントエンド — ダウンロードユーティリティ関数の追加

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.4/frontend/src/features/reviewer/components/SplitSettingsSection.tsx` | テキスト/JSONファイルのダウンロードヘルパー関数を追加 |

### 実装

```typescript
/**
 * テキストコンテンツをファイルとしてダウンロードする
 */
function downloadAsFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
```

※ `useZipExport.ts` で使用している JSZip とは異なり、単一ファイルのダウンロードなので Blob API で十分。
※ 既に同等のユーティリティが存在する場合はそちらを利用する。

---

## Step 2: フロントエンド — 設計書パーツ見出しにダウンロードボタンを追加

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.4/frontend/src/features/reviewer/components/SplitSettingsSection.tsx` | 設計書パーツ見出し（`■ 設計書: N パート`）の右側に INDEX.md / MAP.json ダウンロードボタンを追加 |

### 変更箇所

`SplitSettingsSection` の設計書パーツ表示部分（現在 L304-L327 付近）:

```tsx
{/* 変更前 */}
<h4 className="text-sm font-medium text-gray-600 mb-2">
  ■ 設計書: {previewResult.documentParts.length} パート
</h4>

{/* 変更後 */}
<h4 className="text-sm font-medium text-gray-600 mb-2 flex items-center gap-3">
  <span>■ 設計書: {previewResult.documentParts.length} パート</span>
  {previewResult.documentIndex && (
    <button
      type="button"
      onClick={() => downloadAsFile(previewResult.documentIndex!, 'spec-INDEX.md', 'text/markdown')}
      className="text-xs text-blue-600 hover:text-blue-800 hover:underline"
    >
      INDEX.md ↓
    </button>
  )}
  {previewResult.documentMapJson && (
    <button
      type="button"
      onClick={() => downloadAsFile(
        JSON.stringify(previewResult.documentMapJson, null, 2),
        'spec-MAP.json',
        'application/json'
      )}
      className="text-xs text-blue-600 hover:text-blue-800 hover:underline"
    >
      MAP.json ↓
    </button>
  )}
</h4>
```

- `documentIndex` / `documentMapJson` が null でない場合のみボタンを表示
- MAP.json は `JSON.stringify` で整形して出力

---

## Step 3: フロントエンド — コードパーツ見出しにダウンロードボタンを追加

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.4/frontend/src/features/reviewer/components/SplitSettingsSection.tsx` | コードパーツ見出し（`■ プログラム: N パート`）の右側に INDEX.md / MAP.json ダウンロードボタンを追加 |

### 変更箇所

`SplitSettingsSection` のコードパーツ表示部分（現在 L333-L340 付近）:

```tsx
{/* 変更前 */}
<h4 className="text-sm font-medium text-gray-600 mb-2">
  ■ プログラム: {previewResult.codeParts.length} パート
  {previewResult.codeLanguage && (
    <span className="ml-2 text-xs text-gray-500">
      ({previewResult.codeLanguage})
    </span>
  )}
</h4>

{/* 変更後 */}
<h4 className="text-sm font-medium text-gray-600 mb-2 flex items-center gap-3">
  <span>
    ■ プログラム: {previewResult.codeParts.length} パート
    {previewResult.codeLanguage && (
      <span className="ml-2 text-xs text-gray-500">
        ({previewResult.codeLanguage})
      </span>
    )}
  </span>
  {previewResult.codeIndex && (
    <button
      type="button"
      onClick={() => downloadAsFile(previewResult.codeIndex!, 'code-INDEX.md', 'text/markdown')}
      className="text-xs text-blue-600 hover:text-blue-800 hover:underline"
    >
      INDEX.md ↓
    </button>
  )}
  {previewResult.codeMapJson && (
    <button
      type="button"
      onClick={() => downloadAsFile(
        JSON.stringify(previewResult.codeMapJson, null, 2),
        'code-MAP.json',
        'application/json'
      )}
      className="text-xs text-blue-600 hover:text-blue-800 hover:underline"
    >
      MAP.json ↓
    </button>
  )}
</h4>
```

---

## Step 4: テストの追加

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.4/frontend/src/__tests__/` | ダウンロードボタンの表示・非表示、クリック時の動作テスト |

### テストケース

| ケース | 内容 |
|---|---|
| 設計書ダウンロードボタンの表示 | `documentIndex` / `documentMapJson` が存在する場合、INDEX.md / MAP.json ボタンが表示される |
| 設計書ダウンロードボタンの非表示 | `documentIndex` / `documentMapJson` が null の場合、ボタンが表示されない |
| コードダウンロードボタンの表示 | `codeIndex` / `codeMapJson` が存在する場合、INDEX.md / MAP.json ボタンが表示される |
| コードダウンロードボタンの非表示 | `codeIndex` / `codeMapJson` が null の場合、ボタンが表示されない |
| ダウンロード関数の呼び出し | ボタンクリック時に適切なファイル名・内容でダウンロードが実行される |

---

## 修正順序と依存関係

```
Step 1: ダウンロードユーティリティ関数の追加
  ↓
Step 2: 設計書パーツ見出しにダウンロードボタン追加（Step 1 の関数を利用）
  ↓
Step 3: コードパーツ見出しにダウンロードボタン追加（Step 1 の関数を利用）
  ↓
Step 4: テスト追加
```

※ Step 2 と Step 3 は同一ファイル内の修正だが、独立した変更であるため並行実施可能。

---

## 影響範囲

| 対象 | 影響 |
|---|---|
| md2map | 変更なし |
| バックエンド | 変更なし |
| フロントエンド | `SplitSettingsSection.tsx` のみ修正。`downloadAsFile` ヘルパー関数追加、設計書・コードパーツ見出しにダウンロードボタン追加 |
| `useZipExport.ts` | 変更なし（既存の zip ダウンロード機能に影響なし） |
| code2map | 変更なし |
| ドキュメント | 変更なし（軽微なUI追加のため spec.md / split-review.md の更新は不要） |

---

## 関連

- Issue: [#73 分割プレビュー画面でMAP.json・INDEX.mdをダウンロード可能にする](https://github.com/elvezjp/spec-code-ai-reviewer/issues/73)
- サマリーモードオプション計画書: [20260325-summary-mode-options-plan.md](20260325-summary-mode-options-plan.md)
- 分割レビュー仕様書: [split-review.md](split-review.md)

---

## 完了チェックリスト

### Step 1: ダウンロードユーティリティ関数

- [x] `downloadAsFile()` ヘルパー関数を `SplitSettingsSection.tsx` に追加

### Step 2: 設計書パーツのダウンロードボタン

- [x] 設計書パーツ見出しに `INDEX.md ↓` ボタンを追加
- [x] 設計書パーツ見出しに `MAP.json ↓` ボタンを追加
- [x] `documentIndex` / `documentMapJson` が null の場合は非表示

### Step 3: コードパーツのダウンロードボタン

- [x] コードパーツ見出しに `INDEX.md ↓` ボタンを追加
- [x] コードパーツ見出しに `MAP.json ↓` ボタンを追加
- [x] `codeIndex` / `codeMapJson` が null の場合は非表示

### Step 4: テスト追加

- [x] フロントエンドテスト追加・全テスト通過（180件）

### 最終確認

- [x] 全フロントエンドテスト通過（180件）
- [ ] 手動動作確認（分割プレビュー → ダウンロードボタン表示 → ファイルダウンロード → 内容確認）
