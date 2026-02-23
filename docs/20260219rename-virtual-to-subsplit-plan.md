# 修正計画: virtual 表現を subsplit にリネーム + note フィールド導入 + タイトルフォーマット統一

## 1. 背景と目的

### 1.1 課題

現在、AI/NLP モードで再分割されたセクションを表すために `is_virtual` / `virtual_title` / `split_reason` という用語を使用しているが、以下の問題がある：

1. **`virtual`（仮想）の意味が曖昧**: 「何が仮想なのか」が名前から伝わらない。元のMarkdownに見出しが存在せず、ツールが分析してさらに分割したセクションであることが直感的に理解しにくい
2. **見出しベースのサブセクションとの区別がつかない**: `subpart` のような名前だと、元から存在する H3 子セクションと AI 分割で生成したセクションの区別がつかない
3. **`split_reason` の情報不足**: 現在の値（例: `ai boundary split`）は分割方法のみを示し、「どのセクションのどの範囲を分割したか」という具体的な由来情報が欠落している
4. **INDEX.md / MAP.json から親子関係がわからない**: 再分割された子パートが、親セクションのどの部分に対応するかを把握するには行番号を目視で比較する必要がある
5. **AI モードの subsplit タイトルに親の情報がない**: NLP モードは `親タイトル (part N/M)` 形式で親との関係がわかるが、AI モードは独自タイトルのみで親との関係が読み取りにくい
6. **NLP モードのナンバリング `(part N/M)` がパス変換で崩れる**: `/` が特殊文字として削除され、`(part 2/3)` がファイル名で `_(part_23)` になり意味不明になる

### 1.2 決定事項

以下の議論を経て、次の方針を決定した：

**フィールド名の変更:**

| 項目 | 変更前 | 変更後 | 理由 |
|------|--------|--------|------|
| フラグ | `is_virtual` | `is_subsplit` | 「さらに分割（split）された」ことを示し、通常の見出し子セクションと区別できる |
| タイトル | `virtual_title` | `subsplit_title` | `is_subsplit` と対になる命名 |
| 備考 | `split_reason` | `note` | 汎用的な備考欄として、分割の由来だけでなく将来的な付記にも対応。`is_subsplit` で種別判定は十分なため、専用フィールド名は不要 |
| ラベル | `[Virtual]` | `[SubSplit]` | INDEX.md の構造ツリーおよびセクション詳細での表示 |

**subsplit_title のフォーマット統一:**

| モード | 変更前 | 変更後 |
|--------|--------|--------|
| AI | `ファイルの概要と参考情報` | `コーディング規約一覧: ファイルの概要と参考情報` |
| NLP | `命名規則クラス（1） (part 1/3)` | `命名規則クラス（1）: part-1` |

両モードとも **`親タイトル: サブタイトル`** 形式に統一する。

- AI モード: LLM が返したタイトルの前に親セクション名を付与
- NLP モード: `(part N/M)` を `part-N` に変更（`/` を排除しパス安全にする）。総数の情報は `note` フィールドに含まれるためタイトルには不要

### 1.3 `note` フィールドの値フォーマット

`note` には分割の由来を具体的に記述する：

```
Subsplit of {親セクションID} (L{開始行}–L{終了行}, {分割方法})
```

例：
- `"Subsplit of MD2 (L10–L20, ai boundary split)"`
- `"Subsplit of MD5 (L70–L88, nlp threshold split)"`
- `"Subsplit of MD2 (L21–L43, ai threshold split)"`

これにより、`split_reason` では得られなかった以下の情報が追加される：
- **親セクションID**: どのセクションを再分割したか
- **行範囲**: 元ファイルのどの範囲に対応するか

---

## 2. 変更対象ファイル

### 2.1 ソースコード

| ファイル | 変更内容 |
|---------|---------|
| `md2map/models/section.py` | フィールド名の変更: `is_virtual` → `is_subsplit`, `virtual_title` → `subsplit_title`, `split_reason` → `note`。`display_name()` メソッドの条件式も更新 |
| `md2map/parsers/markdown_parser.py` | セクション生成時の属性名変更。`note` の値を新フォーマット（親ID・行範囲を含む）で生成。subsplit_title の生成ロジックを変更（AI: 親タイトル付与、NLP: ナンバリング形式変更） |
| `md2map/generators/map_generator.py` | MAP.json 出力のフィールド名変更: `is_virtual` → `is_subsplit`, `split_reason` → `note`, `virtual_title` → `subsplit_title` |
| `md2map/generators/parts_generator.py` | parts ファイルヘッダのフィールド名変更 |
| `md2map/generators/index_generator.py` | `[Virtual]` → `[SubSplit]` ラベル変更、`split_reason` → `note` の表示変更 |

