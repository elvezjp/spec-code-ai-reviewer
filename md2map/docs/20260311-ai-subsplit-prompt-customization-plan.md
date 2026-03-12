# AI サブスプリット プロンプトカスタマイズ対応 計画書

作成日: 2026-03-11
関連Issue: #4（AIサブスプリットの分割位置が不適切になる場合がある）
ステータス: **対応完了**（v0.3.0 としてリリース済み）

## 1. 背景と目的

### 現状の課題

1. **プロンプトがハードコード**: `_select_chunks_ai()` 内にシステムプロンプトが直接記述されており、外部から変更・追記する手段がない
2. **構造ブロックの保護指示が不十分**: Mermaid ブロックやコードブロックの途中で分割されるケースがある
3. **分割観点の指定不可**: 分割数は `max_subsections` で制御できるが、「項番単位で分割」「処理フロー単位で分割」等の分割の観点を呼び出し元から指定できない
4. **外部アプリからの制御**: spec-code-ai-reviewer 等の外部アプリが `MarkdownParser` を呼び出す際、プロンプトをカスタマイズする手段がない

### 目的

- システムプロンプトを構造化し、`notes`（注意事項）パートへの追記を外部から行えるようにする
- CLI および外部アプリ（関数呼び出し）の両方からプロンプトカスタマイズを可能にする
- Issue #4 対応案 A（プロンプト改善）の土台を整備する

---

## 2. 現状分析

### 2.1 現在のシステムプロンプト構成

`md2map/parsers/markdown_parser.py` L644-671 に以下の 4 パートで構成：

| パートキー | 見出し | 内容 |
|-----------|--------|------|
| `role` | `# 役割` | 「文書構造の分析に特化したアシスタント」 |
| `purpose` | `# 目的` | 「意味的なまとまりが壊れないよう話題や内容の切れ目で区切る」+ タイトル付与 |
| `format` | `# 出力形式` | JSON 配列スキーマ（title, start_line, end_line） |
| `notes` | `# 注意事項` | 意味的グルーピング、カバレッジ、言語合わせ等 |

### 2.2 外部アプリからの呼び出し例

`spec-code-ai-reviewer` の `split.py` L99-103:

```python
parser = MarkdownParser(
    split_mode=request.splitMode,
    llm_config=md2map_llm_config,
    max_subsections=max_subsections,
)
```

現状プロンプトをカスタマイズするパラメータは存在しない。

### 2.3 CLI の呼び出し

`md2map/cli.py` L136-141:

```python
parser = MarkdownParser(
    split_mode=args.split_mode,
    split_threshold=args.split_threshold,
    max_subsections=args.max_subsections,
    llm_config=llm_config,
)
```

---

## 3. 設計

### 3.1 システムプロンプト構成の構造化

4 パートの構成を固定キーの辞書として定義する。各パートは「デフォルトテキスト」を持つ。

```python
# デフォルトのシステムプロンプトパート定義
DEFAULT_AI_PROMPT_PARTS: Dict[str, str] = {
    "role": (
        "あなたは文書構造の分析に特化したアシスタントです。"
    ),
    "purpose": (
        "行番号付きテキストを、意味的なまとまりが壊れないよう"
        "話題や内容の切れ目で区切ってください。\n"
        "各区間には、その内容を端的に表すタイトルを付与してください。"
    ),
    "format": (
        "JSON 配列のみを返してください。説明文やマークダウン装飾は不要です。\n"
        "各要素は以下のフィールドを持つオブジェクトです:\n"
        "- title (string): 区間の内容を表す簡潔なタイトル（文書の言語に合わせる）\n"
        "- start_line (integer): 区間の開始行番号\n"
        "- end_line (integer): 区間の終了行番号（inclusive）\n"
        "\n"
        "スキーマ:\n"
        "[{\"title\": \"...\", \"start_line\": 1, \"end_line\": ...}, ...]"
    ),
    "notes": (
        "- 意味的に関連する行は同じ区間に含め、話題の変わり目で区切ること\n"
        "- 最初の区間は行 1 から開始すること\n"
        "- 前の区間の end_line + 1 が次の区間の start_line と一致すること"
        "（隙間・重複の禁止）\n"
        "- タイトルは元の文書の言語（日本語の文書なら日本語）で付与すること"
    ),
}
```

**注意**: 実行時に変わる情報（`total_lines` 等）はユーザープロンプトに記載する方針のため、システムプロンプトには含めない。

