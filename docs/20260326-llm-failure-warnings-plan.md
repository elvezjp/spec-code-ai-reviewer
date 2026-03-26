# LLM 呼び出し失敗時の warnings 追加 修正計画書

## 概要

AI 分割モード（`--split-mode ai`）または AI サマリーモード（`--summary-mode ai`）で LLM 呼び出しが失敗した場合、`parse()` が返す `warnings` リストにエラー情報を追加する。

対応 Issue: [#19](https://github.com/elvezjp/md2map/issues/19)

## 背景

- 現状、LLM 失敗時は `logger.warning()` でログ出力するのみで、`parse()` の戻り値 `warnings` には含まれない
- バックエンド API 等の呼び出し元は `warnings` を参照するが、LLM エラーが含まれないため認証エラーとテキスト不足を区別できない

## 前提

- 現在の実装: md2map ルート（`md2map/`）、バージョン v0.4.0
- 今回の修正は v0.4.1 として実装する

---

## Step 0: v0.4.0 の退避と v0.4.1 の準備

### v0.4.0 の退避

現在の実装を `versions/v0.4.0` に退避する。

```
対象ファイル:
  md2map/         → versions/v0.4.0/md2map/
  tests/          → versions/v0.4.0/tests/
  main.py         → versions/v0.4.0/main.py
  pyproject.toml  → versions/v0.4.0/pyproject.toml
  uv.lock         → versions/v0.4.0/uv.lock
  spec.md         → versions/v0.4.0/spec.md
```

### v0.4.1 の準備

- `pyproject.toml` の `version` を `"0.4.1"` に更新
- `spec.md` にバージョン番号を反映

---

## 現状の問題箇所

| メソッド | 失敗時の動作 | warnings への追加 |
|---|---|---|
| `_generate_ai_summary()` (L578-583) | `logger.warning()` + `return None` | なし |
| `_select_chunks_ai()` (L917-921) | `logger.warning()` + `return [], None` | なし |

## 設計方針

### warnings リストの受け渡し

`parse()` メソッド内で生成される `warnings` リストを、LLM 呼び出しを行うメソッドからアクセスできるようにする必要がある。

**方針: インスタンス変数として `_warnings` を導入**

- `parse()` 呼び出し時にインスタンス変数 `self._warnings` を初期化する
- `_generate_ai_summary()` と `_select_chunks_ai()` で `self._warnings` に追加する
- `parse()` の最後に `self._warnings` を返す

この方針の利点:
- 既存メソッドのシグネチャを変更しない（`_extract_section_info()` → `_generate_ai_summary()` の呼び出しチェーンで `warnings` を引き回す必要がない）
- `_refine_sections()` → `_select_chunks_ai()` も同様

---

## Step 1: v0.4.0 の退避と v0.4.1 の準備

- `versions/v0.4.0/` に現在の実装を退避
- `pyproject.toml` の `version` を `"0.4.1"` に更新
- `spec.md` にバージョン番号を反映

---

## Step 2: `_warnings` インスタンス変数の導入

### `parse()` の変更

```python
def parse(self, file_path: str, max_depth: int = 3) -> Tuple[List[Section], List[str]]:
    logger = get_logger()
    warnings: List[str] = []
    self._warnings = warnings  # 追加: LLM 失敗メソッドからアクセス可能にする

    # ... 既存処理 ...

    return sections, warnings
```

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `md2map/parsers/markdown_parser.py` | `parse()` 内で `self._warnings = warnings` を追加 |

---

## Step 3: LLM 失敗時の warnings 追加

### `_generate_ai_summary()` の変更

```python
except Exception as exc:
    warning_msg = f"AI summary generation failed for '{section.title}': {exc}"
    logger.warning(warning_msg)
    self._warnings.append(warning_msg)  # 追加
    return None
```

### `_select_chunks_ai()` の変更

```python
except Exception as exc:
    warning_msg = f"AI API call failed: {exc}"
    logger.warning(warning_msg)
    self._warnings.append(warning_msg)  # 追加
    return [], None
```

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `md2map/parsers/markdown_parser.py` | `_generate_ai_summary()` と `_select_chunks_ai()` の `except` ブロックに `self._warnings.append()` を追加 |

---

## Step 4: テストの追加

### テストケース

| # | ケース | 内容 |
|---|---|---|
| 1 | AI サマリー失敗時の warning | `summary_mode="ai"` で LLM が例外を投げた場合、`warnings` にメッセージが含まれることを確認 |
| 2 | AI 分割失敗時の warning | `split_mode="ai"` で LLM が例外を投げた場合、`warnings` にメッセージが含まれることを確認 |
| 3 | 複数セクション失敗 | 複数セクションで LLM が失敗した場合、各セクションの warning が全て `warnings` に含まれることを確認 |
| 4 | 成功時は warning なし | LLM が正常応答した場合、LLM 関連の warning が `warnings` に含まれないことを確認 |

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `tests/test_markdown_parser.py` | LLM 失敗時の warnings テスト 4 件を追加 |

---

## Step 5: spec.md の更新

### 7.3 要約生成

AI サマリー失敗時の挙動として、`warnings` にエラーメッセージが追加される旨を追記。

### 3.3 セクション再分割フェーズ

AI 分割失敗時の挙動として、`warnings` にエラーメッセージが追加される旨を追記。

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `spec.md` | AI 失敗時に `warnings` に追加される旨を追記 |

---

## 影響範囲

| 対象 | 影響 |
|---|---|
| `versions/v0.4.0/` | v0.4.0 の退避 |
| `pyproject.toml` | `version` を `"0.4.1"` に更新 |
| `md2map/parsers/markdown_parser.py` | `parse()` に `self._warnings` 初期化追加、`_generate_ai_summary()` と `_select_chunks_ai()` に `self._warnings.append()` 追加 |
| `tests/test_markdown_parser.py` | テスト 4 件追加 |
| `spec.md` | バージョン番号更新、AI 失敗時の warnings 追記 |
| `md2map/cli.py` | 変更なし（既に `warnings` を出力する仕組みがある） |
| `md2map/generators/` | 変更なし |
| 既存テスト | 影響なし（後方互換性維持） |

---

## 完了チェックリスト

### Step 1: v0.4.0 の退避と v0.4.1 の準備

- [x] `versions/v0.4.0/` に既存実装を退避
- [x] `pyproject.toml` の version を `"0.4.1"` に更新
- [x] `spec.md` にバージョン番号を反映

### Step 2: `_warnings` インスタンス変数の導入

- [x] `parse()` 内で `self._warnings = warnings` を追加

### Step 3: LLM 失敗時の warnings 追加

- [x] `_generate_ai_summary()` の `except` ブロックに `self._warnings.append()` を追加
- [x] `_select_chunks_ai()` の `except` ブロックに `self._warnings.append()` を追加

### Step 4: テストの追加

- [x] AI サマリー失敗時の warning テスト
- [x] AI 分割失敗時の warning テスト
- [x] 複数セクション失敗時のテスト
- [x] 成功時は warning なしのテスト
- [x] 全テスト通過（130 件）

### Step 5: spec.md の更新

- [x] AI サマリー失敗時の warnings 追記
- [x] AI 分割失敗時の warnings 追記

### 最終確認

- [x] 既存テストが全て通過（後方互換性維持、全 130 件パス）
- [x] `spec.md` の更新内容が実装と整合している
