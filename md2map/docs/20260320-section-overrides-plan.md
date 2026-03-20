# セクション単位の分割設定オーバーライド機能 修正計画書

> **対応完了**: PR [#10](https://github.com/elvezjp/md2map/pull/10) / Issue [#9](https://github.com/elvezjp/md2map/issues/9) にて v0.3.1 として実装済み。全 99 テストパス、v0.3 との後方互換性確認済み。

## 概要

セクション単位で分割設定をオーバーライドする機能を追加する。
デフォルトの分割設定に対して、特定セクションの設定（split_mode, max_subsections 等）を個別に上書きできるようにする。

セクションの識別には `start_line`（見出しの開始行番号）を使用し、同名見出しがある場合でも一意に識別可能とする。

## 背景

- 呼び出し元（AI レビュアー）で、特定セクションに異なる分割設定を適用したいユースケースが発生
- md2map としては汎用的な「セクション単位の設定オーバーライド」として実装し、呼び出し元の用途に依存しない設計とする

## 前提

- 現在の実装: md2map ルート（`md2map/`）、バージョン v0.3.0
- 今回の修正は v0.3.1 として実装する

---

## Step 0: v0.3.0 の退避と v0.3.1 の準備

### v0.3.0 の退避

現在の実装を `versions/v0.3.0` に退避する。

```
対象ファイル（v0.2.0 と同様の構成）:
  md2map/         → versions/v0.3.0/md2map/
  tests/          → versions/v0.3.0/tests/
  main.py         → versions/v0.3.0/main.py
  pyproject.toml  → versions/v0.3.0/pyproject.toml
  uv.lock         → versions/v0.3.0/uv.lock
  spec.md         → versions/v0.3.0/spec.md
```

### v0.3.1 の準備

- `pyproject.toml` の `version` を `"0.3.1"` に更新
- `spec.md` にバージョン番号を反映

---

## Step 1: 見出し一覧取得機能の追加

分割実行前に見出し一覧だけを軽量に取得する公開メソッドを追加する。
呼び出し元がセクション一覧を表示し、オーバーライド対象を選択するために使用する。

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `md2map/parsers/markdown_parser.py` | `extract_headings(content, max_depth)` 公開メソッドを追加 |
| `md2map/cli.py` | `headings` サブコマンドを追加 |
| `tests/` | 見出し一覧取得のテストを追加 |

### 設計方針: 既存ロジックの再利用による整合性保証

`extract_headings()` は新規ロジックを書かず、既存の `_extract_headings()` + `_build_sections()` を内部で呼び出し、結果を軽量な形式に変換する。

これにより：
- **実装の重複なし**: 見出し解析・セクション構築のロジックは既存メソッドをそのまま使用
- **行番号の整合性保証**: `build` コマンドと同じコードパスを通るため、`start_line` が必ず一致。後から `section_overrides` のキーとして使用しても安全
- **省略されるのはサブスプリットとファイル生成のみ**: `_refine_sections()` と `_extract_section_info()` とファイル I/O をスキップするため高速

### 実装イメージ

```python
def extract_headings(self, content: str, max_depth: int = 6) -> list[dict]:
    """見出し一覧を軽量に取得する（ファイル生成・サブスプリットなし）"""
    lines = content.splitlines()
    # 既存ロジックをそのまま使用（重複なし・行番号の整合性保証）
    headings = self._extract_headings(lines, max_depth)
    sections = self._build_sections(headings, lines, "")
    # Section オブジェクトから必要なフィールドだけ抽出
    return [
        {
            "title": s.title,
            "level": s.level,
            "start_line": s.start_line,
            "end_line": s.end_line,
            "estimated_chars": sum(
                len(line) for line in lines[s.start_line - 1 : s.end_line]
            ),
        }
        for s in sections
    ]
```

### 入出力

```
入力:  markdown テキスト, max_depth（省略時: 6）
出力:  [{ title, level, start_line, end_line, estimated_chars }]
```

- `start_line`, `end_line` は `_build_sections()` が算出した値をそのまま使用
- `estimated_chars` はセクション内の文字数（見出し行を含む）
- LLM 不要、高速処理

### CLI

```
md2map headings input.md [--max-depth 2]
```

出力は JSON 形式で標準出力に出力する。

### Python API

```python
parser = MarkdownParser()
headings = parser.extract_headings(content, max_depth=2)
# → [{"title": "API仕様", "level": 2, "start_line": 79, "end_line": 110, "estimated_chars": 1084}, ...]
```

---

## Step 2: セクション単位の分割設定オーバーライド

### 設計

#### オーバーライド構造

```python
section_overrides = [
    {
        "start_line": 79,
        "split_mode": "ai",
        "max_subsections": 10,
        "split_threshold": 300,
        "ai_prompt_extra_notes": "項番単位で分割する"
    },
    {
        "start_line": 111,
        "split_mode": "heading"
        // 指定しないフィールドはコンストラクタ引数の値を継承
    }
]
```

- `section_overrides` はオーバーライドのリスト。`start_line` で対象セクションを識別
- overrides で省略されたフィールドはコンストラクタ引数の値（デフォルト設定）を継承
- `default` ブロックは持たない。デフォルト設定はコンストラクタ引数（`split_mode`, `split_threshold`, `max_subsections`, `ai_prompt_extra_notes`）がそのまま使用される

#### 設定の優先順位

```
セクション単位の override > コンストラクタ引数（= デフォルト設定）
```

- コンストラクタ引数が全セクションのデフォルトとなる（既存の呼び出し方と完全互換）
- `section_overrides` は特定セクションのみ上書きする追加指定
- これにより、既存の呼び出し元（CLI、ライブラリ）は `section_overrides` を渡さなければ従来通り動作する

#### セクション識別

- `start_line`（見出しの開始行番号、1-based）で一意に識別
- `extract_headings()` の結果から取得した `start_line` をそのまま使用
- 同名見出しがある場合でも行番号で区別可能

#### 設定のマージルール

```python
def _resolve_settings(self, section):
    """セクションに適用する設定を解決する"""
    # デフォルト: コンストラクタ引数の値
    default = {
        "split_mode": self.split_mode,
        "split_threshold": self.split_threshold,
        "max_subsections": self.max_subsections,
        "ai_prompt_extra_notes": self.ai_prompt_extra_notes or "",
    }
    override = self._override_map.get(section.start_line)
    if override is None:
        return default
    # override のフィールドで default を上書き（未指定フィールドはコンストラクタ引数を維持）
    return {**default, **{k: v for k, v in override.items() if k != "start_line"}}
```

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `md2map/parsers/markdown_parser.py` | `section_overrides` パラメータを受け取り、`_refine_sections()` 内でセクションごとに設定を切り替え |
| `md2map/cli.py` | `--section-overrides` オプションを追加（JSON ファイルパスまたは JSON 文字列） |
| `tests/` | セクション単位オーバーライドのテストを追加 |

### MarkdownParser の変更

```python
class MarkdownParser:
    def __init__(
        self,
        split_mode="heading",
        split_threshold=500,
        max_subsections=5,
        ai_prompt_extra_notes="",
        llm_config=None,
        section_overrides=None,  # 追加: list[dict] | None
    ):
        # 既存フィールド（= 全セクションのデフォルト設定）
        self.split_mode = split_mode
        self.split_threshold = split_threshold
        self.max_subsections = max_subsections
        self.ai_prompt_extra_notes = ai_prompt_extra_notes
        self.llm_config = llm_config
        # 新規: オーバーライドマップ（start_line → 設定 dict）
        self._override_map = {}
        if section_overrides:
            for o in section_overrides:
                self._override_map[o["start_line"]] = o

        # 遅延初期化: LLM provider / NLP tokenizer はオーバーライドで
        # 必要になる可能性があるため、コンストラクタでは初期化しない場合がある。
        # → _ensure_llm_provider(), _ensure_nlp_tokenizer() で必要時に初期化
```

### LLM provider / NLP tokenizer の遅延初期化

現在の実装ではコンストラクタで `split_mode` に応じて LLM provider や sudachipy tokenizer を初期化しているが、オーバーライドにより特定セクションだけ異なるモードを使用するケースが発生する。

例: デフォルトは `split_mode="heading"` だが、特定セクションのみ `split_mode="ai"` にオーバーライド → コンストラクタ時点では LLM provider が未初期化。

**対策: 遅延初期化パターン**

```python
def _ensure_llm_provider(self):
    """LLM provider が未初期化なら初期化する（遅延初期化）"""
    if self._llm_provider is not None:
        return
    if self.llm_config:
        self._llm_provider = get_llm_provider(self.llm_config)
    else:
        config = build_llm_config_from_env()
        self._llm_provider = get_llm_provider(config)

def _ensure_nlp_tokenizer(self):
    """NLP tokenizer が未初期化なら初期化する（遅延初期化）"""
    if self._tokenizer is not None:
        return
    try:
        from sudachipy import Dictionary
        self._tokenizer = Dictionary().create()
    except ImportError:
        raise RuntimeError("sudachipy が必要です: pip install sudachipy sudachidict-core")
```

- コンストラクタでの初期化ロジックは維持する（デフォルトの `split_mode` に応じて初期化）
- `_refine_sections()` 内でオーバーライドにより異なるモードが必要になった場合、上記メソッドを呼び出して遅延初期化する
- 既にコンストラクタで初期化済みなら何もしない（冪等）

### _refine_sections() の変更

```python
def _refine_sections(self, sections, lines):
    for section in sections:
        # セクションごとに設定を解決
        settings = self._resolve_settings(section)
        split_mode = settings["split_mode"]
        threshold = settings["split_threshold"]
        max_subs = settings["max_subsections"]
        extra_notes = settings.get("ai_prompt_extra_notes", "")

        # 以降は既存ロジック（settings の値を使用）
        own_start, own_end = self._get_own_content_range(section, sections)
        total_count = self._count_words(own_text)

        if split_mode == "heading":
            continue  # 見出しモードではサブスプリットしない

        if total_count >= threshold:
            target_parts = min(max_subs, max(2, ceil(total_count / threshold)))
            if split_mode == "nlp":
                self._ensure_nlp_tokenizer()  # 遅延初期化
                # NLP 分割（既存ロジック）
            elif split_mode == "ai":
                self._ensure_llm_provider()  # 遅延初期化
                # AI 分割（既存ロジック、extra_notes を使用）
```

### CLI の変更

```
md2map build input.md \
  --split-mode ai --max-subsections 5 \
  --section-overrides overrides.json
```

- `--section-overrides`: JSON ファイルパスまたは JSON 文字列
- `--split-mode` 等の既存オプションが全セクションのデフォルト設定となる
- `--section-overrides` は特定セクションのみ上書きする追加指定
- `--section-overrides` を指定しない場合、既存オプションがそのまま使用される（後方互換性維持）

### API（Python ライブラリとしての使用）

バックエンド等から直接 `MarkdownParser` を使用する場合：

```python
parser = MarkdownParser(
    split_mode="ai",              # デフォルト設定（全セクションに適用）
    max_subsections=5,
    section_overrides=[           # 特定セクションのみ上書き
        {"start_line": 79, "max_subsections": 10},
        {"start_line": 111, "split_mode": "heading"},
    ]
)
sections, warnings = parser.parse(file_path, max_depth=2)
```

- コンストラクタ引数 `split_mode="ai"`, `max_subsections=5` が全セクションのデフォルト
- start_line=79 のセクション: `max_subsections` のみ 10 に上書き（`split_mode` は "ai" を継承）
- start_line=111 のセクション: `split_mode` を "heading" に上書き（サブスプリットなし）

---

## テスト計画

### Step 1: 見出し一覧取得

| テストケース | 内容 |
|---|---|
| 基本取得 | H1〜H4 の見出しを含む MD から正しく一覧取得 |
| max_depth 制限 | max_depth=2 で H3 以下が除外される |
| コードブロック内 | コードブロック内の `#` が見出しとして誤検出されない |
| 空ファイル | 見出しなしで空リストが返る |
| end_line 計算 | 最後のセクションの end_line が文書末尾になる |
| estimated_chars | 文字数が正しく算出される |
| build との整合性 | `extract_headings()` の `start_line` が `build` 実行時のセクションの `start_line` と一致する |

### Step 2: セクション単位オーバーライド

| テストケース | 内容 |
|---|---|
| override なし | 従来と同じ動作（後方互換性） |
| 単一 override | 指定セクションのみ異なる設定で分割される |
| 複数 override | 複数セクションにそれぞれ異なる設定が適用される |
| コンストラクタ引数継承 | override で省略したフィールドがコンストラクタ引数から継承される |
| 存在しない start_line | 警告を出さず、コンストラクタ引数の設定で処理される |
| split_mode 混在 | あるセクションは AI、別のセクションは heading で分割 |
| 遅延初期化（AI） | デフォルト heading だが override で AI 指定時、LLM provider が遅延初期化される |
| 遅延初期化（NLP） | デフォルト heading だが override で NLP 指定時、tokenizer が遅延初期化される |
| JSON ファイル読み込み | CLI で JSON ファイルパスを指定して正しく読み込める |
| JSON 文字列 | CLI で JSON 文字列を直接指定して正しく解析される |

---

## spec.md の更新

以下のセクションを更新する。

### 2.3.1 コマンド構文

`headings` サブコマンドの構文を追加:

```
md2map headings <input_file> [--max-depth <N>]
```

### 2.3.2 引数・オプション

以下を追加:

| 引数/オプション | 必須 | デフォルト | 説明 |
|---|---|---|---|
| `--section-overrides <JSON>` | 任意 | なし | セクション単位の分割設定オーバーライド（JSON ファイルパスまたは JSON 文字列） |

### 3.1 全体フロー

見出し一覧取得（`headings` コマンド）のフローを追記。

### 3.3 セクション再分割フェーズ

セクション単位のオーバーライドによる設定解決の手順を追記:
- `_resolve_settings()` による設定マージ
- セクションごとに `split_mode`, `split_threshold`, `max_subsections`, `ai_prompt_extra_notes` が異なりうる旨

### LLM provider / NLP tokenizer の遅延初期化

AI モード・NLP モードの前提条件に遅延初期化の説明を追記:
- コンストラクタ時点で不要なプロバイダー/トークナイザーは初期化しない
- オーバーライドにより必要になった時点で初期化する

---

## 影響範囲

| 対象 | 影響 |
|---|---|
| `markdown_parser.py` | `extract_headings()` 追加、`_refine_sections()` にオーバーライド分岐追加、遅延初期化メソッド追加 |
| `cli.py` | `headings` サブコマンド追加、`--section-overrides` オプション追加 |
| `section.py` | 変更なし（セクションモデルへのフィールド追加不要） |
| `map_generator.py` | 変更なし |
| `spec.md` | CLI 仕様・処理フローにセクションオーバーライドと見出し一覧取得を追記 |
| `README.md` / `README_ja.md` | `headings` コマンド、`--section-overrides` オプションの使用例を追記 |
| 既存テスト | 影響なし（後方互換性維持） |
| CLI の後方互換性 | `--section-overrides` を指定しなければ従来通り動作 |

---

## 完了チェックリスト

### Step 0: 退避と準備

- [x] `versions/v0.3.0/` に既存実装を退避
- [x] `pyproject.toml` の version を `"0.3.1"` に更新

### Step 1: 見出し一覧取得機能

- [x] `MarkdownParser.extract_headings()` の実装
- [x] CLI `headings` サブコマンドの実装
- [x] テスト追加・全テスト通過（7 件追加）
- [x] `spec.md` に `headings` コマンドの仕様を追記
- [x] `README.md` / `README_ja.md` に `headings` コマンドの使用例を追記

### Step 2: セクション単位オーバーライド

- [x] `section_overrides` パラメータの追加（`MarkdownParser.__init__`）
- [x] `_resolve_settings()` の実装
- [x] `_ensure_llm_provider()` / `_ensure_nlp_tokenizer()` 遅延初期化の実装
- [x] `_refine_sections()` のオーバーライド対応
- [x] CLI `--section-overrides` オプションの実装
- [x] テスト追加・全テスト通過（9 件追加）
- [x] `spec.md` にセクションオーバーライドの仕様を追記
- [x] `README.md` / `README_ja.md` に `--section-overrides` オプションの使用例を追記

### 最終確認

- [x] 既存テストが全て通過（後方互換性、全 99 件パス）
- [x] `spec.md` の更新内容が実装と整合している
- [x] v0.3 との diff で heading / nlp / ai 全モード差分ゼロを確認
