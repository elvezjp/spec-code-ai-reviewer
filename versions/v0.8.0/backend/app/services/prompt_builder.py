"""プロンプト組み立て・メタデータ構築の共通ロジック

全LLMプロバイダー（Bedrock / Anthropic / OpenAI）で共通して使用する
プロンプト組み立てとメタデータ構築のロジックを提供する。
"""

from datetime import datetime


def build_system_prompt(role: str, purpose: str, format: str, notes: str) -> str:
    """システムプロンプトを組み立てる

    Args:
        role: AIの役割
        purpose: レビューの目的
        format: 出力形式
        notes: 注意事項

    Returns:
        str: 組み立てられたシステムプロンプト
    """
    return f"""## 役割
{role}

## 目的
{purpose}

## 出力形式
{format}

## 注意事項
{notes}"""


def build_user_message(
    spec_markdown: str | None,
    spec_filename: str | None,
    designs: list[dict],
    codes: list[dict],
    legacy_code_with_line_numbers: str | None = None,
    legacy_code_filename: str | None = None,
) -> str:
    """ユーザーメッセージを組み立てる

    Args:
        spec_markdown: 設計書のMarkdown（後方互換用）
        spec_filename: 設計書のファイル名（後方互換用）
        designs: 設計書のリスト
        codes: コードのリスト
        legacy_code_with_line_numbers: 後方互換用の単一コード文字列
        legacy_code_filename: 後方互換用の単一コードのファイル名

    Returns:
        str: 組み立てられたユーザーメッセージ

    Raises:
        ValueError: 設計書またはコードが指定されていない場合
    """
    code_blocks = codes.copy()
    design_blocks = designs.copy()

    # 後方互換: 旧フィールドのみが提供された場合はリスト形式に変換
    if not code_blocks and legacy_code_with_line_numbers:
        code_blocks = [
            {
                "filename": legacy_code_filename or "code",
                "contentWithLineNumbers": legacy_code_with_line_numbers,
            }
        ]

    if not design_blocks and spec_markdown:
        design_blocks = [
            {
                "filename": spec_filename or "design",
                "content": spec_markdown,
                "isMain": True,
            }
        ]

    if not code_blocks:
        raise ValueError("コードファイルが指定されていません。")

    if not design_blocks:
        raise ValueError("設計書が指定されていません。")

    review_targets = {"designs": [], "programs": []}
    design_sections = []
    program_sections = []

    # メイン設計書を先頭に並び替え
    design_blocks = sorted(
        design_blocks,
        key=lambda d: 0 if d.get("isMain") else 1,
    )

    for design in design_blocks:
        filename = design.get("filename", "design")
        is_main = design.get("isMain") or False
        role = "メイン" if is_main else "参照"
        design_type = design.get("type") or "設計書"

        meta = [f"役割: {role}", f"種別: {design_type}"]
        review_targets["designs"].append(f"- 設計書: {filename}（{'; '.join(meta)}）")
        design_sections.append(
            "\n".join(
                [
                    f"## 設計書: {filename}",
                    f"- 種別: {design_type}",
                    f"- 役割: {role}",
                    "",
                    design.get("content", ""),
                ]
            ).strip()
        )

    for code in code_blocks:
        filename = code.get("filename", "code")
        content = code.get("contentWithLineNumbers", "")
        review_targets["programs"].append(f"- プログラム: {filename}")
        program_sections.append(
            f"## プログラム: {filename}\n\n```\n{content}\n```"
        )

    designs_text = "\n\n".join(design_sections)
    programs_text = "\n\n".join(program_sections)

    review_targets_text = "\n".join(
        [
            "## 設計書",
            "\n".join(review_targets["designs"]) or "- (未指定)",
            "",
            "## プログラム",
            "\n".join(review_targets["programs"]) or "- (未指定)",
        ]
    )

    return f"""以下の設計書とプログラムを突合レビューしてください。

# レビュー対象一覧
{review_targets_text}

# 設計書詳細
{designs_text}

# プログラム詳細
{programs_text}"""


