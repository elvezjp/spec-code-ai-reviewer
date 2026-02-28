# AIでMarkdown整理 - トークン上限チェック廃止計画

## 背景

「AIでMarkdown整理」機能は、元の設計書にIDを付与したり構造を明確化することが目的であり、トークン数を削減することは目的に含まれていない。

現状のバックエンド（`organize.py`）では、入力トークン数が`ORGANIZE_MAX_INPUT_TOKENS`（既定値: 20,000）を超える場合にセクション分割して処理する仕組みがあるが、以下の問題がある:

1. セクション分割しても、LLMの出力が途中で切れる事象が発生する（「設計書が膨大なため、N番まで表示しました」等の出力）
2. 分割レビュー機能が追加されたため、整理後のファイルが大きくても分割レビューで対応可能
3. トークン削減は本機能の目的に合っていない

## 修正方針

### 1. バックエンド: トークン上限チェック・セクション分割ロジックの廃止

**対象ファイル:** `backend/app/routers/organize.py`

**現状（90〜119行目）:**

```python
estimated_tokens = estimate_tokens(preprocessed_markdown + "\n" + request.policy)
if estimated_tokens > _MAX_INPUT_TOKENS:
    sections = split_markdown_by_section(preprocessed_markdown)
    if len(sections) <= 1:
        return OrganizeMarkdownResponse(
            success=False,
            error="入力が長すぎます。章単位で分割してください。",
            errorCode="token_limit",
        )

    organized_sections: list[str] = []
    for section in sections:
        section_tokens = estimate_tokens(section + "\n" + request.policy)
        if section_tokens > _MAX_INPUT_TOKENS:
            return OrganizeMarkdownResponse(
                success=False,
                error="入力が長すぎます。章単位で分割してください。",
                errorCode="token_limit",
            )

        ok, organized, error_code, error_message = await run_with_retry(section)
        if not ok or organized is None:
            return OrganizeMarkdownResponse(...)
        organized_sections.append(organized.strip())

    organized = "\n\n".join([section for section in organized_sections if section])
else:
    ok, organized, error_code, error_message = await run_with_retry(preprocessed_markdown)
    ...
```

**変更後:**

- `_MAX_INPUT_TOKENS` 定数、`estimate_tokens`、`split_markdown_by_section` のインポートと使用箇所を削除
- トークン数チェックの分岐を廃止し、常に入力全体を `run_with_retry` に渡す

```python
ok, organized, error_code, error_message = await run_with_retry(preprocessed_markdown)
if not ok or organized is None:
    return OrganizeMarkdownResponse(
        success=False,
        error=error_message or "Markdown整理に失敗しました。",
        errorCode=error_code or "api_error",
    )
```

### 2. フロントエンド: エラーコードの保持

**対象ファイル:** `frontend/src/features/reviewer/components/MarkdownOrganizer.tsx`

**現状（180〜181行目）:**

```typescript
if (!result.success) {
  throw new Error(`[${file.filename}] ${result.error || '整理に失敗しました'}`)
}
```

APIレスポンスの `errorCode` が `throw new Error()` の過程で失われている。

**変更後:**

エラー時に `errorCode` を保持するようにする。

```typescript
if (!result.success) {
  setError({
    code: result.errorCode,
    message: `[${file.filename}] ${result.error || '整理に失敗しました'}`,
  })
  setStatus(`❌ [${file.filename}] ${result.error || '整理に失敗しました'}`)
  return  // 以降のファイル処理を中断
}
```

※ `throw` ではなく直接 `setError` で設定し、`finally` ブロックで `setIsProcessing(false)` が実行されるようにループを中断する。

### 3. フロントエンド: 注意書きの追加

**対象ファイル:** `frontend/src/features/reviewer/components/MarkdownOrganizer.tsx`

**現状（284〜286行目）:**

```tsx
<p className="text-xs text-gray-400">
  ※ 設計書が大きい場合は、処理に時間が掛かったり、タイムアウトや制限等でエラーになる可能性があります。
</p>
```

**変更後:**

```tsx
<p className="text-xs text-gray-400">
  ※ 設計書が大きい場合は、処理に時間が掛かったり、タイムアウトや制限等でエラーになる可能性があります。
  また、一部の情報や制約が失われることがあります。分割設定でのレビューもお試しください。
</p>
```

## 変更対象ファイル一覧

| ファイル | 変更内容 |
|----------|----------|
| `backend/app/routers/organize.py` | トークン上限チェック・セクション分割ロジック削除 |
| `frontend/.../MarkdownOrganizer.tsx` | エラーコード保持、注意書き追加 |

## 変更しないもの

- `OrganizerAlerts.tsx`: エラーコードに応じた表示タイトル（`token_limit` → 「トークン超過」等）は、LLM APIからのトークン関連エラーの表示に引き続き有用なため、そのまま残す
- `backend/app/services/markdown_organizer.py`: `estimate_tokens`、`split_markdown_by_section` 関数は他の箇所で利用される可能性があるため、関数自体は残す（`organize.py` からの呼び出しのみ削除）
- バックエンドのリトライ・タイムアウト処理: 引き続き必要
- `_TIMEOUT_SECONDS`、`_MAX_RETRIES`: 引き続き使用