### 2.2 テスト

| ファイル | 変更内容 |
|---------|---------|
| `tests/test_llm.py` | `is_virtual` → `is_subsplit`, `virtual_title` → `subsplit_title`, `split_reason` のアサーションを `note` に変更。値のフォーマットも新形式に合わせる。subsplit_title のアサーションを新フォーマットに合わせる |

### 2.3 仕様書

| ファイル | 変更内容 |
|---------|---------|
| `spec.md` | 2.2.2 節（parts ヘッダ）、2.2.3 節（MAP.json フィールド）、2.3.6 節（分割モード）、3.3 節（再分割フェーズ）、3.5 節（索引生成）、5.3 節（NLP 命名）、6.5 節（AI 命名）等の用語・フォーマットを更新 |

### 2.4 変更不要（過去の計画書）

以下のファイルは過去の計画・提案の記録であり、当時の用語のまま保持する：

- `docs/20260218enhancement_plan.md`
- `docs/20260218semantic_mapping_proposal.md`

---

## 3. 変更詳細

### 3.1 Section モデル (`md2map/models/section.py`)

**変更前:**
```python
is_virtual: bool = False
split_reason: str = ""
virtual_title: str = ""
```

**変更後:**
```python
is_subsplit: bool = False
note: str = ""
subsplit_title: str = ""
```

**`display_name()` メソッド:**

変更前:
```python
if self.is_virtual and self.virtual_title:
    return self.virtual_title
```

変更後:
```python
if self.is_subsplit and self.subsplit_title:
    return self.subsplit_title
```

### 3.2 パーサー (`md2map/parsers/markdown_parser.py`)

セクション生成箇所で以下を変更する：
- 属性名を新名称に変更
- `note` に親セクションの情報を含める
- `subsplit_title` を `親タイトル: サブタイトル` 形式で生成

#### 3.2.1 AI モードの subsplit_title 生成

**変更前:**
```python
is_virtual=True,
split_reason=f"{self.split_mode} boundary split",
virtual_title=display_title,
```

**変更後:**
```python
is_subsplit=True,
note=f"Subsplit of {parent_section.id} (L{start_line}–L{end_line}, {self.split_mode} boundary split)",
subsplit_title=f"{parent_section.title}: {display_title}",
```

AI モードの threshold split も同様：

**変更前:**
```python
is_virtual=True,
split_reason=f"{self.split_mode} threshold split",
virtual_title=virtual_title,
```

**変更後:**
```python
is_subsplit=True,
note=f"Subsplit of {parent_section.id} (L{start_line}–L{end_line}, {self.split_mode} threshold split)",
subsplit_title=f"{parent_section.title}: {virtual_title}",
```

#### 3.2.2 NLP モードの subsplit_title 生成

**変更前:**
```python
virtual_title = f"{base_title} (part {i}/{total})"
```

**変更後:**
```python
subsplit_title = f"{base_title}: part-{i}"
```

- `(part N/M)` → `part-N` に変更
- `/` を排除し、パス変換でも読みやすいファイル名を生成可能にする
- 総数 `M` は `note` フィールドに含まれるため省略

> **注意**: `note` 生成時に `parent_section.id` と行範囲を参照する必要がある。パーサーの該当箇所でこれらの値がスコープ内にあるか確認し、必要に応じて引数として渡す。

### 3.3 MAP.json 生成 (`md2map/generators/map_generator.py`)

**変更前:**
```python
if section.is_virtual:
    entry["is_virtual"] = True
    if section.split_reason:
        entry["split_reason"] = section.split_reason
    if section.virtual_title:
        entry["virtual_title"] = section.virtual_title
```

**変更後:**
```python
if section.is_subsplit:
    entry["is_subsplit"] = True
    if section.note:
        entry["note"] = section.note
    if section.subsplit_title:
        entry["subsplit_title"] = section.subsplit_title
```

### 3.4 parts ファイル生成 (`md2map/generators/parts_generator.py`)

**変更前:**
```python
if section.is_virtual:
    virtual_lines += "is_virtual: true\n"
    if section.split_reason:
        virtual_lines += f"split_reason: {section.split_reason}\n"
    if section.virtual_title:
        virtual_lines += f"virtual_title: {section.virtual_title}\n"
```

**変更後:**
```python
if section.is_subsplit:
    subsplit_lines += "is_subsplit: true\n"
    if section.note:
        subsplit_lines += f"note: {section.note}\n"
    if section.subsplit_title:
        subsplit_lines += f"subsplit_title: {section.subsplit_title}\n"
```

