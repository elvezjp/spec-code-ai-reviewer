"""markdown_organizer.py の単体テスト

テストケース:
- UT-MD-001: estimate_tokens() - 基本的なトークン数推定
- UT-MD-002: estimate_tokens() - 空文字列
- UT-MD-003: build_markdown_organize_system_prompt() - プロンプト生成
- UT-MD-004: build_markdown_organize_user_message() - ユーザーメッセージ生成
- UT-MD-005: split_markdown_by_section() - 章単位分割（見出しあり）
- UT-MD-006: split_markdown_by_section() - 見出しなし
- UT-MD-007: assign_reference_ids() - 段落単位の参照ID付与
- UT-MD-008: assign_reference_ids() - 表行単位の参照ID付与
- UT-MD-009: assign_reference_ids() - 箇条書きの参照ID付与
- UT-MD-010: assign_reference_ids() - コードブロック内はスキップ
- UT-MD-011: detect_warnings() - 改変検出
- UT-MD-012: detect_warnings() - 参照ID欠落検出
- UT-MD-013: detect_warnings() - 警告なし
"""

import pytest

from app.services.markdown_organizer import (
    assign_reference_ids,
    build_markdown_organize_system_prompt,
    build_markdown_organize_user_message,
    detect_warnings,
    estimate_tokens,
    split_markdown_by_section,
)


