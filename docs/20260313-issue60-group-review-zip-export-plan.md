# 計画書: グループレビュー個別結果をZIPダウンロードに含める (issue#60)

## 概要

| # | タイトル | 種別 |
|---|---------|------|
| [#60](https://github.com/elvezjp/spec-code-ai-reviewer/issues/60) | 分割レビューのグループレビュー個別結果をZIPダウンロードに含める | enhancement |

レビュー実行結果画面のZIPダウンロード機能において、分割レビュー時のグループレビュー個別結果（各グループのMarkdownレポート）をZIPに含めるようにする。

対象バージョン: `versions/v0.9.1`

---

## 現状の問題整理

分割レビュー時のZIPには以下が含まれている:

**基本5ファイル:**
- `README.md`, `system-prompt.md`, `spec-markdown.md`, `code-numbered.txt`, `review-result.md`（統合結果）

**分割情報（splitフォルダ）:**
- `split/spec-INDEX.md`, `split/spec-MAP.json`, `split/code-INDEX.md`, `split/code-MAP.json`

**問題:** グループレビューの個別結果（各グループの `report` マークダウン）はZIPに含まれていない。統合結果のみでは、個々のグループでどのような指摘があったかを追跡できない。

---

## 修正方針

- 分割レビュー完了時のZIPに、各グループのレビュー結果を `split/review-result-{groupId}.md` として含める
- READMEの同梱ファイルテーブルにグループレビュー個別結果ファイルを動的に追加する
- 結果画面のダウンロード内容テーブルにもグループレビュー個別結果の表示を追加する
- バックエンド修正は不要（グループレビュー結果はフロントエンドの `splitReviewState.groupReviews` に保持済み、ZIP生成もJSZipでフロントエンド処理）

---

## 修正対象ファイル

| ファイル | 修正内容 |
|---------|---------|
| `versions/v0.9.1/spec.md` | ZIP同梱ファイル仕様、README.mdテンプレート、画面イメージ、E2Eテストケースの更新 |
| `frontend/src/features/reviewer/hooks/useZipExport.ts` | `SplitExportData` 型にグループレビュー結果を追加、ZIPへの書き込み処理を追加 |
| `frontend/src/features/reviewer/index.tsx` | `downloadZip` ラッパーでグループレビュー結果を `splitData` に渡す |
| `frontend/src/features/reviewer/services/markdown.ts` | `generateReadmeMarkdown` にグループレビューファイルの同梱ファイル行を動的追加 |
| `frontend/src/features/reviewer/components/ReviewResult.tsx` | ダウンロード内容テーブルにグループレビュー個別結果ファイル行を表示 |
| `frontend/src/__tests__/features/reviewer/hooks/useZipExport.test.ts` | グループレビュー結果がZIPに含まれることを検証するテストケースを追加 |
| `frontend/src/__tests__/features/reviewer/services/markdown.test.ts` | READMEにグループレビューファイルが同梱ファイル一覧に出力されることを検証 |
| `CHANGELOG.md` | v0.9.1の追加項目にグループレビュー個別結果ZIP同梱を追記、リリース日を2026-03-13に修正 |
| `versions/README.md` | v0.9.1の更新履歴にグループレビュー個別結果ZIP同梱を追記、リリース日を2026-03-13に修正 |

---

## 修正詳細

### 1. `spec.md` — ZIP同梱ファイル仕様の更新

#### 1-1. ZIP内の同梱ファイルテーブル（L601-609）に追記

分割レビュー時の条件付きファイルとして、グループレビュー個別結果を追記する:

```markdown
**ZIP内の同梱ファイル:**

| ファイル名 | 説明 |
|-----------|------|
| README.md | レビュー情報と同梱ファイルの説明 |
| system-prompt.md | システムプロンプト（役割・目的・出力形式・注意事項） |
| spec-markdown.md | 変換後の設計書（マークダウン形式） |
| code-numbered.txt | 行番号付きプログラム |
| review-result.md | AIレビュー結果 |

**分割レビュー時の追加ファイル:**

| ファイル名 | 説明 |
|-----------|------|
| split/spec-INDEX.md | 設計書の構造情報（md2map生成） |
| split/spec-MAP.json | 設計書のセクションマップ（md2map生成） |
| split/code-INDEX.md | プログラムの構造情報（code2map生成） |
| split/code-MAP.json | プログラムのシンボルマップ（code2map生成） |
| split/review-result-{groupId}.md | グループレビュー個別結果（グループごとに1ファイル） |
```

#### 1-2. README.mdテンプレート（L639-648）に追記

同梱ファイルテーブルにグループレビュー個別結果ファイルの行を追加する。グループ数に応じて動的に行が増えるため、テンプレートにはコメントで説明を記載:

```markdown
| split/review-result-group1.md | グループレビュー個別結果（ユーザー管理） |
| split/review-result-group2.md | グループレビュー個別結果（注文処理） |
```

#### 1-3. 結果画面のダウンロード内容テーブル（L1383-1392）を更新

分割レビュー時のダウンロード内容テーブルに、グループレビュー個別結果ファイルが含まれることを画面イメージに反映する。

#### 1-4. E2Eテストケース（L3425）を更新

`E2E-RV-009` の期待結果に、分割レビュー時は `split/review-result-{groupId}.md` が含まれることを追加する。

---

### 2. `hooks/useZipExport.ts` — `SplitExportData` 型とZIP生成の拡張

#### 2-1. `SplitExportData` にグループレビュー結果フィールドを追加

```ts
export interface SplitExportData {
  documentIndex?: string
  documentMapJson?: Record<string, unknown>[]
  codeIndex?: string
  codeMapJson?: Record<string, unknown>[]
  groupReviews?: { groupId: string; groupName: string; report: string }[]  // 追加
}
```

#### 2-2. `downloadZip` 関数内でグループレビュー結果をZIPに追加

既存の `if (splitData)` ブロック内（L50-63）に以下を追加:

```ts
// グループレビュー個別結果
if (splitData.groupReviews) {
  for (const gr of splitData.groupReviews) {
    zip.file(`split/review-result-${gr.groupId}.md`, gr.report)
  }
}
```

---

### 3. `index.tsx` — ダウンロードデータ構築の拡張

`downloadZip` ラッパー（L131-144）で `splitData` を構築する際、`splitReviewState.groupReviews` から completed のグループレビュー結果を渡す:

```ts
const downloadZip = useCallback(
  async (data: ReviewExecutionData, executionNumber: number) => {
    let splitData: SplitExportData | undefined
    if (splitPreviewResult) {
      splitData = {
        documentIndex: splitPreviewResult.documentIndex || undefined,
        documentMapJson: splitPreviewResult.documentMapJson || undefined,
        codeIndex: splitPreviewResult.codeIndex || undefined,
        codeMapJson: splitPreviewResult.codeMapJson || undefined,
        // グループレビュー個別結果を追加
        groupReviews: splitReviewState.groupReviews
          .filter((g) => g.status === 'completed' && g.result?.report)
          .map((g) => ({
            groupId: g.groupId,
            groupName: g.groupName,
            report: g.result!.report,
          })),
      }
    }
    await rawDownloadZip(data, executionNumber, splitData)
  },
  [rawDownloadZip, splitPreviewResult, splitReviewState.groupReviews]
)
```

注意: 依存配列に `splitReviewState.groupReviews` を追加する。

---

### 4. `services/markdown.ts` — README生成の拡張

#### 4-1. `generateReadmeMarkdown` の引数を拡張

`hasSplitData` に加えて、グループレビュー情報を受け取れるようにする:

```ts
export function generateReadmeMarkdown(
  reviewMeta: { /* 既存 */ },
  executionNumber: number,
  hasSplitData: boolean = false,
  groupReviews?: { groupId: string; groupName: string }[],  // 追加
): string {
```

#### 4-2. 同梱ファイルテーブルにグループレビュー行を動的追加

```ts
const groupReviewFiles = groupReviews && groupReviews.length > 0
  ? groupReviews.map(
      (gr) => `| split/review-result-${gr.groupId}.md | グループレビュー個別結果（${gr.groupName}） |`
    ).join('\n') + '\n'
  : ''
```

テンプレート内の同梱ファイルテーブル（L96-108）に挿入:

```ts
${hasSplitData ? `| split/spec-INDEX.md | 設計書の構造情報（md2map生成） |
| split/spec-MAP.json | 設計書のセクションマップ（md2map生成） |
| split/code-INDEX.md | プログラムの構造情報（code2map生成） |
| split/code-MAP.json | プログラムのシンボルマップ（code2map生成） |
${groupReviewFiles}` : ''}
```

#### 4-3. 呼び出し元の更新

`useZipExport.ts` L46 の `generateReadmeMarkdown` 呼び出しに `groupReviews` を渡す:

```ts
const readme = generateReadmeMarkdown(
  data.reviewMeta,
  executionNumber,
  !!splitData,
  splitData?.groupReviews?.map((gr) => ({ groupId: gr.groupId, groupName: gr.groupName })),
)
```

---

### 5. `components/ReviewResult.tsx` — ダウンロード内容テーブルの更新

分割レビュー時のダウンロード内容テーブル（L228-244付近、L354付近）に、グループレビュー個別結果ファイルの行を動的に追加する。

分割レビュー結果画面（`isSplitMode` が `true` の場合）のテーブルに以下を追加:

```tsx
{/* グループレビュー個別結果（分割レビュー時のみ） */}
{splitReviewState?.groupReviews
  ?.filter((g) => g.status === 'completed' && g.result?.report)
  .map((g) => (
    <tr key={g.groupId}>
      <td className="...">split/review-result-{g.groupId}.md</td>
      <td className="...">グループレビュー個別結果（{g.groupName}）</td>
    </tr>
  ))
}
```

---

### 6. テストの追加

#### 6-1. `useZipExport.test.ts`

```ts
it('分割レビュー時にグループレビュー個別結果がZIPに含まれる', async () => {
  const { result } = renderHook(() => useZipExport())
  const splitData: SplitExportData = {
    groupReviews: [
      { groupId: 'group1', groupName: 'ユーザー管理', report: '## サマリー\n\n...' },
      { groupId: 'group2', groupName: '注文処理', report: '## サマリー\n\n...' },
    ],
  }
  await act(async () => {
    await result.current.downloadZip(mockData, 1, splitData)
  })
  // JSZip.file が 'split/review-result-group1.md' と 'split/review-result-group2.md' で呼ばれたことを検証
})
```

#### 6-2. `markdown.test.ts`

```ts
it('groupReviewsがあるときグループレビュー個別結果ファイルが同梱ファイル一覧に含まれる', () => {
  const result = generateReadmeMarkdown(
    mockMeta,
    1,
    true,
    [
      { groupId: 'group1', groupName: 'ユーザー管理' },
      { groupId: 'group2', groupName: '注文処理' },
    ],
  )
  expect(result).toContain('split/review-result-group1.md')
  expect(result).toContain('split/review-result-group2.md')
  expect(result).toContain('ユーザー管理')
})

it('groupReviewsが空のときグループレビューファイル行が含まれない', () => {
  const result = generateReadmeMarkdown(mockMeta, 1, true, [])
  expect(result).not.toContain('review-result-')
})
```

---

### 7. `CHANGELOG.md` / `versions/README.md` — 変更履歴の更新

#### 7-1. `CHANGELOG.md`

v0.9.1セクションのリリース日を `2026-03-13` に修正し、「追加」セクションに以下を追記:

```markdown
## [0.9.1] - 2026-03-13

### 追加
- **グループレビュー個別結果のZIP同梱**（#60）: 分割レビュー時のZIPダウンロードに、各グループのレビュー結果を `split/review-result-{groupId}.md` として含めるよう追加。結果画面のダウンロード内容テーブルにもファイル一覧を表示
```

#### 7-2. `versions/README.md`

v0.9.1のリリース日を `2026-03-13` に修正し、更新履歴セクションに以下を追記:

```markdown
### v0.9.1 (2026-03-13)
- **グループレビュー個別結果のZIP同梱**: 分割レビュー時のZIPダウンロードに各グループのレビュー結果（`split/review-result-{groupId}.md`）を含める（#60）
```

---

## 実装順序

1. `spec.md` — 仕様書の更新
2. `hooks/useZipExport.ts` — `SplitExportData` 型拡張とZIP生成ロジック追加
3. `services/markdown.ts` — README生成の拡張
4. `index.tsx` — ダウンロードデータ構築の拡張
5. `components/ReviewResult.tsx` — ダウンロード内容テーブルの更新
6. テストの追加・更新
7. `CHANGELOG.md` / `versions/README.md` — 変更履歴の更新

---

## 検証方針

- 分割レビュー完了後のZIPダウンロードに `split/review-result-{groupId}.md` ファイルが含まれること
- 各グループレビューファイルの内容が、グループレビューフェーズで取得したレポートと一致すること
- README.mdの同梱ファイルテーブルにグループレビュー個別結果ファイルが列挙されること
- スキップされたグループ（`status !== 'completed'`）のレビュー結果はZIPに含まれないこと
- 一括レビュー時（分割レビューでない場合）は従来通り5ファイルのみでグループレビューファイルが含まれないこと
- 結果画面のダウンロード内容テーブルにグループレビューファイルが表示されること

---

## 完了チェックリスト

### 仕様書

- [x] `spec.md` L601-609: ZIP同梱ファイルテーブルにグループレビュー個別結果ファイルを追記
- [x] `spec.md` L639-648: README.mdテンプレートの同梱ファイル一覧に追記
- [x] `spec.md` L1383-1392: 結果画面のダウンロード内容テーブル画面イメージを更新
- [x] `spec.md` L3425: E2Eテストケース `E2E-RV-009` にグループレビュー個別結果の確認を追加

### 実装

- [x] `hooks/useZipExport.ts`: `SplitExportData` に `groupReviews` フィールドを追加
- [x] `hooks/useZipExport.ts`: `downloadZip` 内でグループレビュー結果を `split/review-result-{groupId}.md` としてZIPに追加
- [x] `services/markdown.ts`: `generateReadmeMarkdown` に `groupReviews` 引数を追加
- [x] `services/markdown.ts`: 同梱ファイルテーブルにグループレビューファイル行を動的追加
- [x] `hooks/useZipExport.ts`: `generateReadmeMarkdown` 呼び出しに `groupReviews` を渡す
- [x] `index.tsx`: `downloadZip` ラッパーで `splitReviewState.groupReviews` からデータを構築して渡す
- [x] `components/ReviewResult.tsx`: ダウンロード内容テーブルにグループレビュー個別結果ファイル行を動的表示

### テスト

- [x] `useZipExport.test.ts`: グループレビュー結果がZIPに含まれることを検証
- [x] `markdown.test.ts`: READMEにグループレビューファイルが同梱ファイル一覧に出力されることを検証
- [x] `markdown.test.ts`: groupReviewsが空のときグループレビューファイル行が含まれないことを検証

### 変更履歴

- [x] `CHANGELOG.md`: v0.9.1のリリース日を `2026-03-13` に修正、「追加」にグループレビュー個別結果ZIP同梱を追記
- [x] `versions/README.md`: v0.9.1のリリース日を `2026-03-13` に修正、更新履歴にグループレビュー個別結果ZIP同梱を追記

### 検証

- [x] 分割レビュー完了後のZIPに `split/review-result-{groupId}.md` が含まれる
- [x] 各ファイルの内容がグループレビュー結果と一致する
- [x] スキップされたグループはZIPに含まれない
- [x] 一括レビュー時は従来通りの5ファイルのみ
- [x] 結果画面のダウンロード内容テーブルにグループレビューファイルが表示される
