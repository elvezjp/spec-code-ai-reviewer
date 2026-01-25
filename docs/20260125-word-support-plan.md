# Word対応 有効化 変更計画書

作成日: 2026-01-25
更新日: 2026-01-25

> **パス表記**: 想定変更箇所のパスは `versions/v0.7.0/` を基準とする。実体は `versions/v0.7.0/frontend/` 等で要確認。

## 目的
AIレビュアーでWordファイル（主に`.docx`）を**ファイル形式として**選択・変換できるようにし、**複数ファイル混在時でも `.docx` は必ず MarkItDown で変換**されるようにする。

## 背景
- MarkItDownはWord対応だが、UI/フロー上でWordを明示選択できない。
- Word選択時に他ツール（excel2md等）が選べると不整合が起きる。

## 対象範囲
- フロントエンドのファイル種別選択UI
- ファイル入力コンポーネントの受付拡張子
- 変換ツール選択UIとバリデーション
- 変換リクエスト生成ロジック

## 非対象（今回やらない）
- バックエンドのMarkItDown依存追加（別途対応）
- バックエンドAPIの拡張子チェック修正（別途対応）
- `.doc`（旧Word形式）の対応
- 変換品質の改善や差分検証

## 要件
1. UIでWord（.docx）を選択できること（ファイル形式として）
2. 複数ファイルを選んだ場合でも、`.docx` には常に `markitdown` が適用されること
3. Word（.docx）行のツール選択はMarkItDownのみ表示・選択可能であること
4. Word（.docx）送信時の`tool`は必ず`markitdown`になること

## 変更方針
- Word対応は**ファイル形式（拡張子）**で扱う。種別（spec type）にはWordを追加しない
- Word（.docx）行のツール選択UIを固定（選択不可 or MarkItDownのみ表示）
- 既存のバリデーション/デフォルト割当ロジックで `.docx` を明示的に分岐

### Word判定の方式
Word判定は**ファイル拡張子のみ**で行う（`.docx`）。`type`（種別）はファイル形式ではないため、Word判定には使わない。

`.docx` を `addSpecFiles` で追加した際は、`type` は `DEFAULT_TYPE`（設計書）のまま、`tool` のみ `'markitdown'` に設定する。

## 想定変更箇所

### 1. ファイル入力コンポーネント
- `versions/v0.7.0/frontend/src/features/reviewer/index.tsx`
  - `FileInputButton` の `accept` 属性に `.docx` を追加
  - 現状: `accept=".xlsx,.xls"` → 変更後: `accept=".xlsx,.xls,.docx"`
  - カード見出しを「設計書 (Excel)」から「設計書 (Excel / Word)」に変更

### 2. ファイル種別の設定
- **変更なし**。`specTypes` はレビュー用の「種別」であり、ファイル形式ではないためWord項目は追加しない。

### 3. ファイル変換フック
- `versions/v0.7.0/frontend/src/features/reviewer/hooks/useFileConversion.ts`
  - Word判定用のヘルパー関数を追加
  - **addSpecFiles**
    - 拡張子 `.doc` のファイルを除外し、除外した件数があれば `setSpecStatus` でエラーメッセージを設定
    - 除外後、`isMain` は「除外後のリストの先頭」に付与
    - `.docx` のファイルには `tool: 'markitdown'` を設定。`type` は `DEFAULT_TYPE` のまま（Word 判定は拡張子を主とする）
  - **setSpecTool**: Word ファイルに対して `excel2md` 等を渡そうとした場合は無視する（ガード）
  - **applyToolToAll**: 一括で excel2md を選んだ場合、Word（.docx）ファイルには適用しない（Word は markitdown のまま）
  - **convertSpecs**: API 呼び出し時に、Word の場合は `tool` を `'markitdown'` に正規化してから送信（防御的な二重チェック）