class TestEstimateTokens:
    """estimate_tokens() のテスト"""

    def test_ut_md_001_basic(self):
        """UT-MD-001: 基本的なトークン数推定"""
        text = "Hello, world!"
        result = estimate_tokens(text)

        assert result > 0
        assert result == max(1, (len(text) + 3) // 4)  # 簡易推定式

    def test_ut_md_002_empty_string(self):
        """UT-MD-002: 空文字列は1を返す"""
        result = estimate_tokens("")

        assert result == 1

    def test_estimate_tokens_long_text(self):
        """長いテキストのトークン数推定"""
        text = "a" * 100
        result = estimate_tokens(text)

        assert result == 25  # 100 / 4 = 25


class TestBuildMarkdownOrganizeSystemPrompt:
    """build_markdown_organize_system_prompt() のテスト"""

    def test_ut_md_003_basic(self):
        """UT-MD-003: プロンプト生成"""
        policy = "要件/条件/例外で整理してください。"
        result = build_markdown_organize_system_prompt(policy)

        assert "設計書Markdownの構造化を行うアシスタント" in result
        assert "要約や推測は禁止" in result
        assert "## 整理方針" in result
        assert policy in result

    def test_build_markdown_organize_system_prompt_empty_policy(self):
        """空のポリシーでもプロンプトが生成される"""
        result = build_markdown_organize_system_prompt("")

        assert "## 整理方針" in result


class TestBuildMarkdownOrganizeUserMessage:
    """build_markdown_organize_user_message() のテスト"""

    def test_ut_md_004_basic(self):
        """UT-MD-004: ユーザーメッセージ生成"""
        markdown = "## 機能\n説明文"
        result = build_markdown_organize_user_message(markdown)

        assert "# 原文Markdown" in result
        assert markdown in result

    def test_build_markdown_organize_user_message_empty(self):
        """空のMarkdownでもメッセージが生成される"""
        result = build_markdown_organize_user_message("")

        assert "# 原文Markdown" in result


class TestSplitMarkdownBySection:
    """split_markdown_by_section() のテスト"""

    def test_ut_md_005_with_headings(self):
        """UT-MD-005: 章単位分割（見出しあり）"""
        markdown = """## 第1章
内容1

## 第2章
内容2

### 第2-1節
内容2-1
"""
        result = split_markdown_by_section(markdown)

        assert len(result) == 3
        assert "第1章" in result[0]
        assert "第2章" in result[1]
        assert "第2-1節" in result[2]

    def test_ut_md_006_no_headings(self):
        """UT-MD-006: 見出しなしは1つのセクションとして扱う"""
        markdown = """段落1

段落2
"""
        result = split_markdown_by_section(markdown)

        assert len(result) == 1
        assert "段落1" in result[0]
        assert "段落2" in result[0]

    def test_split_markdown_by_section_empty(self):
        """空のMarkdownは空リストを返す"""
        result = split_markdown_by_section("")

        assert result == []

    def test_split_markdown_by_section_only_headings(self):
        """見出しのみの場合は各見出しがセクションになる"""
        markdown = """## 章1

## 章2
"""
        result = split_markdown_by_section(markdown)

        assert len(result) == 2


class TestAssignReferenceIds:
    """assign_reference_ids() のテスト"""

    def test_ut_md_007_paragraphs(self):
        """UT-MD-007: 段落単位の参照ID付与"""
        markdown = """## 機能1
段落1です。

段落2です。
"""
        result = assign_reference_ids(markdown)

        assert "[ref:S1-P1]" in result
        assert "[ref:S1-P2]" in result
        assert "段落1です" in result
        assert "段落2です" in result

    def test_ut_md_008_tables(self):
        """UT-MD-008: 表行単位の参照ID付与"""
        markdown = """## 機能
| 項目 | 説明 |
|---|---|
| 項目1 | 説明1 |
| 項目2 | 説明2 |
"""
        result = assign_reference_ids(markdown)

        assert "| 項目 | 説明 | 参照ID |" in result or "| 参照ID |" in result
        assert "[ref:T1-R1]" in result
        assert "[ref:T1-R2]" in result

    def test_ut_md_009_lists(self):
        """UT-MD-009: 箇条書きの参照ID付与"""
        markdown = """## 機能
- 項目1
- 項目2
"""
        result = assign_reference_ids(markdown)

        assert "[ref:S1-P1-A]" in result
        assert "[ref:S1-P1-B]" in result

    def test_ut_md_010_code_blocks(self):
        """UT-MD-010: コードブロック内はスキップ"""
        markdown = """## 機能
```python
def func():
    pass
```
通常の段落です。
"""
        result = assign_reference_ids(markdown)

        assert "```python" in result
        assert "def func():" in result
        assert "[ref:S1-P1]" in result  # コードブロック外の段落にはIDが付与される

    def test_assign_reference_ids_nested_headings(self):
        """階層見出しの参照ID付与"""
        markdown = """## 章1
段落1

### 節1-1
段落2
"""
        result = assign_reference_ids(markdown)

        assert "[ref:S1-P1]" in result
        assert "[ref:S1-1-P1]" in result

    def test_assign_reference_ids_existing_refs(self):
        """既存の参照IDがある場合は追加しない"""
        markdown = """## 機能
[ref:S1-P1] 既存のID付き段落

通常の段落
"""
        result = assign_reference_ids(markdown)

        # 既存のIDはそのまま、新しい段落にはIDが付与される
        assert "[ref:S1-P1]" in result
        assert "[ref:S1-P2]" in result

    def test_assign_reference_ids_table_with_existing_ref_column(self):
        """既に参照ID列がある表は追加しない"""
        markdown = """## 機能
| 項目 | 参照ID |
|---|---|
| 項目1 | [ref:T1-R1] |
"""
        result = assign_reference_ids(markdown)

        # 参照ID列が既にある場合は重複しない
        assert "[ref:T1-R1]" in result


class TestDetectWarnings:
    """detect_warnings() のテスト"""

    def test_ut_md_011_content_modified(self):
        """UT-MD-011: 改変検出（内容が大幅に短縮された場合）"""
        original = "a" * 1000
        organized = "a" * 100  # 50%以下に短縮

        result = detect_warnings(original, organized)

        assert len(result) > 0
        assert any(w["code"] == "content_modified" for w in result)

    def test_ut_md_012_ref_missing(self):
        """UT-MD-012: 参照ID欠落検出"""
        original = "## 機能\n段落1\n段落2"
        organized = """## 機能
段落1（IDなし）
段落2（IDなし）
"""

        result = detect_warnings(original, organized)

        assert len(result) > 0
        assert any(w["code"] == "ref_missing" for w in result)

    def test_ut_md_013_no_warnings(self):
        """UT-MD-013: 警告なし（適切に整理された場合）"""
        original = "## 機能\n段落1"
        organized = """## 機能
[ref:S1-P1] 段落1
"""

        result = detect_warnings(original, organized)

        # 参照IDが適切に付与されていれば警告なし
        warnings = [w for w in result if w["code"] == "ref_missing"]
        assert len(warnings) == 0

    def test_detect_warnings_table_ref_missing(self):
        """表の参照ID欠落検出"""
        original = "## 機能\n| 項目 | 説明 |\n|---|---|\n| 項目1 | 説明1 |"
        organized = """## 機能
| 項目 | 説明 |
|---|---|
| 項目1 | 説明1 |
"""

        result = detect_warnings(original, organized)

        assert any(w["code"] == "ref_missing" for w in result)

    def test_detect_warnings_list_ref_missing(self):
        """箇条書きの参照ID欠落検出"""
        original = "## 機能\n- 項目1\n- 項目2"
        organized = """## 機能
- 項目1
- 項目2
"""

        result = detect_warnings(original, organized)

        assert any(w["code"] == "ref_missing" for w in result)

    def test_detect_warnings_code_block_ignored(self):
        """コードブロック内は警告対象外"""
        original = "## 機能\n段落1"
        organized = """## 機能
```python
def func():
    pass
```
[ref:S1-P1] 段落1
"""

        result = detect_warnings(original, organized)

        # コードブロック内はカウントされないので警告なし
        warnings = [w for w in result if w["code"] == "ref_missing"]
        assert len(warnings) == 0

    def test_detect_warnings_small_reduction_no_warning(self):
        """小さな短縮では警告が出ない"""
        original = "a" * 100
        organized = "a" * 60  # 50%以上なので警告なし

        result = detect_warnings(original, organized)

        warnings = [w for w in result if w["code"] == "content_modified"]
        assert len(warnings) == 0