### 3.2 カスタマイズ方法

`notes`（注意事項）パートへの **追記** のみを提供する。

他の 3 パート（`role`, `purpose`, `format`）は機能の根幹やレスポンスバリデーションと密結合しているため、外部からの変更は許可しない。

#### インターフェース

`MarkdownParser` に `Optional[str]` 型の `ai_prompt_extra_notes` 引数を追加する。指定された場合、`notes` パートのデフォルトテキスト末尾に改行区切りで追記される。

#### 使用例

```python
# 呼び出し元から notes に追記する例
parser = MarkdownParser(
    split_mode="ai",
    llm_config=llm_config,
    ai_prompt_extra_notes=(
        "- Mermaid ブロック（```mermaid ... ```）やコードブロックの途中では分割しないこと\n"
        "- 項番単位で分割すること"
    ),
)
```

### 3.3 `MarkdownParser` のインターフェース変更

```python
class MarkdownParser(BaseParser):
    def __init__(
        self,
        split_mode: str = "heading",
        split_threshold: int = 500,
        max_subsections: int = 5,
        llm_config: Optional["LLMConfig"] = None,
        llm_provider: Optional["BaseLLMProvider"] = None,
        ai_prompt_extra_notes: Optional[str] = None,  # 追加
    ) -> None:
        ...
        self._ai_prompt_extra_notes = ai_prompt_extra_notes
```

### 3.4 プロンプト組み立てメソッドの抽出

`_select_chunks_ai()` 内のプロンプト構築ロジックを専用メソッドに抽出する。

```python
def _build_ai_system_prompt(self) -> str:
    """AI サブスプリット用のシステムプロンプトを組み立てる

    実行時に変わる情報（total_lines 等）はユーザープロンプトに記載するため、
    システムプロンプトには含めない。
    """
    parts = dict(DEFAULT_AI_PROMPT_PARTS)

    # notes パートへの追記
    if self._ai_prompt_extra_notes:
        parts["notes"] = parts["notes"] + "\n" + self._ai_prompt_extra_notes

    return (
        f"# 役割\n{parts['role']}\n\n"
        f"# 目的\n{parts['purpose']}\n\n"
        f"# 出力形式\n{parts['format']}\n\n"
        f"# 注意事項\n{parts['notes']}\n"
    )
```

### 3.5 ユーザープロンプトの変更

現行のユーザープロンプトに、実行時に決まる制約（`total_lines`）を移動する。

**変更前:**
```
以下のテキストを、意味的なまとまりを保ちつつ最大 {target_parts} つに区切ってください。

{numbered_text}
```

**変更後:**
```
以下のテキストを、意味的なまとまりを保ちつつ最大 {target_parts} つに区切ってください。
テキストは全 {total_lines} 行です。最後の区間は行 {total_lines} で終了してください（すべての行を漏れなくカバー）。

{numbered_text}
```

方針: 実行ファイルに応じて変わる内容（行数等）はシステムプロンプトではなくユーザープロンプトに記載する。

### 3.6 CLI 対応

CLI には `--ai-prompt-extra-notes` オプションを追加し、`notes` パートへの追記を簡易に行えるようにする。

```
md2map build input.md --split-mode ai \
    --ai-prompt-extra-notes "- Mermaid ブロックの途中では分割しないこと"
```

```python
# cli.py に追加
build_parser.add_argument(
    "--ai-prompt-extra-notes",
    default=None,
    help="AI サブスプリットの注意事項に追記するテキスト",
)
```

`cmd_build()` 内:

```python
parser = MarkdownParser(
    split_mode=args.split_mode,
    split_threshold=args.split_threshold,
    max_subsections=args.max_subsections,
    llm_config=llm_config,
    ai_prompt_extra_notes=args.ai_prompt_extra_notes,
)
```

---

## 4. 変更対象ファイル

| ファイル | 変更内容 |
|---------|----------|
| `md2map/parsers/markdown_parser.py` | `DEFAULT_AI_PROMPT_PARTS` 定義、`__init__` に `ai_prompt_extra_notes` 引数追加、`_build_ai_system_prompt()` メソッド追加、`_select_chunks_ai()` のシステムプロンプト組み立てを置換・タイトル生成廃止、ユーザープロンプトに `total_lines` 制約を移動、`_build_virtual_sections_with_titles()` 削除 |
| `md2map/cli.py` | `--ai-prompt-extra-notes` オプション追加、`cmd_build()` で `ai_prompt_extra_notes` を渡し |
| `tests/test_llm.py` | プロンプトカスタマイズ関連のテスト追加 |

