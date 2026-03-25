# サブスプリットへの親セクション override 継承 修正計画書

## 概要

`--section-overrides` で親セクションに指定した設定が、AIサブスプリットで生成された子セクションに継承されない問題を修正する。

対応 Issue: [#17](https://github.com/elvezjp/md2map/issues/17)

## 背景

- `_resolve_settings()` はセクションの `start_line` をキーに `_override_map` を検索する
- サブスプリットは親セクションとは異なる `start_line` を持つため、親のオーバーライドが適用されない
- 例: `start_line: 6` に `summary_mode: ai` を指定しても、サブスプリット part-2（`start_line: 21`）以降はデフォルトの `text` にフォールバックする

## 前提

- 現在の実装: md2map ルート（`md2map/`）、バージョン v0.4.0
- 今回の修正ではバージョン番号の更新は行わない

---

## Step 1: `_resolve_settings()` に親セクションへのフォールバックを追加

### 現在の実装

```python
def _resolve_settings(self, section: Section) -> Dict[str, any]:
    default = {
        "split_mode": self.split_mode,
        "split_threshold": self.split_threshold,
        "max_subsections": self.max_subsections,
        "ai_prompt_extra_notes": self._ai_prompt_extra_notes or "",
        "skip": False,
        "summary_max_chars": self.summary_max_chars,
        "summary_mode": self.summary_mode,
    }
    override = self._override_map.get(section.start_line)
    if override is None:
        return default
    return {**default, **{k: v for k, v in override.items() if k != "start_line"}}
```

### 修正後の実装

```python
def _resolve_settings(self, section: Section) -> Dict[str, any]:
    default = {
        "split_mode": self.split_mode,
        "split_threshold": self.split_threshold,
        "max_subsections": self.max_subsections,
        "ai_prompt_extra_notes": self._ai_prompt_extra_notes or "",
        "skip": False,
        "summary_max_chars": self.summary_max_chars,
        "summary_mode": self.summary_mode,
    }
    override = self._override_map.get(section.start_line)
    # サブスプリットの場合、親セクションのオーバーライドを継承する
    if override is None and section.is_subsplit and section.parent is not None:
        override = self._override_map.get(section.parent.start_line)
    if override is None:
        return default
    return {**default, **{k: v for k, v in override.items() if k != "start_line"}}
```

### 設計判断

- `section.is_subsplit` と `section.parent is not None` の両方をチェックすることで、通常の子セクション（見出しベースの階層）には影響しない
- サブスプリット自身に直接オーバーライドが指定されている場合は、そちらを優先する（既存の動作を維持）
- 親セクションの `split_mode` や `split_threshold` などの分割関連設定はサブスプリットに影響しない（サブスプリットは再分割されないため）。影響するのは `summary_mode`、`summary_max_chars` 等の情報抽出系設定

### 処理順序の確認

`_extract_section_info()` が `_resolve_settings()` を呼ぶ時点での状態:

1. `_refine_sections()` でサブスプリットが生成される
2. `_refine_sections()` 末尾の `_build_hierarchy(refined)` で親子関係が構築される
3. `parse()` に戻り、`_extract_section_info()` が全セクションに対して呼ばれる

→ `_extract_section_info()` 実行時には `section.parent` が設定済みであり、親セクションへのフォールバックが正しく動作する。

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `md2map/parsers/markdown_parser.py` | `_resolve_settings()` にサブスプリットの親セクションフォールバックを追加（2行追加） |

---

## Step 2: テストの追加

### テストケース

| # | ケース | 内容 |
|---|---|---|
| 1 | 親の override がサブスプリットに継承 | 親セクションに `summary_mode: ai` を指定し、サブスプリット全体に適用されることを確認 |
| 2 | サブスプリット自身の override が優先 | サブスプリットの `start_line` に直接 override を指定した場合、親の override より優先されることを確認 |
| 3 | 通常の子セクションには影響なし | 見出しベースの子セクション（`is_subsplit=False`）は、親の override を継承しないことを確認 |
| 4 | 親に override なし | 親セクションにも override がない場合、デフォルト設定が適用されることを確認 |
| 5 | `summary_max_chars` の継承 | 親セクションの `summary_max_chars` override がサブスプリットにも適用されることを確認 |

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `tests/test_markdown_parser.py` | サブスプリット override 継承のテスト 5 件を追加 |

---

## Step 3: spec.md の更新

### 修正内容

セクションオーバーライドの仕様説明に、サブスプリットへの継承ルールを追記する。

```
セクションオーバーライドの継承:
- サブスプリット（再分割で生成されたセクション）は、自身に直接 override が指定されていない場合、
  親セクションの override を継承する
- 通常の子セクション（見出しベースの階層）は親の override を継承しない
```

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `spec.md` | セクションオーバーライドの仕様にサブスプリット継承ルールを追記 |

---

## 影響範囲

| 対象 | 影響 |
|---|---|
| `md2map/parsers/markdown_parser.py` | `_resolve_settings()` に 2 行追加 |
| `md2map/models/section.py` | 変更なし（`parent`, `is_subsplit` フィールドは既存） |
| `md2map/cli.py` | 変更なし |
| `md2map/generators/` | 変更なし |
| `md2map/llm/` | 変更なし |
| `spec.md` | サブスプリット継承ルールを追記 |
| 既存テスト | 影響なし（後方互換性維持: override 未指定時の動作は不変） |

---

## 完了チェックリスト

### Step 1: `_resolve_settings()` の修正

- [x] サブスプリットの親セクションフォールバックを追加
- [x] 既存テストが全て通過

### Step 2: テストの追加

- [x] サブスプリット override 継承テスト 5 件の追加
- [x] 全テスト通過（126 件）

### Step 3: spec.md の更新

- [x] セクションオーバーライドの仕様にサブスプリット継承ルールを追記

### 最終確認

- [x] 既存テストが全て通過（後方互換性、全 126 件パス）
- [x] `spec.md` の更新内容が実装と整合している
- [x] サンプルファイルで動作確認（`--section-overrides` 指定のサブスプリットに親の設定が継承される）