### 3.5 INDEX.md 生成 (`md2map/generators/index_generator.py`)

**構造ツリーのラベル:**

変更前:
```python
virtual_label = "[Virtual] " if section.is_virtual else ""
```

変更後:
```python
subsplit_label = "[SubSplit] " if section.is_subsplit else ""
```

**セクション詳細:**

変更前:
```python
if section.is_virtual:
    lines.append(f"- split_reason: {section.split_reason or 'n/a'}\n")
```

変更後:
```python
if section.is_subsplit:
    lines.append(f"- note: {section.note or 'n/a'}\n")
```

### 3.6 テスト (`tests/test_llm.py`)

全テストケースで以下を更新：
- `s.is_virtual` → `s.is_subsplit`
- `s.virtual_title` → `s.subsplit_title`
- `s.split_reason` → `s.note`
- `note` の値アサーションは新フォーマットに合わせる（親IDと行範囲を含む文字列）
- NLP テストの subsplit_title アサーションを `part-N` 形式に合わせる

### 3.7 仕様書 (`spec.md`)

以下の箇所を更新：

| 節 | 変更内容 |
|----|---------|
| 1.2 設計思想 | 「仮想見出し」の説明を「サブスプリット（subsplit）」に更新 |
| 2.2.2 parts ヘッダ | `is_virtual` → `is_subsplit`, `split_reason` → `note`, `virtual_title` → `subsplit_title` の説明を更新 |
| 2.2.3 MAP.json フィールド | 同上 |
| 2.3.6 分割モード | 「仮想見出し」の表現を更新。subsplit_title のフォーマット仕様を追記 |
| 3.3 再分割フェーズ | 仮想セクション → subsplit セクション |
| 3.5 索引生成 | `[Virtual]` → `[SubSplit]` |
| 5.3 NLP の命名 | `(part N/M)` → `part-N` 形式に更新。`親タイトル: part-N` フォーマットを明記 |
| 6.5 AI の命名 | `親タイトル: AIタイトル` フォーマットを明記 |

---

## 4. 出力例の変更

### 4.1 AI モード MAP.json

**変更前:**
```json
{
  "id": "MD4",
  "section": "命名規則に関するガイドライン",
  "level": 3,
  "path": "設計書: ... > コーディング規約一覧 > コーディング規約一覧: 命名規則に関するガイドライン",
  "original_start_line": 10,
  "original_end_line": 20,
  "is_virtual": true,
  "split_reason": "ai boundary split",
  "virtual_title": "命名規則に関するガイドライン"
}
```

**変更後:**
```json
{
  "id": "MD4",
  "section": "コーディング規約一覧: 命名規則に関するガイドライン",
  "level": 3,
  "path": "設計書: ... > コーディング規約一覧 > コーディング規約一覧: 命名規則に関するガイドライン",
  "original_start_line": 10,
  "original_end_line": 20,
  "is_subsplit": true,
  "note": "Subsplit of MD2 (L10–L20, ai boundary split)",
  "subsplit_title": "コーディング規約一覧: 命名規則に関するガイドライン"
}
```

### 4.2 NLP モード MAP.json

**変更前:**
```json
{
  "id": "MD6",
  "section": "命名規則クラス（1） (part 1/3)",
  "level": 3,
  "path": "... > 命名規則クラス（1） > 命名規則クラス（1） (part 1/3)",
  "original_start_line": 70,
  "original_end_line": 88,
  "part_file": "parts/...命名規則クラス（1）_命名規則クラス（1）_(part_13).md",
  "is_virtual": true,
  "split_reason": "nlp threshold split",
  "virtual_title": "命名規則クラス（1） (part 1/3)"
}
```

**変更後:**
```json
{
  "id": "MD6",
  "section": "命名規則クラス（1）: part-1",
  "level": 3,
  "path": "... > 命名規則クラス（1） > 命名規則クラス（1）: part-1",
  "original_start_line": 70,
  "original_end_line": 88,
  "part_file": "parts/...命名規則クラス（1）_命名規則クラス（1）_part-1.md",
  "is_subsplit": true,
  "note": "Subsplit of MD5 (L70–L88, nlp threshold split)",
  "subsplit_title": "命名規則クラス（1）: part-1"
}
```

### 4.3 AI モード INDEX.md 構造ツリー

**変更前:**
```
- [MD2] コーディング規約一覧 (L6–L51)
    - [MD3] [Virtual] ファイルの概要と参考情報 (L7–L9)
    - [MD4] [Virtual] 命名規則に関するガイドライン (L10–L20)
    - [MD5] [Virtual] コーディング・コメント・テストに関するガイドライン (L21–L43)
    - [MD6] [Virtual] セキュリティに関するガイドライン (L44–L51)
    - [MD7] 補足 (L52–L55)
```

