# fetchHeadings エラーハンドリング修正計画書

## 概要

「分割」モード選択時に `POST /api/split/headings` が HTTP エラー（405 等）を返した場合、フロントエンドがエラーを検知できず、事前重要指定・事前除外指定パネルが正しく表示されない不具合を修正する。

対応 Issue: [#79](https://github.com/elvezjp/spec-code-ai-reviewer/issues/79)

## 背景

ユーザーから「分割モードを選択しても事前指定パネルが表示されない」という報告があった。

調査の結果、バックエンドが v0.9.1（`POST /api/split/headings` 未実装）で起動している場合、以下の挙動になることが判明した:

| ケース | 挙動 |
|---|---|
| バックエンド停止時 | `fetch` 自体が例外 → `catch` ブロックでエラーメッセージ表示 |
| v0.9.1 バックエンド時 | 405 レスポンスを受信 → `response.json()` がパース試行 → `result.success === false` に該当せず → `setHeadings(result.headings \|\| [])` で空配列セット → **エラーなし・見出し0件の状態** |

### 根本原因

`fetchHeadings()` 関数で `response.ok` のチェックを行っていないため、HTTP エラーレスポンス（405, 500 等）でもそのまま `response.json()` を実行してしまう。

```typescript
// 現在のコード（問題あり）
export async function fetchHeadings(content: string): Promise<...> {
  const response = await fetch(`${getBackendUrl()}/api/split/headings`, { ... })
  return await response.json()  // ← response.ok のチェックがない
}
```

## 修正方針

`fetchHeadings()` で `response.ok` をチェックし、非 2xx レスポンスの場合はエラーを返す。

同様の問題がある他の API 関数についても、影響範囲を確認し、必要に応じて修正する。

---

## 前提

- 現在の実装: `versions/v0.9.4`
- `versions/v0.9.4` を丸ごとコピーして `versions/v0.9.5` を作成し、v0.9.5 上で修正を行う

---

## Step 0: v0.9.5 ディレクトリの作成

- `versions/v0.9.4` を `versions/v0.9.5` にコピー
- v0.9.5 の spec.md にバージョン番号を反映

---

## Step 1: fetchHeadings の response.ok チェック追加

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.5/frontend/src/features/reviewer/services/api.ts` | `fetchHeadings()` に `response.ok` チェックを追加 |

### 修正内容

```typescript
export async function fetchHeadings(
  content: string
): Promise<{ success?: boolean; headings: HeadingInfo[]; error?: string }> {
  const response = await fetch(`${getBackendUrl()}/api/split/headings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  })

  if (!response.ok) {
    return { headings: [], error: `見出し一覧の取得に失敗しました (HTTP ${response.status})` }
  }

  return await response.json()
}
```

---

## Step 2: 他の API 関数の影響調査と修正

### 調査対象

`api.ts` 内の全 API 関数について、`response.ok` チェックの有無を確認する。

| 関数 | 現状 | 影響度 | 対応 |
|---|---|---|---|
| `fetchAvailableTools()` | `try-catch` で例外時はフォールバック | 低（フォールバックあり） | 対応不要 |
| `convertExcelToMarkdown()` | チェックなし | 中 | 要修正 |
| `addLineNumbers()` | チェックなし | 中 | 要修正 |
| `executeReview()` | チェックなし | 中 | 要修正 |
| `testLlmConnection()` | チェックなし | 中 | 要修正 |
| `organizeMarkdown()` | チェックなし | 中 | 要修正 |
| `fetchHeadings()` | チェックなし | 高（本Issue） | **Step 1 で修正** |
| `splitMarkdown()` | チェックなし | 中 | 要修正 |
| `splitCode()` | チェックなし | 中 | 要修正 |
| `executeStructureMatching()` | チェックなし | 中 | 要修正 |
| `executeGroupReview()` | チェックなし | 中 | 要修正 |
| `executeIntegrate()` | チェックなし | 中 | 要修正 |
| `executeSummarize()` | チェックなし | 中 | 要修正 |

### 修正方針

共通のレスポンスチェックヘルパーを導入し、全 API 関数に適用する。

```typescript
/**
 * レスポンスのステータスコードをチェックし、非 2xx の場合はエラーをスローする
 */
async function assertResponseOk(response: Response, context: string): Promise<void> {
  if (!response.ok) {
    let detail = ''
    try {
      const body = await response.text()
      if (body) detail = `: ${body}`
    } catch {
      // ボディ読み取り失敗は無視
    }
    throw new Error(`${context} (HTTP ${response.status}${detail})`)
  }
}
```

各 API 関数での適用例:

```typescript
export async function splitMarkdown(request: SplitMarkdownRequest): Promise<SplitMarkdownResponse> {
  const response = await fetch(`${getBackendUrl()}/api/split/markdown`, { ... })
  await assertResponseOk(response, '分割処理に失敗しました')
  return await response.json()
}
```

`fetchHeadings` はエラーをオブジェクトとして返す必要があるため、ヘルパーを使わず個別にハンドリングする（Step 1 の実装を維持）。

---

## Step 3: テストの追加

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.5/frontend/src/__tests__/features/reviewer/services/api.test.ts` | `fetchHeadings` の HTTP エラーレスポンス時のテスト、`assertResponseOk` のテスト、各 API 関数の非 2xx レスポンス時のテスト |

### テストケース

| ケース | 内容 |
|---|---|
| fetchHeadings: 405 レスポンス | エラーオブジェクトが返り、headings が空配列であること |
| fetchHeadings: 500 レスポンス | エラーオブジェクトが返り、headings が空配列であること |
| fetchHeadings: 200 正常レスポンス | headings が正常に返ること（既存動作の回帰テスト） |
| assertResponseOk: 非 2xx レスポンス | エラーがスローされること |
| 各 API 関数: 非 2xx レスポンス | エラーがスローされること |

---

## Step 4: ドキュメント更新

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.5/spec.md` | バージョン番号を v0.9.5 に更新 |

---

## 修正順序と依存関係

```
Step 0: v0.9.5 作成
  ↓
Step 1: fetchHeadings の response.ok チェック追加（本 Issue の直接修正）
  ↓
Step 2: 他の API 関数の response.ok チェック追加（波及修正）
  ↓
Step 3: テスト追加
  ↓
Step 4: ドキュメント更新
```

---

## 影響範囲

| 対象 | 影響 |
|---|---|
| バックエンド | 変更なし |
| フロントエンド（api.ts） | 全 API 関数に `response.ok` チェックを追加 |
| フロントエンド（その他） | 変更なし（既存の `catch` ブロックでスローされたエラーを処理） |
| md2map / code2map | 変更なし |
| ドキュメント | `spec.md` のバージョン番号更新 |

---

## 関連

- Issue: [#79 「分割」モード選択時に事前重要指定パネルが表示されない](https://github.com/elvezjp/spec-code-ai-reviewer/issues/79)
- 事前重要指定の計画書: [20260318-pre-split-importance-plan.md](20260318-pre-split-importance-plan.md)
- 事前除外の計画書: [20260324-pre-split-exclusion-plan.md](20260324-pre-split-exclusion-plan.md)

---

## 完了チェックリスト

### Step 0: v0.9.5 作成

- [ ] `versions/v0.9.4` を `versions/v0.9.5` にコピー
- [ ] v0.9.5 の全バージョン番号を更新
- [ ] インフラ設定（Docker/Nginx/PM2）に v0.9.5 を追加
- [ ] `latest` シンボリックリンクを v0.9.5 に更新
- [ ] 全バージョンの `useVersions.ts` に v0.9.5 を追加

### Step 1: fetchHeadings の response.ok チェック追加

- [ ] `fetchHeadings()` に `response.ok` チェックを追加
- [ ] 405 レスポンス時にエラーメッセージが表示されることを確認

### Step 2: 他の API 関数の response.ok チェック追加

- [ ] `assertResponseOk()` ヘルパー関数の追加
- [ ] 全 API 関数に `response.ok` チェックを適用

### Step 3: テスト追加

- [ ] `fetchHeadings` の HTTP エラーレスポンス時のテスト追加
- [ ] `assertResponseOk` のテスト追加
- [ ] 全フロントエンドテスト通過

### Step 4: ドキュメント更新

- [ ] `versions/v0.9.5/spec.md` のバージョン番号更新

### 最終確認

- [ ] 全バックエンドテスト通過
- [ ] 全フロントエンドテスト通過
- [ ] 手動動作確認（v0.9.1 バックエンドで分割モード選択時にエラーメッセージが表示されること）
