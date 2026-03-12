"""要約API"""

from fastapi import APIRouter

from app.models.schemas import (
    SummarizeRequest,
    SummarizeResponse,
)
from app.services.llm_service import get_llm_provider

router = APIRouter()


def _estimate_tokens(text: str) -> int:
    """簡易トークン数推定（日本語考慮）"""
    # 日本語は1文字あたり約1.5トークン、英数字は約0.25トークン
    japanese_chars = sum(1 for c in text if ord(c) > 0x3000)
    other_chars = len(text) - japanese_chars
    return int(japanese_chars * 1.5 + other_chars * 0.25)


def _build_summarize_prompt(target_type: str) -> tuple[str, str]:
    """要約のシステムプロンプトとユーザーメッセージプレフィックスを構築する"""

    if target_type == "design":
        system = (
            "あなたは設計書を要約する専門家です。\n"
            "設計書の内容を、突合レビューに必要な情報を保ちながら要約してください。"
        )
        instruction = (
            "以下の設計書テキストを要約してください。\n\n"
            "【必ず保持する情報】\n"
            "- 仕様の具体的な値（数値、文字数制限、範囲、閾値）\n"
            "- 条件分岐・判定条件\n"
            "- エラーケース・例外条件\n"
            "- 制約・前提条件\n"
            "- 入出力の項目名と型\n"
            "- 元の行番号参照（Lxx-Lyy）\n\n"
            "【省略してよい情報】\n"
            "- 書式設定や見た目に関する説明\n"
            "- 同じ内容の繰り返し・冗長な説明\n"
            "- 例の詳細展開（代表例1つに集約可）\n\n"
            "【設計書テキスト】\n"
        )
    elif target_type == "code":
        system = (
            "あなたはソースコードを要約する専門家です。\n"
            "コードの内容を、突合レビューに必要な情報を保ちながら要約してください。"
        )
        instruction = (
            "以下のソースコードを要約してください。\n\n"
            "【必ず保持する情報】\n"
            "- 関数/メソッドのシグネチャ（名前、引数、戻り値の型）\n"
            "- バリデーション条件と閾値\n"
            "- 条件分岐のロジック\n"
            "- エラーハンドリング\n"
            "- 重要なビジネスロジック\n"
            "- 元の行番号コメント（// lines: X-Y）\n\n"
            "【省略してよい情報】\n"
            "- import文\n"
            "- getter/setterなどの定型コード\n"
            "- ログ出力\n"
            "- 自明なコメント\n\n"
            "【ソースコード】\n"
        )
    else:  # review_result
        system = (
            "あなたはレビュー結果を要約する専門家です。\n"
            "レビュー結果の内容を、指摘事項を漏れなく保ちながら要約してください。"
        )
        instruction = (
            "以下のレビュー結果を要約してください。\n\n"
            "【必ず保持する情報】\n"
            "- 全ての指摘事項（設計書箇所、コード箇所、問題の内容）\n"
            "- 重要度・深刻度\n"
            "- 対応推奨事項\n"
            "- 申し送り事項\n\n"
            "【省略してよい情報】\n"
            "- 「問題なし」の項目の詳細\n"
            "- 詳細な背景説明\n"
            "- 重複する指摘の2つ目以降\n\n"
            "【レビュー結果】\n"
        )

    return system, instruction


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_text(request: SummarizeRequest):
    """
    テキスト要約API

    設計書、コード、レビュー結果を要約する。
    トークン上限超過時のリトライで使用される。
    """
    try:
        provider = get_llm_provider(request.llmConfig)

        system_prompt, instruction = _build_summarize_prompt(request.targetType)
        user_message = instruction + request.text

        response_text, input_tokens, output_tokens = provider.send_message(
            system_prompt, user_message
        )

        original_tokens = _estimate_tokens(request.text)
        summarized_tokens = _estimate_tokens(response_text)

        return SummarizeResponse(
            success=True,
            summarizedText=response_text,
            originalTokens=original_tokens,
            summarizedTokens=summarized_tokens,
            tokensUsed={"input": input_tokens, "output": output_tokens},
        )
    except Exception as e:
        return SummarizeResponse(
            success=False,
            error=f"要約中にエラーが発生しました: {str(e)}",
        )
