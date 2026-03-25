# INDEX.md サマリー改善 修正計画書

> **対応完了**: PR [#16](https://github.com/elvezjp/md2map/pull/16) / Issue [#15](https://github.com/elvezjp/md2map/issues/15) にて v0.4.0 として実装済み。全 121 テストパス、v0.3.2 との後方互換性確認済み。

## 概要

INDEX.md のセクション詳細に出力される `summary` を改善する。

- **案A**: ルールベースの文字数上限をパラメータで変更可能にする
- **案B**: LLMによる要約生成モード（`--summary-mode ai`）を追加する

対応 Issue: [#15](https://github.com/elvezjp/md2map/issues/15)

## 背景

- 現在の `summary` は見出し直後の最初の段落を100文字で切り詰めているだけであり、「要約」と呼ぶには不十分
- テーブル主体のセクションではパイプ記号・NaN がそのまま残り、ノイズになっている
- LLMが利用できない環境でも使えるようにしたいため、案Aと案Bの両方を実装する

## 前提

- 現在の実装: md2map ルート（`md2map/`）、バージョン v0.3.2
- 今回の修正は v0.4.0 として実装する
- ルールベース改善（案A）は過度に複雑にせず、文字数上限のパラメータ化に留める

---

## Step 0: v0.3.2 の退避と v0.4.0 の準備

### v0.3.2 の退避

現在の実装を `versions/v0.3.2` に退避する。

```
対象ファイル:
  md2map/         → versions/v0.3.2/md2map/
  tests/          → versions/v0.3.2/tests/
  main.py         → versions/v0.3.2/main.py
  pyproject.toml  → versions/v0.3.2/pyproject.toml
  uv.lock         → versions/v0.3.2/uv.lock
  spec.md         → versions/v0.3.2/spec.md
```

### v0.4.0 の準備

- `pyproject.toml` の `version` を `"0.4.0"` に更新
- `spec.md` にバージョン番号を反映

---

## Step 1: 案A — `summary_max_chars` のパラメータ化

### 設計

`_extract_summary()` の固定100文字を、外部から設定可能にする。

#### グローバルオプション

| オプション | デフォルト | 説明 |
|---|---|---|
| `--summary-max-chars <N>` | `100` | ルールベースサマリーの文字数上限 |

#### セクションオーバーライド

`--section-overrides` で `summary_max_chars` をセクション単位で指定可能にする。

```json
[
  {"start_line": 6, "summary_max_chars": 200},
  {"start_line": 52, "summary_max_chars": 50}
]
```

### 実装

#### MarkdownParser コンストラクタ

```python
def __init__(
    self,
    split_mode: str = "heading",
    split_threshold: int = 500,
    max_subsections: int = 5,
    llm_config: Optional["LLMConfig"] = None,
    llm_provider: Optional["BaseLLMProvider"] = None,
    ai_prompt_extra_notes: Optional[str] = None,
    section_overrides: Optional[List[Dict[str, any]]] = None,
    summary_max_chars: int = 100,         # 追加
    summary_mode: str = "text",           # 追加（Step 2 で使用）
) -> None:
    # ...
    self.summary_max_chars = max(1, summary_max_chars)
    self.summary_mode = summary_mode
```

#### `_resolve_settings()`

```python
def _resolve_settings(self, section):
    default = {
        "split_mode": self.split_mode,
        "split_threshold": self.split_threshold,
        "max_subsections": self.max_subsections,
        "ai_prompt_extra_notes": self._ai_prompt_extra_notes or "",
        "skip": False,
        "summary_max_chars": self.summary_max_chars,    # 追加
        "summary_mode": self.summary_mode,              # 追加（Step 2 で使用）
    }
    # ... 以下同じ
```

#### `_extract_section_info()`

設定に基づいて `_extract_summary()` に文字数上限を渡す。

```python
def _extract_section_info(self, section, lines):
    settings = self._resolve_settings(section)
    max_chars = settings["summary_max_chars"]

    section_lines = lines[section.start_line - 1 : section.end_line]
    section_text = "".join(section_lines)

    skip_first = self.HEADING_PATTERN.match(section_lines[0].rstrip()) is not None
    section.summary = self._extract_summary(
        section_lines, skip_first_line=skip_first, max_chars=max_chars
    )
    # ... リンク、キーワード、単語数は変更なし
```

#### `_extract_summary()`

```python
def _extract_summary(self, lines, skip_first_line=True, max_chars=100):
    """最初の段落を要約として抽出する

    Args:
        lines: セクションの行リスト
        skip_first_line: 最初の行をスキップするか
        max_chars: 最大文字数

    Returns:
        要約文字列、なければ None
    """
    # ... 既存のロジック（段落抽出）は変更なし ...

    if len(summary) > max_chars:
        summary = summary[:max_chars - 3] + "..."

    return self._sanitize_summary(summary)
```

#### `_sanitize_summary()` の新規追加

サマリーの生成方式（text / ai）にかかわらず、INDEX.md の `- summary:` 行に安全に出力できるようサニタイズする。

```python
def _sanitize_summary(self, summary: Optional[str]) -> Optional[str]:
    """サマリー文字列をサニタイズする

    - 改行を除去して1行にする
    - 前後の空白を除去する

    Args:
        summary: サニタイズ対象の文字列

    Returns:
        サニタイズ済み文字列、None の場合は None
    """
    if summary is None:
        return None
    return " ".join(summary.strip().splitlines())
```

#### CLI（`cli.py`）

```python
build_parser.add_argument(
    "--summary-max-chars",
    type=int,
    default=100,
    help="ルールベースサマリーの文字数上限（デフォルト: 100）",
)
```

```python
parser = MarkdownParser(
    # ... 既存引数 ...
    summary_max_chars=args.summary_max_chars,
)
```

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `md2map/parsers/markdown_parser.py` | コンストラクタに `summary_max_chars` 追加、`_resolve_settings()` に追加、`_extract_section_info()` で設定値を使用、`_extract_summary()` に `max_chars` 引数追加、`_sanitize_summary()` 新規追加 |
| `md2map/cli.py` | `--summary-max-chars` オプション追加、`MarkdownParser` に引数渡し |

---

## Step 2: 案B — `--summary-mode ai` の追加

### 設計

分割モード（`--split-mode`）とは独立したオプションとして、サマリー生成モードを追加する。

#### グローバルオプション

| オプション | デフォルト | 説明 |
|---|---|---|
| `--summary-mode <MODE>` | `text` | サマリー生成モード（`text`/`ai`） |

#### セクションオーバーライド

```json
[
  {"start_line": 6, "summary_mode": "ai"},
  {"start_line": 52, "summary_mode": "text", "summary_max_chars": 200}
]
```

#### 使用例

```bash
# グローバル: ルールベース200文字、セクション6だけAI要約
uv run md2map build input.md \
  --summary-max-chars 200 \
  --section-overrides '[{"start_line": 6, "summary_mode": "ai"}]'

# グローバル: AI要約、セクション52だけルールベースに戻す
uv run md2map build input.md \
  --summary-mode ai \
  --section-overrides '[{"start_line": 52, "summary_mode": "text"}]'

# 分割モードとサマリーモードの独立した組み合わせ
uv run md2map build input.md \
  --split-mode heading \
  --summary-mode ai
```

### 実装

#### `_extract_section_info()` の分岐

```python
def _extract_section_info(self, section, lines):
    settings = self._resolve_settings(section)
    summary_mode = settings["summary_mode"]
    max_chars = settings["summary_max_chars"]

    section_lines = lines[section.start_line - 1 : section.end_line]
    section_text = "".join(section_lines)

    skip_first = self.HEADING_PATTERN.match(section_lines[0].rstrip()) is not None

    if summary_mode == "ai":
        section.summary = self._generate_ai_summary(section, section_text, max_chars)
    else:
        section.summary = self._extract_summary(
            section_lines, skip_first_line=skip_first, max_chars=max_chars
        )

    # ... リンク、キーワード、単語数は変更なし
```

#### プロンプト定義（モジュールレベル定数）

既存の `DEFAULT_AI_PROMPT_PARTS` と同じ4パート構造で定義する。

```python
DEFAULT_SUMMARY_PROMPT_PARTS: Dict[str, str] = {
    "role": (
        "あなたはドキュメント要約の専門家です。"
    ),
    "purpose": (
        "与えられたセクションの内容を簡潔に要約してください。"
    ),
    "format": (
        "要約文のみを返してください。説明文やマークダウン装飾は不要です。\n"
        "箇条書きや表形式ではなく、平文で回答してください。"
    ),
    "notes": (
        "- 要約は指定された文字数以内に収めること"
    ),
}
```

システムプロンプトの組み立ては `_build_ai_system_prompt()` と同じ形式を使う。

```python
def _build_summary_system_prompt(self) -> str:
    """AI サマリー生成用のシステムプロンプトを組み立てる"""
    parts = dict(DEFAULT_SUMMARY_PROMPT_PARTS)
    return (
        f"# 役割\n{parts['role']}\n\n"
        f"# 目的\n{parts['purpose']}\n\n"
        f"# 出力形式\n{parts['format']}\n\n"
        f"# 注意事項\n{parts['notes']}\n"
    )
```

#### `_generate_ai_summary()` の新規追加

`summary_max_chars` はセクションごとに変わる可能性があるため、ユーザープロンプトに含める。

```python
def _generate_ai_summary(
    self, section: Section, section_text: str, max_chars: int
) -> Optional[str]:
    """LLMを使用してセクションの要約を生成する

    Args:
        section: セクション
        section_text: セクションのテキスト
        max_chars: 要約の最大文字数

    Returns:
        AI生成の要約文字列、失敗時は None
    """
    self._ensure_llm_provider()

    system_text = self._build_summary_system_prompt()
    user_text = (
        f"以下のセクション「{section.title}」の内容を"
        f"{max_chars}文字以内で要約してください。\n\n"
        f"{section_text}"
    )

    try:
        summary = self._llm_provider.send_message(system_text, user_text)
        return self._sanitize_summary(summary)
    except Exception as exc:
        logger.warning(f"AI summary generation failed for '{section.title}': {exc}")
        return None
```

#### AI 要否判定の修正（`cmd_build()`）

`summary_mode` が `"ai"` の場合も LLM 初期化が必要。

```python
# cli.py の cmd_build() 内
needs_ai = args.split_mode == "ai" or args.summary_mode == "ai"
if section_overrides:
    needs_ai = needs_ai or any(
        o.get("split_mode") == "ai" or o.get("summary_mode") == "ai"
        for o in section_overrides
    )
```

#### `parse()` 内の AI 要否判定の修正

```python
# markdown_parser.py の parse() 内
has_non_heading_override = any(
    o.get("split_mode", self.split_mode) != "heading"
    for o in self._override_map.values()
    if not o.get("skip")
)
# summary_mode による AI 初期化は _extract_section_info() 内の
# _ensure_llm_provider() で遅延初期化されるため、ここでの変更は不要
```

#### CLI（`cli.py`）

```python
build_parser.add_argument(
    "--summary-mode",
    default="text",
    choices=["text", "ai"],
    help="サマリー生成モード（text: ルールベース, ai: LLM要約）",
)
```

```python
parser = MarkdownParser(
    # ... 既存引数 ...
    summary_max_chars=args.summary_max_chars,
    summary_mode=args.summary_mode,
)
```

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `md2map/parsers/markdown_parser.py` | `_extract_section_info()` に summary_mode 分岐追加、`_generate_ai_summary()` 新規追加、`_build_summary_system_prompt()` 新規追加 |
| `md2map/cli.py` | `--summary-mode` オプション追加、AI 要否判定に `summary_mode` 考慮を追加 |

---

## Step 3: テストの追加

### テストケース

#### 案A: `summary_max_chars` 関連

| # | ケース | 内容 |
|---|---|---|
| 1 | デフォルト100文字 | 従来通り100文字で切り詰められることを確認 |
| 2 | 上限値変更 | `summary_max_chars=200` で200文字まで取得できることを確認 |
| 3 | セクションオーバーライド | 特定セクションのみ文字数上限を変更できることを確認 |
| 4 | 短いテキスト | 上限値より短いテキストがそのまま返ることを確認 |
| 5 | 切り詰め位置 | `max_chars - 3` の位置で切り詰め + `...` が付くことを確認 |

#### サニタイズ関連

| # | ケース | 内容 |
|---|---|---|
| 6 | 改行の除去 | 改行を含むサマリーが1行に結合されることを確認 |
| 7 | None の透過 | `None` がそのまま `None` で返ることを確認 |
| 8 | 前後空白の除去 | 前後の空白が除去されることを確認 |

#### 案B: `summary_mode` 関連

| # | ケース | 内容 |
|---|---|---|
| 9 | デフォルト text | `summary_mode` 未指定時はルールベースで生成されることを確認 |
| 10 | AI モード | `summary_mode="ai"` でLLMが呼ばれることを確認（モック使用） |
| 11 | セクションオーバーライド | 特定セクションのみ AI 要約を使用できることを確認 |
| 12 | AI 失敗時 | LLM呼び出しが失敗した場合に `None` が返ることを確認 |
| 13 | text と ai の混在 | グローバル text + オーバーライド ai が正しく動作することを確認 |
| 14 | AI 初期化 | `summary_mode="ai"` 指定時に LLM provider が初期化されることを確認 |

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `tests/test_markdown_parser.py` | `summary_max_chars` 関連テスト追加、`summary_mode` 関連テスト追加 |

---

## Step 4: spec.md・README の更新

### spec.md

- `--summary-max-chars` オプションの仕様を追記
- `--summary-mode` オプションの仕様を追記
- セクションオーバーライドの設定キーに `summary_max_chars` と `summary_mode` を追記
- `_generate_ai_summary()` の処理フローを追記

### README.md / README_ja.md

- 主要オプション表に `--summary-max-chars` と `--summary-mode` を追記
- サマリー生成の使用例セクションを追加

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `spec.md` | 新オプションの仕様を追記 |
| `README.md` / `README_ja.md` | 新オプションの使用例を追記 |

---

## Step 5: サンプル出力の追加

v0.3.2 と同じ入力ファイルで v0.4.0 のサンプル出力を生成する。

### 生成コマンド

```bash
# 入力ファイルをコピー
cp docs/examples/v0.3.2/20260218サンプルコーディング規約.md docs/examples/v0.4.0/

# heading モード（デフォルトサマリー）
uv run md2map build docs/examples/v0.4.0/20260218サンプルコーディング規約.md \
  --out docs/examples/v0.4.0/output-heading --split-mode heading

# NLP モード
uv run md2map build docs/examples/v0.4.0/20260218サンプルコーディング規約.md \
  --out docs/examples/v0.4.0/output-nlp --split-mode nlp

# AI モード
uv run md2map build docs/examples/v0.4.0/20260218サンプルコーディング規約.md \
  --out docs/examples/v0.4.0/output-ai --split-mode ai

# headings コマンド
uv run md2map headings docs/examples/v0.4.0/20260218サンプルコーディング規約.md \
  > docs/examples/v0.4.0/headings.json
```

### docs/examples/README.md の更新

- ディレクトリ構成に `v0.4.0/` を追加
- 再生成コマンドに v0.4.0 セクションを追加

---

## Step 6: 更新履歴・バージョン情報の更新

### CHANGELOG.md / CHANGELOG_ja.md

v0.3.2 の前に v0.4.0 エントリを追加する。記載内容:

- **Added**: `--summary-max-chars` オプション（ルールベースサマリーの文字数上限をパラメータ化）
- **Added**: `--summary-mode` オプション（`text`/`ai` でサマリー生成方式を選択）
- **Added**: `--section-overrides` で `summary_max_chars` と `summary_mode` をセクション単位で指定可能
- **Sample output**: `docs/examples/v0.4.0/` にサンプル出力を追加

### versions/README.md

バージョン比較表に v0.4.0 列を追加:

| 項目 | 差分 |
|---|---|
| サマリー生成 | `--summary-max-chars` で文字数上限を変更可能、`--summary-mode ai` でLLM要約に対応 |
| セクション単位オーバーライド | + `summary_max_chars`, `summary_mode` をセクション単位で指定可能 |

---

## API

### Python API

```python
# 案A: 文字数上限の変更
parser = MarkdownParser(
    summary_max_chars=200,
)

# 案B: AI要約モード
parser = MarkdownParser(
    summary_mode="ai",
    llm_config=llm_config,
)

# 案A + 案B: セクション単位の使い分け
parser = MarkdownParser(
    summary_max_chars=200,          # デフォルトはルールベース200文字
    summary_mode="text",            # デフォルトはルールベース
    section_overrides=[
        {"start_line": 6, "summary_mode": "ai"},                         # このセクションはAI要約
        {"start_line": 52, "summary_mode": "text", "summary_max_chars": 50},  # このセクションは50文字
    ],
    llm_config=llm_config,
)
sections, warnings = parser.parse(file_path, max_depth=2)
```

### CLI

```bash
# 案A: 文字数上限を200に変更
md2map build input.md --summary-max-chars 200

# 案B: 全セクションAI要約
md2map build input.md --summary-mode ai

# 案A + 案B: セクション単位の使い分け
md2map build input.md \
  --summary-max-chars 200 \
  --section-overrides '[{"start_line": 6, "summary_mode": "ai"}]'
```

---

## 影響範囲

| 対象 | 影響 |
|---|---|
| `md2map/parsers/markdown_parser.py` | コンストラクタに `summary_max_chars`, `summary_mode` 追加、`_resolve_settings()` に追加、`_extract_section_info()` に分岐追加、`_extract_summary()` に `max_chars` 引数追加、`_generate_ai_summary()` 新規追加 |
| `md2map/cli.py` | `--summary-max-chars`, `--summary-mode` オプション追加、AI 要否判定の修正 |
| `md2map/models/section.py` | 変更なし（`summary` フィールドはそのまま使用） |
| `md2map/generators/` | 変更なし（`section.summary` をそのまま出力するため） |
| `md2map/llm/` | 変更なし（既存の `send_message()` インターフェースを使用） |
| `spec.md` | 新オプションの仕様を追記 |
| `README.md` / `README_ja.md` | 新オプションの使用例を追記 |
| `CHANGELOG.md` / `CHANGELOG_ja.md` | v0.4.0 の更新履歴を追加 |
| `versions/README.md` | バージョン比較表に v0.4.0 を追加 |
| `docs/examples/` | v0.4.0 のサンプル出力を追加 |
| 既存テスト | 影響なし（後方互換性維持） |

---

## 完了チェックリスト

### Step 0: 退避と準備

- [x] `versions/v0.3.2/` に既存実装を退避
- [x] `pyproject.toml` の version を `"0.4.0"` に更新

### Step 1: 案A — `summary_max_chars` のパラメータ化

- [x] コンストラクタに `summary_max_chars` 引数を追加
- [x] `_resolve_settings()` のデフォルト辞書に `summary_max_chars` を追加
- [x] `_extract_section_info()` で設定値を `_extract_summary()` に渡す
- [x] `_extract_summary()` に `max_chars` 引数を追加（固定100文字を置き換え）
- [x] `_sanitize_summary()` を新規実装
- [x] `_extract_summary()` の戻り値を `_sanitize_summary()` 経由にする
- [x] CLI に `--summary-max-chars` オプションを追加
- [x] 既存テストが全て通過

### Step 2: 案B — `--summary-mode ai` の追加

- [x] コンストラクタに `summary_mode` 引数を追加
- [x] `_resolve_settings()` のデフォルト辞書に `summary_mode` を追加
- [x] `_extract_section_info()` に `summary_mode` 分岐を追加
- [x] `DEFAULT_SUMMARY_PROMPT_PARTS` をモジュールレベル定数として定義
- [x] `_build_summary_system_prompt()` を新規実装
- [x] `_generate_ai_summary()` を新規実装（戻り値を `_sanitize_summary()` 経由にする）
- [x] CLI に `--summary-mode` オプションを追加
- [x] CLI の AI 要否判定に `summary_mode` を考慮
- [x] 既存テストが全て通過

### Step 3: テストの追加

- [x] `summary_max_chars` 関連テスト 5 件の追加
- [x] サニタイズ関連テスト 3 件の追加
- [x] `summary_mode` 関連テスト 6 件の追加
- [x] 全テスト通過（121 件）

### Step 4: ドキュメント更新

- [x] `spec.md` に新オプションの仕様を追記
- [x] `README.md` / `README_ja.md` に新オプションの使用例を追記

### Step 5: サンプル出力の追加

- [x] `docs/examples/v0.4.0/` に入力ファイルをコピー
- [x] heading / nlp / ai モードの出力を生成
- [x] `headings` コマンドの出力を生成
- [x] `docs/examples/README.md` に v0.4.0 のディレクトリ説明と再生成コマンドを追記

### Step 6: 更新履歴・バージョン情報の更新

- [x] `CHANGELOG.md` に v0.4.0 の更新履歴を追加
- [x] `CHANGELOG_ja.md` に v0.4.0 の更新履歴を追加
- [x] `versions/README.md` のバージョン比較表に v0.4.0 列を追加

### 最終確認

- [x] 既存テストが全て通過（後方互換性、全 121 件パス）
- [x] `spec.md` の更新内容が実装と整合している
