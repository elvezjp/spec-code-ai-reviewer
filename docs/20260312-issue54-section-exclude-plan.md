# 計画書: 分割プレビュー セクション除外機能 (issue#54)

## 概要

分割プレビューの設計書パーツ一覧に「除外」チェックボックスを追加し、除外されたセクションを構造マッチング・グループレビューの対象から外せるようにする。

対象バージョン: `versions/v0.9.1`

---

## 修正対象ファイル

| ファイル | 修正内容 |
|---|---|
| `frontend/src/features/reviewer/types/index.ts` | `DocumentPart` に `excluded` フィールドを追加 |
| `frontend/src/features/reviewer/hooks/useSplitSettings.ts` | 除外トグル関数・state を追加 |
| `frontend/src/features/reviewer/components/SplitSettingsSection.tsx` | 「除外」列を `DocumentPartsTable` に追加、`PartContentPreview` コンポーネントを追加 |
| `frontend/src/features/reviewer/index.tsx` | 除外パーツをレビュー対象から除外するフィルタリングを追加 |
| `docs/split-review.md` | セクション除外機能の説明を追加 |
| `versions/v0.9.1/spec.md` | 2.7.5 分割プレビューの表と 2.7.x セクション除外機能の仕様を追加 |

---

## 修正詳細

### 1. `types/index.ts` — `DocumentPart` に `excluded` フィールド追加

```ts
export interface DocumentPart {
  // ... 既存フィールド
  excluded: boolean  // 追加: trueのとき構造マッチング・グループレビューの対象外
}
```

### 2. `hooks/useSplitSettings.ts` — 除外トグル関数の追加

**追加する内容:**

- `UseSplitSettingsReturn` インターフェースに `toggleExcludedDocPart: (partId: string) => void` を追加
- `toggleExcludedDocPart` を `useCallback` で実装する。`excluded` を `true` にする際は、「重要」（`pinnedDocPartIds`）と「要約」（`summarizeMode`）も同時に解除する

```ts
const toggleExcludedDocPart = useCallback((partId: string) => {
  setPreviewResult((prev) => {
    if (!prev || !prev.documentParts) return prev
    const target = prev.documentParts.find((p) => p.id === partId)
    if (!target) return prev
    const newExcluded = !target.excluded
    return {
      ...prev,
      documentParts: prev.documentParts.map((p) =>
        p.id === partId
          ? {
              ...p,
              excluded: newExcluded,
              // 除外ON時は「要約」を解除
              ...(newExcluded ? { summarizeMode: 'original' as const } : {}),
            }
          : p
      ),
    }
  })
  // 除外ON時は「重要」も解除
  setPinnedDocPartIds((prev) => {
    const target = prev.includes(partId)
    if (!target) return prev
    // toggleExcluded は除外ON/OFFを切り替えるが、除外OFFのときは重要を復元しない
    // setPreviewResult と同期が取れないため、除外方向のみ解除する
    return prev.filter((id) => id !== partId)
  })
}, [])
```

ただし `toggleExcludedDocPart` は `previewResult` を参照しないため、除外ON/OFFの判定を呼び出し元（`SplitSettingsSection`）から受け取る方式に変更する。シグネチャを以下に変更する:

```ts
toggleExcludedDocPart: (partId: string) => void
// 内部では part.excluded の現在値を見て反転させるため、シグネチャ変更は不要
// ただし setPinnedDocPartIds の呼び出しは、excluded が true になる場合のみ行う
```

実装のポイント:
- `setPreviewResult` のコールバック内で `target.excluded` の現在値を確認し、`newExcluded = !target.excluded` を算出する
- `newExcluded === true` のときのみ `summarizeMode: 'original'` に戻す
- `newExcluded === true` のときのみ `setPinnedDocPartIds` から `partId` を除去する

- `executePreview` 内の `setPreviewResult` で、`documentParts` の各パーツに `excluded: false` の初期値を付与する（既存コードの `summarizeMode: 'original'` と同様）