---

## 5. テスト計画

### 5.1 ユニットテスト

| テストケース | 検証内容 |
|-------------|----------|
| `test_default_prompt_unchanged` | `ai_prompt_extra_notes` 未指定時、従来と同一のプロンプトが生成される |
| `test_prompt_extra_appended` | `ai_prompt_extra_notes` で指定したテキストが `notes` パートの末尾に追記される |
| `test_prompt_extra_none` | `ai_prompt_extra_notes=None` の場合、デフォルトのプロンプトがそのまま使用される |
| `test_total_lines_in_user_prompt` | ユーザープロンプトに `total_lines` が正しく含まれる |

### 5.2 結合テスト

| テストケース | 検証内容 |
|-------------|----------|
| `test_ai_mode_with_prompt_extra` | `ai_prompt_extra_notes` 付きで `MarkdownParser.parse()` が正常動作する |
| `test_cli_ai_prompt_extra_notes` | CLI の `--ai-prompt-extra-notes` が LLM 呼び出し時のプロンプトに反映される |

---

## 6. 対応案 A（プロンプト改善）

本計画（対応案 B）の実装と合わせて、以下のプロンプト改善を行う。

### 6.1 タイトル生成の廃止

AI にサブスプリットのタイトル生成を求めるのをやめ、分割位置の決定に集中させる。

**理由:**
- タイトル生成は分割精度に寄与しない
- `title` フィールド分のトークンが減り、応答速度・コスト改善
- バリデーションが簡素化される（`title` の空文字チェック等が不要に）
- AI モードも NLP モードと同様に `part-N` 形式に統一され、コードが整理される

**変更内容:**

| 対象 | 変更 |
|------|------|
| `purpose` パート | 「各区間には、その内容を端的に表すタイトルを付与してください。」を削除 |
| `format` パート | `title` フィールドを削除。スキーマを `[{"start_line": 1, "end_line": ...}]` に変更 |
| `notes` パート | 「タイトルは元の文書の言語で付与すること」を削除 |
| `_select_chunks_ai()` | `title` の抽出・返却を削除。常に `titles=None` を返す |
| `_build_virtual_sections_with_titles()` | 削除 |
| AI モードの分割フロー | 常に `_build_virtual_sections()`（`part-N` 形式）を使用 |

**変更後の `DEFAULT_AI_PROMPT_PARTS`:**

```python
DEFAULT_AI_PROMPT_PARTS: Dict[str, str] = {
    "role": (
        "あなたは文書構造の分析に特化したアシスタントです。"
    ),
    "purpose": (
        "行番号付きテキストを、文書の構造や意味的なまとまりを保ちつつ"
        "話題や内容の切れ目で区切ってください。"
    ),
    "format": (
        "JSON 配列のみを返してください。説明文やマークダウン装飾は不要です。\n"
        "各要素は以下のフィールドを持つオブジェクトです:\n"
        "- start_line (integer): 区間の開始行番号\n"
        "- end_line (integer): 区間の終了行番号（inclusive）\n"
        "\n"
        "スキーマ:\n"
        "[{\"start_line\": 1, \"end_line\": ...}, ...]"
    ),
    "notes": (
        "- 最初の区間は行 1 から開始すること\n"
        "- 前の区間の end_line + 1 が次の区間の start_line と一致すること"
        "（隙間・重複の禁止）\n"
        "- ネストされた項目は親項目と同じ区間に含めること"
        "（インデントが深い行を親から切り離さない）\n"
        "- 構造を保ちつつ、各区間のサイズが極端に偏らないよう"
        "バランスよく分割すること"
    ),
}
```

### 6.2 `notes` パートのデフォルト改善

デフォルトの `notes` に以下を追加する（Issue #4 の本題）。

**ネスト構造の保護:**
```
- ネストされた項目は親項目と同じ区間に含めること（インデントが深い行を親から切り離さない）
```

**分割バランス:**
```
- 構造を保ちつつ、各区間のサイズが極端に偏らないようバランスよく分割すること
```

Mermaid ブロックやコードブロックの保護はデフォルトには含めない。必要な場合は `ai_prompt_extra_notes` で呼び出し元から追記する。

