# 事前除外機能 修正計画書

## 概要

分割前にセクションを「除外」として指定する「事前除外」機能を追加する。
不要なセクション（変更履歴、目次など）を分割処理の対象から完全に除外し、処理時間の短縮とトークン節約を実現する。

対応 Issue: [#68](https://github.com/elvezjp/spec-code-ai-reviewer/issues/68)

## 背景

[PR #65](https://github.com/elvezjp/spec-code-ai-reviewer/pull/65) で追加した「事前重要指定」機能では、分割前に H2 見出し単位でセクションを「重要」として指定できる。
これに加えて、分割前にセクションを「除外」としても指定したいという要望を受けた。

現状のフロー:
1. 事前重要指定: H2 見出し一覧から重要セクションにチェック
2. 分割プレビュー実行
3. 分割結果一覧で重要・要約・除外を手動設定

不要なセクションが事前にわかっている場合、分割プレビューの前に除外指定できれば:
- 分割処理の対象から外すことで **処理時間を短縮**
- AI/NLP サブスプリットの対象外になることで **LLM 問い合わせ回数を削減**
- 不要コンテンツを処理しないことで **トークンを節約**

## UX フロー

### 現状のフロー（v0.9.2）

```
設計書アップロード → Markdown変換
→ 「分割」選択時にセクション一覧を取得・表示 → 「事前重要指定」セクションを選択
→ 「事前重要指定」「通常」の分割モード選択 → 分割プレビュー実行
→ 一覧から重要・除外・要約を手動チェック → レビュー開始
```

### 改善後のフロー（v0.9.3）

```
設計書アップロード → Markdown変換
→ 「分割」選択時にセクション一覧を取得・表示
→ 「事前重要指定」「事前除外」セクションを選択
→ 「事前重要指定」「通常」の分割モード選択 → 分割プレビュー実行
→ 一覧から重要・除外・要約を手動チェック → レビュー開始
```

### 変更後の画面イメージ

#### 画面①: 事前重要指定 / 事前除外（パネル変更）

事前重要指定パネルに「事前除外」チェックボックス列を追加する。

- 事前重要と事前除外は排他制御（同一セクションに両方チェック不可）
- 事前重要をONにすると事前除外は自動OFF（逆も同様）

```
┌─────────────────────────────────────────────────────────────────┐
│ 分割設定                                                        │
│                                                                 │
│ レビュー方式:  ○ 一括   ◉ 分割                                  │
│                                                                 │
│ ▼ 分割オプション                                                 │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 事前指定                                        【パネル変更】│ │
│ │                                                             │ │
│ │ 設計書の見出し（H2）単位でセクションを表示しています。         │ │
│ │ 重要・除外を事前に指定できます。                               │ │
│ │                                                             │ │
│ │ 事前重要指定: 重要なセクションに個別の分割設定を適用します。   │ │
│ │ 事前除外指定: 不要なセクションを分割・レビューの対象から除外。 │ │
│ │                                                             │ │
│ │  事前重要  事前除外                                          │ │
│ │  指定      指定     #   セクション名         行範囲  推定文字数│ │
│ │ ┌─────┬─────┬───┬────────────────────┬────────┬──────────┐  │ │
│ │ │ ☐   │ ☐   │ 1 │ 概要               │ L1-L5  │   ~104   │  │ │
│ │ │ ☐   │ ☑   │ 2 │ 変更履歴           │ L6-L7  │    ~41   │  │ │
│ │ │ ☑   │ ☐   │ 3 │ 常駐処理設計書     │ L8-L48 │   ~961   │  │ │
│ │ │ ☐   │ ☐   │ 4 │ 画面設計           │ L47-L78│   ~521   │  │ │
│ │ │ ☐   │ ☑   │ 5 │ 目次               │ L79-L90│    ~200  │  │ │
│ │ └─────┴─────┴───┴────────────────────┴────────┴──────────┘  │ │
│ └─────────────────────────────────────────────────────────────┘ │
```

#### 画面②: 分割プレビュー実行

変更なし。事前除外セクションは分割対象から外れるため、分割設定UIへの影響はない。

#### 画面③: 分割結果一覧

事前除外セクションは md2map の `skip` 機能により `parse()` 結果に含まれない。
分割結果一覧には表示されず、分割プレビューのパート数にもカウントされない。

```
│ ■ 設計書: 20 パート                                             │
│                                                                 │
│ 重要 要約 除外  #  セクション名                   行範囲  推定トークン│
│ ┌──┬──┬──┬───┬─────────────────────────────┬────────┬──────────┐│
│ │☐ │☐ │☐ │  1│ 概要                        │L1-L5   │    ~104  ││
│ │☑ │☐ │☐ │  2│ 常駐処理設計書              │L8-L48  │    ~961  ││
│ │  │  │  │   │ ...                         │        │          ││
│ │☐ │☐ │☐ │ 20│ 入力チェック（記述変更）     │L2764-  │  ~1,359  ││
│ │  │  │  │   │                             │L2797   │          ││
│ └──┴──┴──┴───┴─────────────────────────────┴────────┴──────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## 前提

- 現在の実装: `versions/v0.9.2`
- `versions/v0.9.2` を丸ごとコピーして `versions/v0.9.3` を作成し、v0.9.3 上で修正を行う
- md2map の `skip` 機能は v0.3.2 で実装済み（[md2map PR #12](https://github.com/elvezjp/md2map/pull/12)）、subtree で取り込み済み

---

## Step 0: v0.9.3 ディレクトリの作成

- `versions/v0.9.2` を `versions/v0.9.3` にコピー
- v0.9.3 の spec.md にバージョン番号を反映

---

## Step 1: バックエンド — API スキーマの修正

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.3/backend/app/models/schemas.py` | `SplitMarkdownRequest` に `preExcludedSections` を追加 |

### スキーマ変更

#### SplitMarkdownRequest

```python
class SplitMarkdownRequest(BaseModel):
    content: str
    filename: str
    maxDepth: int = Field(default=2, ge=1, le=6)
    splitMode: Literal["ai", "heading", "nlp"] = "ai"
    llmConfig: LLMConfig | None = None
    aiPromptExtraNotes: str | None = None
    # 事前重要指定関連フィールド
    preImportantSections: list[int] | None = None
    preImportantSplitSettings: SplitSettingsDetail | None = None
    normalSplitSettings: SplitSettingsDetail | None = None
    # 事前除外関連フィールド
    preExcludedSections: list[int] | None = None  # ← 追加: 事前除外セクションの start_line リスト
```

※ `DocumentPart` への `preExcluded` フィールド追加は不要。事前除外セクションは結果に含まれないため。

---

## Step 2: バックエンド — エンドポイントの修正

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.3/backend/app/routers/split.py` | `POST /split/markdown` で `preExcludedSections` を md2map の `section_overrides` に `skip: true` として変換 |

### 処理フロー

```python
# 1. section_overrides の構築に事前除外セクションを追加
section_overrides = []

# 事前重要指定セクション（従来通り）
if has_pre_important and request.preImportantSplitSettings:
    for start_line in request.preImportantSections:
        section_overrides.append({
            "start_line": start_line,
            "split_mode": pre_split_mode,
            "max_subsections": ...,
            "ai_prompt_extra_notes": ...,
        })

# 事前除外セクション（新規）
has_pre_excluded = (
    request.preExcludedSections is not None
    and len(request.preExcludedSections) > 0
)
if has_pre_excluded:
    for start_line in request.preExcludedSections:
        section_overrides.append({
            "start_line": start_line,
            "skip": True,
        })

# 2. md2map で分割実行
#    → skip セクションは parse() 結果に含まれない
parser = MarkdownParser(
    ...,
    section_overrides=section_overrides if section_overrides else None,
)
sections, warnings = parser.parse(input_path, request.maxDepth)

# → 除外セクションは結果に含まれないため、補完処理は不要
```

---

## Step 3: フロントエンド — 型定義・API の修正

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.3/frontend/src/features/reviewer/types/index.ts` | `SplitMarkdownRequest` に `preExcludedSections` を追加 |
| `versions/v0.9.3/frontend/src/features/reviewer/services/api.ts` | `splitMarkdown()` リクエストに `preExcludedSections` を追加 |

### 型定義の変更

```typescript
// SplitMarkdownRequest
export interface SplitMarkdownRequest {
  // ... 既存フィールド
  preExcludedSections?: number[]  // ← 追加
}
```

---

## Step 4: フロントエンド — PreImportantPanel の拡張

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.3/frontend/src/features/reviewer/components/PreImportantPanel.tsx` | 事前除外チェックボックス列を追加、排他制御を実装 |

### UI 変更

- テーブルに「事前除外指定」チェックボックス列を追加
- パネルタイトルを「事前指定」に変更（重要・除外の両方を扱うため）
- 説明文を更新: 「重要・除外を事前に指定できます。」
- 重要・除外の説明を追加: 「事前重要指定: 重要なセクションに個別の分割設定を適用します。」「事前除外指定: 不要なセクションを分割・レビューの対象から除外。」

### 排他制御

- 事前重要をON → 同じセクションの事前除外を自動OFF
- 事前除外をON → 同じセクションの事前重要を自動OFF
- Props に `excludedStartLines: number[]` と `onToggleExcluded: (startLine: number) => void` を追加

---

## Step 5: フロントエンド — 状態管理の修正

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.3/frontend/src/features/reviewer/hooks/useSplitSettings.ts` | `preExcludedSections` state 追加、`togglePreExcludedSection()` 追加、`executePreview()` で `preExcludedSections` を API に送信 |
| `versions/v0.9.3/frontend/src/features/reviewer/components/SplitSettingsSection.tsx` | PreImportantPanel に事前除外関連の props を追加 |

### 状態管理の追加

```typescript
const [preExcludedSections, setPreExcludedSections] = useState<number[]>([])

// 排他制御付きトグル
const togglePreExcludedSection = (startLine: number) => {
  setPreExcludedSections(prev =>
    prev.includes(startLine)
      ? prev.filter(s => s !== startLine)
      : [...prev, startLine]
  )
  // 排他制御: 事前重要から除外
  setPreImportantSections(prev => prev.filter(s => s !== startLine))
  // プレビュー結果をクリア
  setPreviewResult(null)
}

// togglePreImportantSection にも排他制御を追加
const togglePreImportantSection = (startLine: number) => {
  setPreImportantSections(prev =>
    prev.includes(startLine)
      ? prev.filter(s => s !== startLine)
      : [...prev, startLine]
  )
  // 排他制御: 事前除外から除外
  setPreExcludedSections(prev => prev.filter(s => s !== startLine))
  setPreviewResult(null)
}
```

### executePreview() の変更

```typescript
const response = await api.splitMarkdown({
  // ... 既存パラメータ
  ...(preExcludedSections.length > 0 ? {
    preExcludedSections,
  } : {}),
})
```

---

## Step 6: テストの追加

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.3/backend/tests/` | `preExcludedSections` パラメータのテスト追加 |
| `versions/v0.9.3/frontend/src/__tests__/` | PreImportantPanel の事前除外UI、排他制御、useSplitSettings の事前除外ロジックのテスト追加 |

### バックエンドテストケース

| ケース | 内容 |
|---|---|
| 事前除外のみ指定 | 除外セクションが結果に含まれないことを確認 |
| 事前重要 + 事前除外を同時指定 | 重要セクションは結果に含まれ、除外セクションは含まれない |
| 全セクションを事前除外 | 結果が空になることを確認 |
| preExcludedSections 未指定 | 従来通りの動作（後方互換性） |

### フロントエンドテストケース

| ケース | 内容 |
|---|---|
| 事前除外チェックボックスの表示 | テーブルに重要・除外の2列のチェックボックスが表示される |
| 排他制御 | 事前重要ON → 事前除外自動OFF、逆も同様 |
| executePreview で preExcludedSections が送信される | API リクエストに含まれる |

---

## Step 7: ドキュメント更新

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.3/spec.md` | 事前除外機能に関する仕様を追記 |
| `docs/split-review.md` | 事前除外機能の説明を追記 |

---

## 修正順序と依存関係

```
Step 0: v0.9.3 作成
  ↓
Step 1: バックエンド スキーマ修正
  ↓
Step 2: バックエンド エンドポイント修正（md2map の skip 機能を利用）
  ↓
Step 3: フロントエンド 型定義・API 修正（Step 1 のスキーマに対応）
  ↓
Step 4: フロントエンド PreImportantPanel 拡張（Step 3 の型を利用）
  ↓
Step 5: フロントエンド 状態管理修正（Step 4 のコンポーネントを利用）
  ↓
Step 6: テスト追加
  ↓
Step 7: ドキュメント更新
```

---

## 影響範囲

| 対象 | 影響 |
|---|---|
| md2map | 変更なし（v0.3.2 の `skip` 機能をそのまま利用） |
| バックエンド | `SplitMarkdownRequest` スキーマ拡張、`POST /split/markdown` で `skip` オーバーライド追加 |
| フロントエンド | `PreImportantPanel` の2列化、状態管理に `preExcludedSections` 追加 |
| ドキュメント | `spec.md` に事前除外の仕様追記、`split-review.md` に機能説明追記 |
| code2map | 変更なし |

---

## 関連

- Issue: [#68 事前重要指定に加えて「事前除外」も設定できるようにする](https://github.com/elvezjp/spec-code-ai-reviewer/issues/68)
- 事前重要指定の計画書: [20260318-pre-split-importance-plan.md](20260318-pre-split-importance-plan.md)
- md2map skip 機能の計画書: [20260324-section-skip-plan.md](../md2map/docs/20260324-section-skip-plan.md)
- md2map skip 機能の Issue: [elvezjp/md2map#11](https://github.com/elvezjp/md2map/issues/11)

---

## 完了チェックリスト

### Step 0: v0.9.3 作成

- [ ] `versions/v0.9.2` を `versions/v0.9.3` にコピー
- [ ] v0.9.3 の全バージョン番号を更新
- [ ] インフラ設定（Docker/Nginx/PM2）に v0.9.3 を追加
- [ ] `latest` シンボリックリンクを v0.9.3 に更新
- [ ] 全バージョンの `useVersions.ts` に v0.9.3 を追加

### Step 1: バックエンド スキーマ修正

- [ ] `SplitMarkdownRequest` に `preExcludedSections` を追加

### Step 2: バックエンド エンドポイント修正

- [ ] `POST /split/markdown` で `preExcludedSections` を `section_overrides` の `skip: true` に変換

### Step 3: フロントエンド 型定義・API 修正

- [ ] `SplitMarkdownRequest` に `preExcludedSections` を追加
- [ ] `splitMarkdown()` リクエストに `preExcludedSections` を追加

### Step 4: フロントエンド PreImportantPanel 拡張

- [ ] 事前除外チェックボックス列の追加
- [ ] 排他制御の実装
- [ ] パネルタイトル・説明文の更新

### Step 5: フロントエンド 状態管理修正

- [ ] `preExcludedSections` state の追加
- [ ] `togglePreExcludedSection()` の追加（排他制御込み）
- [ ] `togglePreImportantSection()` に排他制御を追加
- [ ] `executePreview()` で `preExcludedSections` を API に送信
- [ ] `clearHeadingsCache()` で `preExcludedSections` もリセット

### Step 6: テスト追加

- [ ] バックエンドテスト追加・全テスト通過
- [ ] フロントエンドテスト追加・全テスト通過

### Step 7: ドキュメント更新

- [ ] `versions/v0.9.3/spec.md` に事前除外の仕様を追記
- [ ] `docs/split-review.md` に事前除外の説明を追記

### 最終確認

- [ ] 全バックエンドテスト通過
- [ ] 全フロントエンドテスト通過
- [ ] 手動動作確認（事前除外 → 分割プレビュー → 除外セクションが結果に含まれないことの確認）