```ts
documentParts: response.parts.map((p) => ({
  ...p,
  summarizeMode: 'original' as const,
  excluded: false,  // 追加
}))
```

- `return` の戻り値に `toggleExcludedDocPart` を追加する

### 3. `components/SplitSettingsSection.tsx` — 「除外」列を追加

**`SplitSettingsSectionProps` インターフェースへの追加:**

```ts
onToggleExcludedDocPart: (partId: string) => void
```

**`DocumentPartsTable` コンポーネントの変更:**

- props に `onToggleExcludedDocPart` を追加
- `TableHead` に「除外」列ヘッダーを追加（「重要」「要約」の後ろに配置）
- 各行に「除外」チェックボックスを追加

```tsx
{/* 除外チェックボックス */}
<TableCell className="text-center">
  <input
    type="checkbox"
    checked={part.excluded}
    onChange={() => onToggleExcludedDocPart(part.id)}
    className="w-4 h-4 text-red-500 rounded"
  />
</TableCell>
```

- 除外されたパーツの行を視覚的にグレーアウト表示する（`opacity-40` など）
- セクション名セルの下に「▶ 内容を表示」ボタンを追加し、クリックで内容をアコーディオン展開する。既存の `SummarizedTextPreview` と同じ構造で実装する

```tsx
{/* セクション内容プレビュー（アコーディオン） */}
<PartContentPreview content={part.content} />
```

`PartContentPreview` は `SummarizedTextPreview` と同様のコンポーネントとして実装する:

```tsx
function PartContentPreview({ content }: { content: string }) {
  const [isExpanded, setIsExpanded] = useState(false)
  return (
    <div className="mt-1">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600"
      >
        {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        内容を表示
      </button>
      {isExpanded && (
        <div className="mt-1 p-2 bg-gray-50 border border-gray-200 rounded text-xs text-gray-700 whitespace-pre-wrap max-h-40 overflow-y-auto">
          {content}
        </div>
      )}
    </div>
  )
}
```

**凡例の更新:**

既存の `<ul>` に以下を追加する:

```tsx
<li><strong>除外</strong>: 構造マッチング・グループレビューの対象から外します。表紙・変更履歴など不要なセクションを除外してください。</li>
```

**`SplitSettingsSection` の `props` から `DocumentPartsTable` への受け渡しを追加:**

```tsx
<DocumentPartsTable
  parts={previewResult.documentParts}
  pinnedDocPartIds={pinnedDocPartIds}
  onTogglePinnedDocPart={onTogglePinnedDocPart}
  onToggleSummarizeMode={onToggleSummarizeMode}
  summarizingPartIds={summarizingPartIds}
  onToggleExcludedDocPart={onToggleExcludedDocPart}  // 追加
/>
```

### 4. `index.tsx` — 除外パーツのフィルタリング

**`useSplitSettings` からの `toggleExcludedDocPart` の取り出し:**

```ts
const {
  // ... 既存
  toggleExcludedDocPart,
} = useSplitSettings()
```

**構造マッチング用 `documentMapJson` の構築時にフィルタリング:**

`index.tsx` の `sections: splitPreviewResult.documentParts?.map(...)` の部分（L314付近）で、除外パーツを除外する:

```ts
sections: splitPreviewResult.documentParts
  ?.filter((p) => !p.excluded)  // 追加
  .map((p) => ({
    id: p.id,
    title: p.section,
    ...
  })) || [],
```

同様に `splitPreviewResult.documentMapJson` を使う場合も、`documentParts` で除外IDを特定してフィルタリングする:

```ts
const excludedDocPartIds = new Set(
  splitPreviewResult.documentParts?.filter(p => p.excluded).map(p => p.id) || []
)
const documentMapJson = splitPreviewResult.documentMapJson
  ? {
      sections: splitPreviewResult.documentMapJson.filter(
        (s) => !excludedDocPartIds.has(s.id as string)
      )
    }
  : {
      sections: splitPreviewResult.documentParts
        ?.filter((p) => !p.excluded)
        .map((p) => ({ ... })) || [],
    }
```