def build_review_meta(
    version: str,
    model_id: str,
    provider: str,
    designs: list[dict],
    codes: list[dict],
    input_tokens: int,
    output_tokens: int,
    executed_at: str | None = None,
) -> dict:
    """レビューメタ情報を構築する

    Args:
        version: アプリケーションのバージョン番号
        model_id: 使用したAIモデルのID
        provider: プロバイダー名 (bedrock/anthropic/openai)
        designs: 設計書のリスト
        codes: コードのリスト
        input_tokens: 入力トークン数
        output_tokens: 出力トークン数
        executed_at: レビュー実行日時（ISO形式）- 未指定時は現在日時を使用

    Returns:
        dict: ReviewMeta形式の辞書
    """
    # ツール名の表示名変換マップ
    tool_labels = {"markitdown": "MarkItDown", "excel2md": "excel2md"}

    # executed_atが指定されていない場合は現在日時を使用（YYYY/MM/DD HH:MM形式）
    if executed_at:
        actual_executed_at = executed_at
    else:
        now = datetime.now()
        actual_executed_at = now.strftime("%Y/%m/%d %H:%M")

    return {
        "version": version,
        "modelId": model_id,
        "provider": provider,
        "executedAt": actual_executed_at,
        "designs": [
            {
                "filename": d.get("filename", "design"),
                "role": "メイン" if d.get("isMain") else "参照",
                "isMain": d.get("isMain") or False,
                "type": d.get("type") or "設計書",
                "tool": tool_labels.get(
                    str(d.get("tool") or "markitdown").lower(),
                    d.get("tool") or "MarkItDown",
                ),
            }
            for d in designs
        ],
        "programs": [{"filename": c.get("filename", "code")} for c in codes],
        "inputTokens": input_tokens,
        "outputTokens": output_tokens,
    }


def build_review_info_markdown(review_meta: dict) -> str:
    """レビュー情報セクションのマークダウンを構築する

    Args:
        review_meta: ReviewMeta形式の辞書

    Returns:
        str: マークダウン形式のレビュー情報
    """
    version = review_meta.get("version", "")
    model_id = review_meta.get("modelId", "")
    provider = review_meta.get("provider", "")
    executed_at = review_meta.get("executedAt", "")
    # executedAtはフロントエンドでフォーマット済み（YYYY/MM/DD HH:MM形式）
    executed_at_formatted = executed_at

    input_tokens = review_meta.get("inputTokens", 0)
    output_tokens = review_meta.get("outputTokens", 0)
    designs = review_meta.get("designs", [])
    programs = review_meta.get("programs", [])

    # 設計書テーブル
    design_rows = "\n".join(
        [f"| {d['filename']} | {d['role']} | {d['type']} | {d['tool']} |" for d in designs]
    )
    design_table = (
        f"""### 設計書

| ファイル名 | 役割 | 種別 | ツール |
|-----------|------|------|--------|
{design_rows}
"""
        if designs
        else ""
    )

    # プログラムテーブル
    program_rows = "\n".join([f"| {p['filename']} |" for p in programs])
    program_table = (
        f"""### プログラム

| ファイル名 |
|-----------|
{program_rows}
"""
        if programs
        else ""
    )

    # プロバイダー行を追加
    provider_row = f"| プロバイダー | {provider} |" if provider else ""

    return f"""# 設計書-Javaプログラム突合 AIレビュアー レビューレポート

## レビュー情報

| 項目 | 内容 |
|------|------|
| バージョン | {version} |
{provider_row}
| モデルID | {model_id} |
| レビュー実行日時 | {executed_at_formatted} |
| 入力トークン数 | {input_tokens:,} |
| 出力トークン数 | {output_tokens:,} |

{design_table}
{program_table}
---

## AIによるレビュー結果

以下はAIが出力したレビュー結果です。

"""
