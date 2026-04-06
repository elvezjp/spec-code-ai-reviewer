# Word（.docx）対応 実装計画

## 背景

- Issue: #26（MarkItDownの機能を用いたワード対応について）
- 参考PR: #27（v0.7.0向けに作成されたが未マージ。v0.9.7対応として本計画で引き継ぐ）

## 方針

- `versions/v0.9.6/` を `versions/v0.9.7/` としてコピーし、以下の変更を加える
- `.doc`（旧形式）はMarkItDown非対応のため、UIで除外しエラーメッセージを表示する
- `.docx` のツールは MarkItDown に固定する（excel2md は Word 非対応のため）
- バックエンドのAPIエンドポイントは**既存の `/excel-to-markdown` を変更せず**、新たに `/word-to-markdown` を追加する
  - CHANGELOGを確認した結果、既存エンドポイントの削除・リネームの前例がないため、後方互換性を維持する方針とする

## 変更ファイル一覧

### 1. バックエンド

#### `versions/v0.9.7/backend/pyproject.toml`

- バージョンを `0.9.6` → `0.9.7` に更新
- `markitdown[xlsx,docx]` に変更（`mammoth` と `lxml` が追加インストールされる）

```toml
# 変更前
"markitdown[xlsx]>=0.0.1a3",

# 変更後
"markitdown[xlsx,docx]>=0.0.1a3",
```

#### `versions/v0.9.7/backend/app/routers/convert.py`

- 新エンドポイント `POST /word-to-markdown` を追加
  - 対応拡張子: `.docx` のみ（`.doc` は除外）
  - ツールは `markitdown` に固定（リクエストパラメータで上書き不可）
  - サイズ上限は既存の `/excel-to-markdown` と同じ 10MB
- 既存の `/excel-to-markdown` は変更しない

### 2. フロントエンド

#### `versions/v0.9.7/frontend/src/features/reviewer/services/api.ts`

- `convertWordToMarkdown()` 関数を追加（`/word-to-markdown` を呼び出す）

#### `versions/v0.9.7/frontend/src/features/reviewer/hooks/useFileConversion.ts`

- `.doc` ファイルをフィルタして除外し、ステータスにエラーメッセージを表示
- `.docx` ファイルのツールを `markitdown` に固定（`setSpecTool` / `applyToolToAll` のガード追加）
- `convertSpecs` で `.docx` は `/word-to-markdown`、それ以外は `/excel-to-markdown` に振り分け

#### `versions/v0.9.7/frontend/src/features/reviewer/index.tsx`

- ファイル選択の `accept` に `.docx` を追加
- セクション見出しを「設計書 (Excel / Word)」に更新

```tsx
// 変更前
<h2 ...>設計書 (Excel)</h2>
<FileInputButton accept=".xlsx,.xls" ...>

// 変更後
<h2 ...>設計書 (Excel / Word)</h2>
<FileInputButton accept=".xlsx,.xls,.docx" ...>
```

#### `versions/v0.9.7/frontend/src/features/reviewer/components/SpecFileList.tsx`

- `.docx` 行のツール選択を `disabled` に固定し「WordはMarkItDownのみ対応」の補足テキストを表示

### 3. インフラ

#### `nginx/version-map.conf`

- v0.9.7 のルーティングを追加し、default を 8097 番ポートに変更

## スコープ外

- `.doc`（旧形式）への対応（MarkItDown非対応のため）
- テスト（`useFileConversion.test.ts`）の更新は別途対応

## 動作確認観点

- [ ] `.docx` を選択でき、ツールが MarkItDown に固定される
- [ ] `.docx` と `.xlsx` の混在時、`.docx` は常に MarkItDown のまま
- [ ] 一括ツール変更（applyToolToAll）でも `.docx` は MarkItDown のまま
- [ ] `.doc` を選択した場合、除外されエラーメッセージが表示される
- [ ] 既存の Excel（.xlsx / .xls）の挙動に変更がない
- [ ] バックエンドで `.docx` ファイルが `/word-to-markdown` 経由で正常に変換される