**グループ復元処理での安全フィルタリング:**

`index.tsx` のグループ復元処理（L368付近）で、除外パーツが `docSections` に含まれている場合は除外する。

MAP.jsonフィルタリングにより通常は除外IDがAIに渡らないが、万一AIが除外IDを返した場合の保険として追加する。なお、現状の実装では存在しないIDは空セクションとして残るだけだが、**除外パーツのIDはdocumentPartsに残っている**（`excluded: true`なだけ）ため、findで見つかり内容がレビューに混入してしまう。このフィルタがそれを防ぐ:

```ts
for (const group of groups) {
  group.docSections = group.docSections
    .filter((ds) => !excludedDocPartIds.has(ds.id))  // 追加: 除外パーツを安全フィルタ
    .map((ds) => { ... })
  // ...
}
```

**重要パーツ注入時のフィルタリング:**

`pinnedDocPartIds` を全グループに注入する際（L384付近）、除外パーツは注入しない:

```ts
const pinnedDocSections = pinnedDocPartIds
  .filter(id => !excludedDocPartIds.has(id))  // 追加
  .map(id => { ... })
```

**`SplitSettingsSection` への prop 追加:**

```tsx
<SplitSettingsSection
  // ... 既存
  onToggleExcludedDocPart={toggleExcludedDocPart}  // 追加
/>
```

---

### 5. `docs/split-review.md` — セクション除外機能の説明を追加

**セクション 3（分割設定）に `3.4 セクション除外` を追加:**

```markdown
### 3.4 セクション除外

分割された設計書セクションのうち、レビュー不要なセクションを除外できます。

- 一覧テーブルの「除外」チェックボックスをチェックすると、そのセクションが構造マッチング・グループレビューの対象から外れる
- 除外チェックON時は「重要」「要約」のチェックが自動的に解除される
- 除外は MAP.json からの除去として実装されており、INDEX.md はオリジナルが維持される
- ダウンロード zip に含まれる INDEX.md / MAP.json はオリジナル（除外前）のものが使用される
- プレビューを再実行すると除外状態はリセットされる
```

**セクション 8（エンドツーエンドの流れ）の `[分割設定]` 行に除外を追記:**

```markdown
[分割設定] 重要パートの選択、セクション除外の設定、事前要約の実行（任意）
```

---

### 6. `versions/v0.9.1/spec.md` — 分割プレビューの仕様を更新

**2.7.5 分割プレビューの設計書パーツ表に「除外」行を追加:**

```markdown
| 除外 | チェックボックス。チェックしたセクションは構造マッチング・グループレビューの対象から外れる |
```

表の位置は「要約」行の後ろ（「セクション名」行の前）に挿入する。

**新セクション 2.7.x（2.7.6 の前）としてセクション除外機能の仕様を追加:**

既存の 2.7.6 以降の番号を繰り下げる（2.7.6 → 2.7.7、2.7.7 → 2.7.8）。

```markdown
#### 2.7.6 セクション除外機能

分割プレビューで設計書パートをレビュー対象から除外する機能。

**目的:**
- Excel変換時に生成される表紙・変更履歴など、レビューに不要なセクションを除外する
- 不要セクションが構造マッチングに含まれるとグループ化精度が低下する可能性があるため、事前に除外することで精度を改善する

**除外フロー:**
1. 分割プレビューの設計書パーツテーブルで、各パートの「内容を表示」で内容を確認する
2. 不要なパートの「除外」チェックボックスをチェックする
3. 除外チェックON時は「重要」「要約」のチェックが自動的に解除される
4. レビューを実行すると、除外パートは構造マッチング（フェーズ1）の MAP.json から除かれる

**除外の動作:**
- 除外されたパートは構造マッチング（フェーズ1）の MAP.json から取り除かれ、LLM によるグループ割り当ての対象にならない
- 除外されたパートはグループレビュー（フェーズ2）の設計書コンテンツにも含まれない
- 実行結果画面のグループ一覧にも除外パートは表示されない
- ダウンロード zip に含まれる INDEX.md / MAP.json はオリジナル（除外前）のものが使用される
- プレビューを再実行すると除外状態はリセットされる
```