### 4. ファイルリストUI
- `versions/v0.7.0/frontend/src/features/reviewer/components/SpecFileList.tsx`
  - Word（.docx）ファイル行のツール選択 UI を固定（MarkItDownのみ表示/disabled）
  - 「WordはMarkItDownのみ対応」の補足テキスト表示
  - **一括設定**: 一括で excel2md を選んだ場合の Word 除外は `useFileConversion.applyToolToAll` 内で行う。任意で、Word が 1 件でも含まれるときに excel2md の一括ボタンを無効化する UI にしてもよい。

## UI仕様（案）
- Word（.docx）ファイル行のツール選択
  - 表示: 「MarkItDown」のみ
  - 操作: 選択不可（固定）
  - 補足文: 「WordはMarkItDownのみ対応」等の説明を表示
- `.doc` ファイルがアップロードされた場合（`addSpecFiles` 内で除外し、`setSpecStatus` で表示）
  - 基本: 「.doc形式は非対応です。.docx形式で保存し直してください」
  - 他形式と混在して .doc のみ除外した場合は、「（n件を除外）」等を付与してよい

## 受け入れ条件
- Wordファイル（.docx）を選択できる
- 複数ファイル混在時でも、`.docx` は常に MarkItDown に固定される
- Word（.docx）行で他ツールが選べない
- Word（.docx）送信時のリクエストが`tool: markitdown`で送信される
- 既存のExcelなどの挙動が変わらない
- .docファイルは拒否され、適切なエラーメッセージが表示される

## テスト観点
- Word（.docx）ファイルが選択できる
- 複数ファイル混在時でも `.docx` 行のツールがMarkItDownに固定される
- 一括ツール適用時でも `.docx` はMarkItDownのまま
- Word以外のファイル選択時は従来通りツール選択が可能
- 画面リロード後も選択状態が崩れない
- .docファイルがアップロードされた場合にエラーが表示される

## バックエンドとの連携方針

### 前提条件
バックエンド側では現在、`/api/convert/excel-to-markdown` エンドポイントで `.xlsx`, `.xls` のみを受け付けている。Word対応には以下のバックエンド修正が別途必要：
- `versions/v0.7.0/backend/app/routers/convert.py` の拡張子チェックに `.docx` を追加

### リリース方針
以下のいずれかを選択する：

**案A: 同時リリース（推奨）**
- フロントエンドとバックエンドの修正を同時にリリース
- ユーザーは即座にWord変換機能を利用可能

**案B: 段階的リリース**
- フロントエンドを先行リリースし、Word選択UIに「準備中」と表示
- バックエンド対応完了後にUI制限を解除

## リスク/留意点
- Word対応のバックエンド依存が未導入だと変換が失敗する
  - → バックエンド対応と同時リリースを前提とする
- `.doc`非対応であることをUIで明示する必要がある
  - → アップロード時にエラーメッセージを表示
- APIエンドポイント名が `excel-to-markdown` のままになる
  - → 将来的に汎用的な名称への変更を検討（バックエンド側の課題）

## 進め方（作業手順）
1. `index.tsx`: FileInputButton の `accept` に `.docx` を追加し、カード見出しを「設計書 (Excel / Word)」に変更
2. `useFileConversion.ts`: Word 判定ヘルパー、addSpecFiles（.doc 除外・setSpecStatus・isMain の付け直し・.docx 時の tool 設定）、setSpecTool のガード、applyToolToAll の Word 除外、convertSpecs の tool 正規化を追加
3. `SpecFileList.tsx`: Word（.docx）行のツール固定、補足文を実装。一括設定の Word 除外は 2. の `applyToolToAll` で対応済み。任意で、Word が 1 件でも含まれるときに excel2md の一括ボタンを無効化する UI を追加してもよい
4. `.doc` のエラーハンドリングは 2. の `addSpecFiles` 内で実施（.doc を除外し、除外件数があれば `setSpecStatus` で「.doc形式は非対応です。.docx形式で保存し直してください」等を表示）
5. 既存のファイル種別（Excel 等）でリグレッション確認
6. バックエンド対応と合わせて結合テスト