例えば、以下のようなネスト構造がある場合：
```
1: - 話題A
2:   - 話題B
3:   - 話題C
4: - 話題D
5:   - 話題E
6: - 話題F
```

3 分割時、`[1-2][3][4-6]` のようにネスト途中で区切るのではなく、
トップレベル項目の境界で `[1-3][4-5][6]` のように区切ることを期待する。

### 6.3 `purpose` との重複削除

現行の `notes` にある「意味的に関連する行は同じ区間に含め、話題の変わり目で区切ること」は `purpose` パートと重複しているため削除する。

---

## 7. タスク

### 7.1 準備

1. 現在（v0.2）の実装を `versions/v0.2.0/` に保持（`md2map/`, `pyproject.toml`, `spec.md`, `tests/`, `main.py`, `uv.lock`）
2. `pyproject.toml` のバージョンを v0.3.0 に更新
3. `spec.md` を更新（プロンプト構造化、タイトル生成廃止、`ai_prompt_extra_notes` 引数、`--ai-prompt-extra-notes` CLI オプション）
  - (v0.3で追加)のような記載はしない。最新仕様が反映された仕様書として更新する。

### 7.2 実装（対応案 B: プロンプトカスタマイズ）

4. `DEFAULT_AI_PROMPT_PARTS` 定数の定義
5. `_build_ai_system_prompt()` メソッドの実装
6. `MarkdownParser.__init__` に `ai_prompt_extra_notes` 引数追加
7. `_select_chunks_ai()` のシステムプロンプト組み立てを `_build_ai_system_prompt()` 呼び出しに置換
8. `_select_chunks_ai()` のユーザープロンプトに `total_lines` 制約を移動
9. CLI の `--ai-prompt-extra-notes` オプション追加

### 7.3 実装（対応案 A: プロンプト改善）

10. タイトル生成の廃止（`format` から `title` 削除、`_select_chunks_ai()` のタイトル処理削除、`_build_virtual_sections_with_titles()` 削除）
11. `purpose` の更新（「文書の構造や意味的なまとまりを保ちつつ」）
12. `notes` のデフォルト改善（ネスト構造保護、分割バランス指示追加、`purpose` 重複削除）

### 7.4 テスト・検証

13. ユニットテスト作成・実行
14. 結合テスト作成・実行
15. `docs/examples/v0.3/` にサンプル実行結果を出力（heading / nlp / ai 各モード）

## 7.5 ドキュメント更新
16. `spec.md`の再確認（仕様書と実装が一致していること）
17. `CHANGELOG.md` に v0.3.0 の変更履歴を追加
18. `versions/README.md` を更新（ディレクトリ構成例に `v0.3.0/` を追記、各バージョンの比較表を追加）

---

## 8. 完了チェックリスト

### 8.1 機能テスト

- [x] `ai_prompt_extra_notes` 未指定時、デフォルトプロンプトで正常に分割される（ユニットテスト `test_default_prompt_unchanged`）
- [x] `ai_prompt_extra_notes` 指定時、`notes` パート末尾に追記される（ユニットテスト `test_prompt_extra_appended`）
- [x] ユーザープロンプトに `total_lines` が含まれる（ユニットテスト `test_total_lines_in_user_prompt`）
- [x] AI レスポンスに `title` が含まれなくてもバリデーションが通る（ユニットテスト `test_prompt_no_title_field`）
- [x] `--ai-prompt-extra-notes` CLI オプションが LLM 呼び出しに反映される（ユニットテスト `test_prompt_extra_passed_to_llm`）
- [x] AI モードで `_build_virtual_sections()`（`part-N` 形式）が使われる（ユニットテスト `test_ai_mode_provider_called_on_parse`）

### 8.2 後方互換性

- [x] `ai_prompt_extra_notes` 未指定時、既存の呼び出しコードが変更なしで動作する（既存テストが全て PASS: 83/83）
- [x] `split_mode=heading` / `split_mode=nlp` に影響がない（既存テストが全て PASS: 83/83）

### 8.3 成果物

- [x] `versions/v0.2.0/` に旧バージョンが保持されている
- [x] `pyproject.toml` のバージョンが v0.3.0 になっている
- [x] `spec.md` が最新の設計を反映している
- [x] `docs/examples/v0.3/` にサンプル実行結果が出力されている（heading / nlp / ai 各モード）