---

## 動作イメージ

- プレビュー実行後、設計書パーツ一覧に「重要」「要約」「除外」の3列が表示される
- 「除外」にチェックを入れると、該当行がグレーアウトされる
- 「除外」にチェックを入れると、同じ行の「重要」「要約」のチェックが自動的に外れる
- 除外パーツは構造マッチング（フェーズ1）の MAP.json から除かれ、LLM によるグループ割り当ての対象にならない
- 除外パーツはグループレビュー（フェーズ2）の設計書コンテンツにも含まれない
- 「重要」と「除外」を同時にチェックしても、「除外」が優先される（注入処理でフィルタリング済み）
- プレビューを再実行すると除外状態はリセットされる（既存の設定変更時クリア仕様と同様）

---

## 考慮事項

- **自動除外候補の提示** (issue#54 対応案4) は今回のスコープ外とする。まず手動除外を実装し、フィードバックを得てから検討する
- `excluded` フィールドは `DocumentPart` 型に追加するが、APIレスポンスには存在しない。フロントエンド側の `executePreview` 内で初期化する
- 除外されたパーツをプレビュー件数のカウント（「N パート」表示）に含めるかどうかは、全件を表示したままチェック状態で管理する方式とする（件数表示の変更は不要）

---

## 完了チェックリスト

### types/index.ts
- [ ] `DocumentPart` に `excluded: boolean` フィールドを追加

### hooks/useSplitSettings.ts
- [ ] `UseSplitSettingsReturn` に `toggleExcludedDocPart` を追加
- [ ] `toggleExcludedDocPart` を `useCallback` で実装（除外ON時に `summarizeMode` を `'original'` に戻す）
- [ ] `toggleExcludedDocPart` 内で除外ON時に `setPinnedDocPartIds` から該当IDを除去
- [ ] `executePreview` の `setPreviewResult` で各パーツに `excluded: false` を初期化
- [ ] `return` の戻り値に `toggleExcludedDocPart` を追加

### components/SplitSettingsSection.tsx
- [ ] `SplitSettingsSectionProps` に `onToggleExcludedDocPart` を追加
- [ ] `DocumentPartsTable` の props に `onToggleExcludedDocPart` を追加
- [ ] テーブルヘッダーに「除外」列を追加（「要約」の後）
- [ ] 各行に「除外」チェックボックスを追加
- [ ] 除外行のグレーアウト表示を追加（`opacity-40` など）
- [ ] `PartContentPreview` コンポーネントを追加
- [ ] セクション名セルに `<PartContentPreview>` を追加
- [ ] 凡例の `<ul>` に「除外」の説明を追加
- [ ] `<DocumentPartsTable>` への `onToggleExcludedDocPart` の受け渡しを追加
- [ ] `<SplitSettingsSection>` への `onToggleExcludedDocPart` prop の追加

### index.tsx
- [ ] `useSplitSettings` から `toggleExcludedDocPart` を取り出す
- [ ] `excludedDocPartIds` セットの構築を追加
- [ ] `documentMapJson` 構築時に除外IDをフィルタリング
- [ ] グループ復元処理（L368付近）で除外IDを安全フィルタリング
- [ ] 重要パーツ注入処理（L384付近）で除外IDをフィルタリング
- [ ] `<SplitSettingsSection>` に `onToggleExcludedDocPart` prop を追加

### docs/split-review.md
- [ ] セクション 3 に `3.4 セクション除外` を追加
- [ ] セクション 8 のエンドツーエンドの流れ `[分割設定]` 行に除外を追記

### versions/v0.9.1/spec.md
- [ ] 2.7.5 設計書パーツ表に「除外」行を追加
- [ ] `2.7.6 セクション除外機能` セクションを新規追加
- [ ] 既存の 2.7.6 以降の番号を繰り下げ（2.7.6 → 2.7.7、2.7.7 → 2.7.8）