**変更後:**
```
- [MD2] コーディング規約一覧 (L6–L51)
    - [MD3] [SubSplit] コーディング規約一覧: ファイルの概要と参考情報 (L7–L9)
    - [MD4] [SubSplit] コーディング規約一覧: 命名規則に関するガイドライン (L10–L20)
    - [MD5] [SubSplit] コーディング規約一覧: コーディング・コメント・テストに関するガイドライン (L21–L43)
    - [MD6] [SubSplit] コーディング規約一覧: セキュリティに関するガイドライン (L44–L51)
    - [MD7] 補足 (L52–L55)
```

### 4.4 NLP モード INDEX.md 構造ツリー

**変更前:**
```
- [MD5] 命名規則クラス（1） (L68–L110)
    - [MD6] [Virtual] 命名規則クラス（1） (part 1/3) (L70–L88)
    - [MD7] [Virtual] 命名規則クラス（1） (part 2/3) (L90–L90)
    - [MD8] [Virtual] 命名規則クラス（1） (part 3/3) (L92–L110)
```

**変更後:**
```
- [MD5] 命名規則クラス（1） (L68–L110)
    - [MD6] [SubSplit] 命名規則クラス（1）: part-1 (L70–L88)
    - [MD7] [SubSplit] 命名規則クラス（1）: part-2 (L90–L90)
    - [MD8] [SubSplit] 命名規則クラス（1）: part-3 (L92–L110)
```

### 4.5 INDEX.md セクション詳細

**変更前:**
```
### [MD4] [Virtual] 命名規則に関するガイドライン (H3)
- lines: L10–L20
- summary: ...
- split_reason: ai boundary split
```

**変更後:**
```
### [MD4] [SubSplit] コーディング規約一覧: 命名規則に関するガイドライン (H3)
- lines: L10–L20
- summary: ...
- note: Subsplit of MD2 (L10–L20, ai boundary split)
```

### 4.6 parts ファイルヘッダ

**変更前（AI モード）:**
```markdown
<!--
md2map fragment
id: MD4
original: 20260218サンプルコーディング規約.md
lines: 10-20
section: 命名規則に関するガイドライン
level: 3
is_virtual: true
split_reason: ai boundary split
virtual_title: 命名規則に関するガイドライン
-->
```

**変更後（AI モード）:**
```markdown
<!--
md2map fragment
id: MD4
original: 20260218サンプルコーディング規約.md
lines: 10-20
section: コーディング規約一覧: 命名規則に関するガイドライン
level: 3
is_subsplit: true
note: Subsplit of MD2 (L10–L20, ai boundary split)
subsplit_title: コーディング規約一覧: 命名規則に関するガイドライン
-->
```

**変更前（NLP モード）:**
```markdown
<!--
md2map fragment
id: MD6
original: 20260218サンプルコーディング規約.md
lines: 70-88
section: 命名規則クラス（1） (part 1/3)
level: 3
is_virtual: true
split_reason: nlp threshold split
virtual_title: 命名規則クラス（1） (part 1/3)
-->
```

**変更後（NLP モード）:**
```markdown
<!--
md2map fragment
id: MD6
original: 20260218サンプルコーディング規約.md
lines: 70-88
section: 命名規則クラス（1）: part-1
level: 3
is_subsplit: true
note: Subsplit of MD5 (L70–L88, nlp threshold split)
subsplit_title: 命名規則クラス（1）: part-1
-->
```

---

## 5. 実装手順

1. `md2map/models/section.py` のフィールド名を変更
2. `md2map/parsers/markdown_parser.py` の属性名・`note` 値生成・subsplit_title 生成ロジックを変更
3. `md2map/generators/map_generator.py` の出力フィールド名を変更
4. `md2map/generators/parts_generator.py` のヘッダ出力を変更
5. `md2map/generators/index_generator.py` のラベル・表示を変更
6. `tests/test_llm.py` のアサーションを更新
7. `spec.md` の仕様記述を更新
8. サンプル出力の再生成（`docs/examples/v0.2/output-ai/` および `docs/examples/v0.2/output-nlp/`）

---

## 6. 後方互換性への影響

- MAP.json のフィールド名が変わるため、既存の MAP.json を読み込む外部ツールがある場合は対応が必要
- `heading` モード（デフォルト）の出力には影響なし（subsplit 関連フィールドは出力されない）
- 過去の計画書（`docs/20260218enhancement_plan.md` 等）は当時の用語のまま保持し、変更しない
