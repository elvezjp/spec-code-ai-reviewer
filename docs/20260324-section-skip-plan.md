# section_overrides に skip オプションを追加する 修正計画書

> **対応完了**: PR [#12](https://github.com/elvezjp/md2map/pull/12) / Issue [#11](https://github.com/elvezjp/md2map/issues/11) にて v0.3.2 として実装済み。全 107 テストパス、v0.3.1 との後方互換性確認済み。

## 概要

`section_overrides` に `"skip": true` オプションを追加し、指定セクション（およびその子セクション）を `parse()` の結果から完全に除外できるようにする。

## 背景

- AIレビュアー（[elvezjp/spec-code-ai-reviewer](https://github.com/elvezjp/spec-code-ai-reviewer)）側で「事前除外」機能を実装予定（[issue #68](https://github.com/elvezjp/spec-code-ai-reviewer/issues/68)）
- 不要なセクション（変更履歴、目次など）を事前除外することで、LLM 問い合わせ回数の削減・トークン節約が期待できる
- 対応 Issue: [#11](https://github.com/elvezjp/md2map/issues/11)

## 前提

- 現在の実装: md2map ルート（`md2map/`）、バージョン v0.3.1
- 今回の修正は v0.3.2 として実装する

---

## Step 0: v0.3.1 の退避と v0.3.2 の準備

### v0.3.1 の退避

現在の実装を `versions/v0.3.1` に退避する。

```
対象ファイル:
  md2map/         → versions/v0.3.1/md2map/
  tests/          → versions/v0.3.1/tests/
  main.py         → versions/v0.3.1/main.py
  pyproject.toml  → versions/v0.3.1/pyproject.toml
  uv.lock         → versions/v0.3.1/uv.lock
  spec.md         → versions/v0.3.1/spec.md
```

### v0.3.2 の準備

- `pyproject.toml` の `version` を `"0.3.2"` に更新
- `spec.md` にバージョン番号を反映

---

## Step 1: `_resolve_settings()` に `skip` キーを追加

### 設計

`_resolve_settings()` が返す設定辞書に `skip` キーを追加する。デフォルト値は `False`。

```python
def _resolve_settings(self, section):
    default = {
        "split_mode": self.split_mode,
        "split_threshold": self.split_threshold,
        "max_subsections": self.max_subsections,
        "ai_prompt_extra_notes": self.ai_prompt_extra_notes or "",
        "skip": False,  # 追加
    }
    override = self._override_map.get(section.start_line)
    if override is None:
        return default
    return {**default, **{k: v for k, v in override.items() if k != "start_line"}}
```

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `md2map/parsers/markdown_parser.py` | `_resolve_settings()` のデフォルト辞書に `"skip": False` を追加 |

---

## Step 2: `_filter_skipped_sections()` の実装と `parse()` への組み込み

### 設計

`_build_sections()` の後、`_refine_sections()` の前に skip 対象セクションをフィルタする。

これにより:
- skip セクションは AI/NLP サブスプリットの対象にならない（処理コスト削減）
- skip セクションは `_extract_section_info()` の対象にならない
- `_refine_sections()` や `_extract_section_info()` の変更は不要
- ジェネレーター（parts、INDEX.md、MAP.json）の変更も不要（`parse()` が返す `sections` リストに skip セクションが含まれないため）

### `_filter_skipped_sections()` の実装

```python
def _filter_skipped_sections(self, sections: List[Section]) -> List[Section]:
    """skip: true が指定されたセクション（とその子）を除外する"""
    # skip 対象の行範囲を収集
    skip_ranges: List[Tuple[int, int]] = []
    for section in sections:
        settings = self._resolve_settings(section)
        if settings.get("skip"):
            skip_ranges.append((section.start_line, section.end_line))

    if not skip_ranges:
        return sections

    # skip 範囲内のセクションを除外
    filtered = [
        s for s in sections
        if not any(
            r_start <= s.start_line and s.end_line <= r_end
            for r_start, r_end in skip_ranges
        )
    ]

    # 親子関係を再構築
    self._build_hierarchy(filtered)
    return filtered
```

### `parse()` への組み込み

```python
def parse(self, file_path, max_depth=3):
    # ... 既存処理 ...
    sections = self._build_sections(headings, lines, file_name)

    # ★ skip 対象セクションをフィルタ（_refine_sections() の前）
    sections = self._filter_skipped_sections(sections)

    # 以降は既存処理（skip 済みのリストが渡される）
    if needs_refinement:
        sections = self._refine_sections(sections, lines)
    for s in sections:
        self._extract_section_info(s, lines)
    return sections, warnings
```

### AI 要否判定の修正

`parse()` 内の AI 要否判定（L227-230）で、`skip: true` のオーバーライドが AI 初期化をトリガーしないよう修正する。

```python
# 修正前
has_non_heading_override = any(
    o.get("split_mode", self.split_mode) != "heading"
    for o in self._override_map.values()
)

# 修正後: skip: true のオーバーライドは除外
has_non_heading_override = any(
    o.get("split_mode", self.split_mode) != "heading"
    for o in self._override_map.values()
    if not o.get("skip")
)
```

### `extract_headings()` への影響

`extract_headings()` は skip の影響を受けない。見出し一覧はオーバーライド対象の `start_line` を特定するための機能であり、skip 対象セクションも表示されるべきである。

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `md2map/parsers/markdown_parser.py` | `_filter_skipped_sections()` の新規追加、`parse()` への組み込み、AI 要否判定の修正 |

---

## Step 3: テストの追加

### テストケース

| # | ケース | 内容 |
|---|---|---|
| 1 | 1 セクション skip | 指定セクションが結果に含まれないことを確認 |
| 2 | 子セクション含む skip | 親セクションを skip すると子も含めて除外されることを確認 |
| 3 | skip と split_mode 混在 | skip セクションは除外され、split_mode 指定セクションは正しく分割されることを確認 |
| 4 | 全セクション skip | 空リストが返ることを確認 |
| 5 | 存在しない start_line に skip | 無視される（既存動作と同じ） |
| 6 | `extract_headings()` への影響なし | skip 指定は `extract_headings()` の結果に影響しないことを確認 |
| 7 | skip: false（明示的） | `skip: false` を指定した場合、通常通り処理されることを確認 |
| 8 | skip セクションが AI 初期化をトリガーしない | `skip: true` + `split_mode: "ai"` のオーバーライドが LLM provider の初期化を引き起こさないことを確認 |

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `tests/test_markdown_parser.py` | `TestSectionOverrides` クラスに skip 関連テストを追加 |

---

## Step 4: spec.md・README の更新

### spec.md

- セクションオーバーライドの設定キーに `skip`（型: `bool`、デフォルト: `false`）を追記
- `_filter_skipped_sections()` による除外フローを処理フローに追記

### README.md / README_ja.md

- `section_overrides` の使用例に skip の例を追記

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `spec.md` | skip キーの仕様、処理フローを追記 |
| `README.md` / `README_ja.md` | skip の使用例を追記 |

---

## Step 5: サンプル出力の追加

v0.3.1 と同じ設定・同じ入力ファイルで v0.3.2 のサンプル出力を生成する。skip はこのバージョンで追加された機能だが、サンプル出力は従来モードとの互換性確認が目的のため、skip の例は含めない。

### 生成コマンド

```bash
# 入力ファイルをコピー
cp docs/examples/v0.3.1/20260218サンプルコーディング規約.md docs/examples/v0.3.2/

# heading モード
uv run md2map build docs/examples/v0.3.2/20260218サンプルコーディング規約.md \
  --out docs/examples/v0.3.2/output-heading --split-mode heading

# NLP モード
uv run md2map build docs/examples/v0.3.2/20260218サンプルコーディング規約.md \
  --out docs/examples/v0.3.2/output-nlp --split-mode nlp

# AI モード
uv run md2map build docs/examples/v0.3.2/20260218サンプルコーディング規約.md \
  --out docs/examples/v0.3.2/output-ai --split-mode ai

# headings コマンド
uv run md2map headings docs/examples/v0.3.2/20260218サンプルコーディング規約.md \
  > docs/examples/v0.3.2/headings.json
```

### docs/examples/README.md の更新

- ディレクトリ構成に `v0.3.2/` を追加
- 再生成コマンドに v0.3.2 セクションを追加

---

## Step 6: 更新履歴・バージョン情報の更新

### CHANGELOG.md / CHANGELOG_ja.md

v0.3.1 の前に v0.3.2 エントリを追加する。記載内容:

- **Added**: `section_overrides` に `skip` オプションを追加（セクションとその子の除外機能）
- **Changed**: `_resolve_settings()` に `skip` デフォルト追加、`parse()` にフィルタ処理を追加
- **Sample output**: `docs/examples/v0.3.2/` にサンプル出力を追加

### versions/README.md

バージョン比較表に v0.3.2 列を追加:

| 項目 | 差分 |
|---|---|
| セクション単位オーバーライド | + `skip: true` でセクション除外可 |

`v0.3.1 (現行)` → `v0.3.1`、`v0.3.2 (現行)` に変更。

### SECURITY.md / SECURITY_ja.md

サポートバージョンを `0.3.2` のみに変更済み。

---

## API

### Python API

```python
parser = MarkdownParser(
    split_mode="ai",
    section_overrides=[
        {"start_line": 6, "skip": True},                                    # このセクションを除外
        {"start_line": 79, "split_mode": "ai", "max_subsections": 10},      # 従来通り
    ],
)
sections, warnings = parser.parse(file_path, max_depth=2)
# → start_line=6 のセクション（とその子）は sections に含まれない
```

### CLI

```bash
md2map build input.md --section-overrides '[{"start_line": 6, "skip": true}]'
```

CLI 側の JSON パース・バリデーション処理に変更は不要。`skip` は `section_overrides` オブジェクト内のキーとして自然に渡される。

---

## 影響範囲

| 対象 | 影響 |
|---|---|
| `md2map/parsers/markdown_parser.py` | `_resolve_settings()` に `skip` デフォルト追加、`_filter_skipped_sections()` 新規追加、`parse()` にフィルタ呼び出し追加、AI 要否判定修正 |
| `md2map/cli.py` | 変更なし |
| `md2map/models/section.py` | 変更なし（`skip` はモデルではなく設定側の概念） |
| `md2map/generators/` | 変更なし（`parse()` の戻り値をそのまま使用するため） |
| `spec.md` | skip キーの仕様を追記 |
| `README.md` / `README_ja.md` | skip の使用例を追記 |
| `CHANGELOG.md` / `CHANGELOG_ja.md` | v0.3.2 の更新履歴を追加 |
| `versions/README.md` | バージョン比較表に v0.3.2 を追加 |
| `docs/examples/` | v0.3.2 のサンプル出力を追加、`README.md` に再生成コマンドを追記 |
| 既存テスト | 影響なし（後方互換性維持） |
| CLI の後方互換性 | `skip` を指定しなければ従来通り動作 |

---

## 完了チェックリスト

### Step 0: 退避と準備

- [x] `versions/v0.3.1/` に既存実装を退避
- [x] `pyproject.toml` の version を `"0.3.2"` に更新

### Step 1: `_resolve_settings()` の修正

- [x] `_resolve_settings()` のデフォルト辞書に `"skip": False` を追加
- [x] 既存テストが全て通過

### Step 2: `_filter_skipped_sections()` の実装

- [x] `_filter_skipped_sections()` の新規実装
- [x] `parse()` への組み込み（`_build_sections()` 後、`_refine_sections()` 前）
- [x] AI 要否判定の修正（skip セクションを除外）
- [x] 既存テストが全て通過

### Step 3: テストの追加

- [x] skip 関連テスト 8 件の追加
- [x] 全テスト通過（107 件）

### Step 4: ドキュメント更新

- [x] `spec.md` に skip キーの仕様・処理フローを追記
- [x] `README.md` / `README_ja.md` に skip の使用例を追記

### Step 5: サンプル出力の追加

v0.3.1 と同じ設定・同じ入力ファイルで v0.3.2 のサンプル出力を生成する（skip の例は不要）。

- [x] `docs/examples/v0.3.2/` に入力ファイルをコピー
- [x] heading / nlp / ai モードの出力を生成
- [x] `headings` コマンドの出力を生成
- [x] `docs/examples/README.md` に v0.3.2 のディレクトリ説明と再生成コマンドを追記

### Step 6: 更新履歴・バージョン情報の更新

- [x] `CHANGELOG.md` に v0.3.2 の更新履歴を追加
- [x] `CHANGELOG_ja.md` に v0.3.2 の更新履歴を追加
- [x] `versions/README.md` のバージョン比較表に v0.3.2 列を追加（v0.3.1 を `(現行)` から変更）

### 最終確認

- [x] 既存テストが全て通過（後方互換性、全 107 件パス）
- [x] `spec.md` の更新内容が実装と整合している
