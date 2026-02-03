"""段階的要約サービス

設計書・コードのチャンクを段階的に要約するためのプロンプト生成。
"""

from __future__ import annotations

from typing import Literal


def build_progressive_summary_prompt(
    type: Literal["spec", "code"],
    chunk: dict,
    chunk_outline: str,
    current_summary: str,
    policy: str,
) -> tuple[str, str]:
    """
    段階的要約用のプロンプトを生成する。

    Args:
        type: "spec" (設計書) or "code" (コード)
        chunk: {"id": str, "title": str, "text": str}
        chunk_outline: 全体のチャンク構成
        current_summary: これまでの累積サマリー
        policy: ユーザーが指定した要約方針

    Returns:
        (system_prompt, user_message)
    """
    if type == "spec":
        return _build_spec_prompt(chunk, chunk_outline, current_summary, policy)
    else:
        return _build_code_prompt(chunk, chunk_outline, current_summary, policy)


def _build_spec_prompt(
    chunk: dict,
    chunk_outline: str,
    current_summary: str,
    policy: str,
) -> tuple[str, str]:
    """設計書用のプロンプトを生成する。"""

    system_prompt = """あなたは設計書の段階的要約アシスタントです。

## 指示
与えられたチャンクを要約し、現在のサマリーに統合してください。

## ルール
- 要約や推測は禁止。原文の意味を変えない。
- 出力はMarkdown形式で、以下の観点で整理する：
  - 機能一覧
  - 入力仕様
  - 出力仕様
  - 制約・条件
  - 例外処理
  - 非機能要件
- 重複する内容は統合し、矛盾があれば明記する。
- 出力はサマリー全文のMarkdownのみ。説明文は不要。"""

    user_message = f"""## 追加の注意事項
{policy}

## 全体構成
{chunk_outline}

## 現在のサマリー
{current_summary if current_summary else "(まだサマリーはありません)"}

## 対象チャンク: {chunk["title"]}
{chunk["text"]}

## 出力
統合後のサマリー全文をMarkdown形式で出力してください。"""

    return system_prompt, user_message


def _build_code_prompt(
    chunk: dict,
    chunk_outline: str,
    current_summary: str,
    policy: str,
) -> tuple[str, str]:
    """コード用のプロンプトを生成する。"""

    system_prompt = """あなたはコードの段階的要約アシスタントです。

## 指示
与えられたコードチャンクを要約し、現在のサマリーに統合してください。

## ルール
- 推測は禁止。コードにない事項は書かない。
- 出力はMarkdown形式で、以下の観点で整理する：
  - エントリーポイント
  - API（公開関数・メソッド）
  - DB操作
  - クラス・構造体
  - 主要な関数
  - 依存関係
- 重複する内容は統合し、矛盾があれば明記する。
- 出力はサマリー全文のMarkdownのみ。説明文は不要。"""

    user_message = f"""## 追加の注意事項
{policy}

## 全体構成
{chunk_outline}

## 現在のサマリー
{current_summary if current_summary else "(まだサマリーはありません)"}

## 対象チャンク: {chunk["title"]}
{chunk["text"]}

## 出力
統合後のサマリー全文をMarkdown形式で出力してください。"""

    return system_prompt, user_message
