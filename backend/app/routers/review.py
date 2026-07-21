"""レビューAPI"""

import json
import re
from importlib.metadata import version

from fastapi import APIRouter

from app.models.schemas import (
    LLMConfig,
    ReviewRequest,
    ReviewResponse,
    ReviewMeta,
    TestConnectionRequest,
    TestConnectionResponse,
    # Structure Matching API
    StructureMatchingRequest,
    StructureMatchingResponse,
    MatchedGroup,
    MatchedDocSection,
    MatchedCodeSymbol,
    # Group Review API
    GroupReviewRequest,
    GroupReviewResponse,
    GroupReviewResult,
    ReviewFinding,
    # Integrate API
    IntegrateRequest,
    IntegrateResponse,
    IntegratedReport,
)
from app.services.llm_service import get_llm_provider
from app.services.prompt_builder import build_system_prompt, build_review_meta, build_review_info_markdown

# pyproject.tomlからバージョンを取得
APP_VERSION = version("spec-code-ai-reviewer-backend")

router = APIRouter()

# ファイルサイズ制限（変換済みテキストベース）
MAX_DESIGN_SIZE = 10 * 1024 * 1024  # 10MB
MAX_CODE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/review", response_model=ReviewResponse)
async def review_api(request: ReviewRequest):
    """
    設計書とプログラムの突合レビューを実行する

    LLMを使用してレビューを実行し、マークダウン形式のレポートを返却する。
    リクエストにllmConfigが含まれる場合は指定されたプロバイダーを使用し、
    含まれない場合はシステムLLM（Bedrock）を使用する。
    """
    try:
        codes = request.get_code_blocks()
        designs = request.get_design_blocks()

        for design in designs:
            content = design.get("content", "")
            if len(content.encode("utf-8")) > MAX_DESIGN_SIZE:
                return ReviewResponse(
                    success=False,
                    error=(
                        f"設計書 '{design.get('filename', 'design')}' のサイズが上限"
                        f"（{MAX_DESIGN_SIZE // (1024 * 1024)}MB）を超えています。"
                    ),
                )

        for code in codes:
            content = code.get("contentWithLineNumbers", "")
            if len(content.encode("utf-8")) > MAX_CODE_SIZE:
                return ReviewResponse(
                    success=False,
                    error=(
                        f"プログラム '{code.get('filename', 'code')}' のサイズが上限"
                        f"（{MAX_CODE_SIZE // (1024 * 1024)}MB）を超えています。"
                    ),
                )

        # LLMプロバイダーを取得
        provider = get_llm_provider(request.llmConfig)

        # レビュー実行
        return provider.execute_review(
            request=request,
            version=f"v{APP_VERSION}",
        )

    except ValueError as e:
        return ReviewResponse(
            success=False,
            error=str(e),
        )
    except Exception as e:
        return ReviewResponse(
            success=False,
            error=f"AI処理中にエラーが発生しました。しばらく待ってから再試行してください。({str(e)})",
        )


@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_llm_connection(request: TestConnectionRequest):
    """
    LLM接続テスト

    設定モーダルの「接続テスト」ボタンから呼び出される。
    ユーザー指定のLLM設定で接続テストを実行する。
    provider/modelが未指定の場合はシステムLLM（Bedrock）をテストする。
    """
    # provider/modelが未指定の場合はシステムLLM（Bedrock）をテスト
    if request.provider is None:
        llm_config = None
    else:
        llm_config = LLMConfig(
            provider=request.provider,
            model=request.model or "",
            apiKey=request.apiKey,
            baseUrl=request.baseUrl,
            accessKeyId=request.accessKeyId,
            secretAccessKey=request.secretAccessKey,
            region=request.region,
        )

    try:
        provider = get_llm_provider(llm_config)
        result = provider.test_connection()

        return TestConnectionResponse(
            status="connected" if result["status"] == "connected" else "error",
            provider=provider.provider_name,
            model=provider.model_id,
            error=result.get("error"),
        )
    except ValueError as e:
        # プロバイダー設定エラー（APIキー未指定など）
        return TestConnectionResponse(
            status="error",
            provider=request.provider or "bedrock",
            model=request.model,
            error=str(e),
        )
    except Exception as e:
        # その他のエラー
        return TestConnectionResponse(
            status="error",
            provider=request.provider or "bedrock",
            model=request.model,
            error=str(e),
        )


# ---------------------------------------------------------------------------
# 分割レビュー用フォールバックプロンプト定数
# systemPromptが未指定の場合に使用されるデフォルト値
# ---------------------------------------------------------------------------

# Phase1: 構造マッチング
STRUCTURE_MATCHING_DEFAULT_ROLE = "設計書とソースコードの構造を分析する専門家"
STRUCTURE_MATCHING_DEFAULT_PURPOSE = (
    "設計書の構造（セクション一覧）とコードの構造（シンボル一覧）を比較し、"
    "関連性の高い設計書セクションとコードシンボルをグループにまとめる"
)

# Phase2: グループレビュー
GROUP_REVIEW_DEFAULT_ROLE = "設計書とソースコードの整合性をレビューする専門家"
GROUP_REVIEW_DEFAULT_PURPOSE = "設計書の記述とコード実装の整合性を確認し、指摘事項を報告する"
GROUP_REVIEW_DEFAULT_FORMAT = """マークダウン形式で、以下の内容を出力してください：
1. サマリー（このグループの整合性評価）
2. 突合結果一覧（テーブル形式: 設計書箇所、コード箇所、判定、指摘内容）
3. 詳細（問題点と推奨事項）"""
GROUP_REVIEW_DEFAULT_NOTES = [
    "- 【重要】提供されている設計書・コードは元ファイルの一部分です。"
    "全体構造情報（INDEX.md / MAP.json）で示される他の部分は別のグループでレビューされています。",
    "- 【重要】別のグループでレビューされている関数・メソッド・クラスについて"
    "「未実装」「存在しない」と指摘しないでください。"
    "全体構造情報を参照し、そのシンボルが他のグループに存在する場合は、実装済みと判断してください。",
    "- 突合結果一覧では、設計書の章番号・項目名を使用してください。グループ名やグループIDは使わないでください。",
    "- 最後に複数グループのレビュー結果を統合するので、統合時への申し送り事項があれば記載してください",
    "- 元ファイルでの行番号範囲はヘッダーコメント（`// lines: X-Y`）に記載されているので、"
    "行番号を参照する際はこの範囲に基づいて記載してください",
]

# Phase3: 結果統合
INTEGRATE_DEFAULT_ROLE = "設計書とプログラムコードの整合性を検証するレビュアー"
INTEGRATE_DEFAULT_PURPOSE = (
    "複数の部分に分けて実施したレビュー結果（下書き）を元に、"
    "設計書の構造に沿った最終レビューレポートをMarkdown形式で作成する"
)
INTEGRATE_DEFAULT_FORMAT = "Markdown形式のレビューレポートを出力してください。"
INTEGRATE_DEFAULT_NOTES = [
    "- 【重要】突合結果一覧は、各部分のレビュー結果にある突合結果をマージし、"
    "設計書の章番号・項目名で整理してください。グループID・グループ名は出力に含めないでください。",
    "- 重複する指摘は排除し、矛盾がある場合は設計書の記載を優先して判断してください。",
    "- 出力形式の指定に従い、全体を一括で評価した場合と同じ形式で出力してください。",
    "- レビュー作業の分割に関する情報（グループ名、グループID、申し送り事項等）は最終レポートに含めないでください。",
]

# ---------------------------------------------------------------------------
# ユーティリティ（分割レビュー用）
# ---------------------------------------------------------------------------


def _estimate_tokens(text: str) -> int:
    """簡易トークン数推定（日本語考慮）"""
    # 日本語は1文字あたり約1.5トークン、英数字は約0.25トークン
    japanese_chars = sum(1 for c in text if ord(c) > 0x3000)
    other_chars = len(text) - japanese_chars
    return int(japanese_chars * 1.5 + other_chars * 0.25)


def _is_token_limit_error(error_message: str) -> bool:
    """LLM APIエラーがトークン上限超過かどうかを判定する"""
    keywords = [
        "too long",          # Anthropic: "prompt is too long"
        "context length",    # OpenAI: "maximum context length"
        "input is too long", # Bedrock
        "token",             # 共通キーワード
        "maximum",           # 共通キーワード
    ]
    msg_lower = error_message.lower()
    return any(kw in msg_lower for kw in keywords)


def _extract_json(text: str) -> dict:
    """LLMの応答からJSONを抽出する"""
    # ```json ... ``` ブロックからの抽出を試行
    json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))
    # テキスト全体をJSONとしてパースを試行
    return json.loads(text.strip())


# ---------------------------------------------------------------------------
# 分割レビューAPI
# ---------------------------------------------------------------------------


@router.post(
    "/review/structure-matching", response_model=StructureMatchingResponse
)
async def structure_matching(request: StructureMatchingRequest):
    """
    構造マッチング（フェーズ1）

    設計書とコードの構造を比較し、関連性の高いグループを特定する。
    AIが設計書のINDEX.md / MAP.jsonとコードのINDEX.md / MAP.jsonを分析し、
    関連する設計書セクションとコードシンボルをグループ化する。
    """
    try:
        # doc_sections が空の場合はLLM呼び出し前にエラーを返す
        all_doc_sections = request.document.mapJson.get("sections", [])
        if not all_doc_sections:
            return StructureMatchingResponse(
                success=False,
                error="設計書セクションが空です。設計書の分割に失敗している可能性があります。分割設定を確認してください。",
            )

        # code_symbols が空の場合はLLM呼び出し前にエラーを返す
        all_code_symbols = []
        for cf in request.codeFiles:
            all_code_symbols.extend(cf.mapJson.get("symbols", []))

        if not all_code_symbols:
            return StructureMatchingResponse(
                success=False,
                error="コードシンボルが空です。コードの分割に失敗している可能性があります。分割設定を確認してください。",
            )

        provider = get_llm_provider(request.llmConfig)

        # システムプロンプト構築（prompt_builder使用）
        # roleの設定（systemPrompt.roleがあれば使用）
        if request.systemPrompt and request.systemPrompt.role:
            role = request.systemPrompt.role
        else:
            role = STRUCTURE_MATCHING_DEFAULT_ROLE

        # purposeの設定（systemPrompt.purposeを引用して構造マッチングの目的を説明）
        if request.systemPrompt and request.systemPrompt.purpose:
            purpose = (
                "最終的な目的:\n"
                "```\n"
                f"{request.systemPrompt.purpose}\n"
                "```\n\n"
                "この目的を達成するため、まず設計書の構造（セクション一覧）と"
                "コードの構造（シンボル一覧）を比較し、"
                "関連性の高い設計書セクションとコードシンボルをグループにまとめてください。"
            )
        else:
            purpose = STRUCTURE_MATCHING_DEFAULT_PURPOSE

        output_format = """以下のJSON形式で出力してください:

```json
{
  "groups": [
    {
      "id": "group1",
      "name": "グループの表示名",
      "doc_sections": ["MD1", "MD2"],
      "code_symbols": ["CD1", "CD3"]
    }
  ]
}
```

制約:
- doc_sections / code_symbols にはMAP.jsonのid値のみを文字列配列で指定してください（title, path, filename, symbol等は不要）
- すべてのIDがいずれかのグループに含まれるようにしてください

出力例（設計書: MD1, MD2, MD3 / コード: CD1, CD2 の場合）:
```json
{
  "groups": [
    {"id": "group1", "name": "ユーザー管理", "doc_sections": ["MD1", "MD2"], "code_symbols": ["CD1"]},
    {"id": "group2", "name": "認証処理", "doc_sections": ["MD3"], "code_symbols": ["CD1", "CD2"]}
  ]
}
```"""

        # 注意事項の構築
        notes_parts = [
            "- 必ず指定されたJSON形式のみで応答してください",
            "- 各グループには doc_sections と code_symbols の両方を含めることを強く推奨します。",
            "- 対応するコードが存在しない設計書セクション、または対応する設計書がないコードシンボルがある場合のみ、片方を空配列にしてください。",
            "- 無理に関連の薄い要素を組み合わせないでください",
            "- 設計書の複数セクションと、複数のコード部分が、1つのグループに対応する場合もあります。",
            "- 1つの設計書セクション、または1つのコードシンボルが、複数のグループに対応する場合もあります。",
            "- 文字数の少ないセクション、コードシンボルは、情報が含まれていない可能性があります。他のセクション、コードシンボルと合わせてグループ化してください。",
        ]

        notes = "\n".join(notes_parts)

        system_prompt = build_system_prompt(role, purpose, output_format, notes)

        # 項目数サマリー
        doc_ids = [s.get("id", "") for s in request.document.mapJson.get("sections", [])]
        code_ids = []
        for cf in request.codeFiles:
            code_ids.extend([s.get("id", "") for s in cf.mapJson.get("symbols", [])])

        # ユーザーメッセージ構築（データのみ）
        user_parts = [
            "## 入力サマリー\n",
            f"- 設計書セクション: {len(doc_ids)}件 ({', '.join(doc_ids)})",
            f"- コードシンボル: {len(code_ids)}件 ({', '.join(code_ids)})",
            f"- すべてのIDがいずれかのグループに含まれるようにしてください\n",
            "## 設計書構造\n",
            "### INDEX.md",
            request.document.indexMd,
            "\n### MAP.json",
            json.dumps(request.document.mapJson, ensure_ascii=False, indent=2),
        ]

        for code_file in request.codeFiles:
            user_parts.extend([
                f"\n## コード構造: {code_file.filename}\n",
                f"### {code_file.filename} - INDEX.md",
                code_file.indexMd,
                f"\n### {code_file.filename} - MAP.json",
                json.dumps(
                    code_file.mapJson, ensure_ascii=False, indent=2
                ),
            ])

        user_message = "\n".join(user_parts)

        # LLM呼び出し
        response_text, input_tokens, output_tokens = provider.send_message(
            system_prompt, user_message
        )

        # デバッグ: LLMレスポンスを標準出力に表示
        print("=" * 80)
        print("[DEBUG] 構造マッチング LLMレスポンス:")
        print("=" * 80)
        print(response_text)
        print("=" * 80)

        # JSON応答パース（IDのみ返却、フロントエンドで復元）
        result = _extract_json(response_text)
        groups = []
        for i, g in enumerate(result.get("groups", [])):
            group_id = g.get("id", f"group_{i + 1}")
            group_name = g.get("name", group_id)

            # IDのみでMatchedDocSectionを構築（title/pathはフロントエンドで復元）
            doc_sections = [
                MatchedDocSection(id=doc_id, title="", path="")
                for doc_id in g.get("doc_sections", [])
                if isinstance(doc_id, str)
            ]

            # IDのみでMatchedCodeSymbolを構築（filename/symbolはフロントエンドで復元）
            code_symbols = [
                MatchedCodeSymbol(id=code_id, filename="", symbol="")
                for code_id in g.get("code_symbols", [])
                if isinstance(code_id, str)
            ]

            # 推定トークン数の計算
            estimated = _estimate_tokens(
                json.dumps(g, ensure_ascii=False)
            )

            groups.append(
                MatchedGroup(
                    groupId=group_id,
                    groupName=group_name,
                    docSections=doc_sections,
                    codeSymbols=code_symbols,
                    reason="",
                    estimatedTokens=estimated,
                )
            )

        return StructureMatchingResponse(
            success=True,
            groups=groups,
            totalGroups=len(groups),
            tokensUsed={"input": input_tokens, "output": output_tokens},
        )

    except json.JSONDecodeError as e:
        return StructureMatchingResponse(
            success=False,
            error=f"AIの応答をJSONとして解析できませんでした: {str(e)}",
        )
    except RuntimeError as e:
        return StructureMatchingResponse(
            success=False,
            error=str(e),
        )
    except Exception as e:
        return StructureMatchingResponse(
            success=False,
            error=f"構造マッチング中にエラーが発生しました: {str(e)}",
        )


@router.post("/review/group", response_model=GroupReviewResponse)
async def review_group(request: GroupReviewRequest):
    """
    グループレビュー（フェーズ2）

    1グループ（関連する設計書パーツ + コードパーツ）をレビューする。
    """
    try:
        provider = get_llm_provider(request.llmConfig)

        # システムプロンプト構築（prompt_builder使用）
        # roleの設定（systemPrompt.roleがあれば使用）
        if request.systemPrompt and request.systemPrompt.role:
            role = request.systemPrompt.role
        else:
            role = GROUP_REVIEW_DEFAULT_ROLE

        # purposeの設定（systemPrompt.purposeを引用してグループレビューの目的を説明）
        if request.systemPrompt and request.systemPrompt.purpose:
            purpose = (
                "最終的な目的:\n"
                "```\n"
                f"{request.systemPrompt.purpose}\n"
                "```\n\n"
                "この目的を達成するため、以下のグループ（関連する設計書セクションとコード）について、"
                "設計書の記述とコード実装の整合性を確認し、指摘事項を報告してください。"
            )
        else:
            purpose = GROUP_REVIEW_DEFAULT_PURPOSE

        # output_formatの設定（systemPrompt.formatがあれば使用）
        if request.systemPrompt and request.systemPrompt.format:
            output_format = request.systemPrompt.format
        else:
            output_format = GROUP_REVIEW_DEFAULT_FORMAT

        # 注意事項の構築
        notes_parts = list(GROUP_REVIEW_DEFAULT_NOTES)

        # request.systemPromptがある場合は注意事項に追加
        if request.systemPrompt and request.systemPrompt.notes:
            notes_parts.extend([
                "",
                request.systemPrompt.notes,
            ])

        notes = "\n".join(notes_parts)

        system_prompt = build_system_prompt(role, purpose, output_format, notes)

        # ユーザーメッセージ構築（データのみ）
        # documentContent, codeContent はフロントエンドで結合済みのテキスト
        user_parts = [
            f"## レビュー対象\n",
            f"（内部管理用: {request.groupId} / {request.groupName}）\n",
        ]

        user_parts.extend([
            "## 設計書内容\n",
            request.documentContent,
            "\n## コード内容\n",
            request.codeContent,
        ])

        # 全体構造コンテキスト（他グループの存在を把握するため、参考情報として末尾に配置）
        if request.documentIndexMd or request.codeIndexMd or request.allGroups:
            user_parts.append("\n## 全体構造情報（参考）\n")
            user_parts.append("以下は設計書・コード全体の構造です。このグループではこの一部をレビューしています。\n")
            if request.documentIndexMd:
                user_parts.extend([
                    "### 設計書全体の構造 (INDEX.md)\n",
                    request.documentIndexMd,
                    "",
                ])
            # MAP.jsonはINDEX.mdと情報が重複するため送信しない
            if request.codeIndexMd:
                user_parts.extend([
                    "### コード全体の構造 (INDEX.md)\n",
                    request.codeIndexMd,
                    "",
                ])
            # MAP.jsonはINDEX.mdと情報が重複するため送信しない
            if request.allGroups:
                user_parts.extend([
                    "### 全グループ一覧\n",
                    "| グループ | 設計書セクション | コードシンボル |",
                    "|---------|----------------|--------------|",
                ])
                for g in request.allGroups:
                    doc_ids = ", ".join(ds.get("id", "") for ds in g.get("docSections", []))
                    code_ids = ", ".join(cs.get("id", "") for cs in g.get("codeSymbols", []))
                    user_parts.append(f"| {g.get('groupName', '')} | {doc_ids} | {code_ids} |")
                user_parts.append("")

        user_message = "\n".join(user_parts)

        # LLM呼び出し
        response_text, input_tokens, output_tokens = provider.send_message(
            system_prompt, user_message
        )

        # Markdown形式のレスポンスをそのまま格納
        review_result = GroupReviewResult(
            report=response_text,
        )

        return GroupReviewResponse(
            success=True,
            groupId=request.groupId,
            reviewResult=review_result,
            tokensUsed={"input": input_tokens, "output": output_tokens},
        )
    except RuntimeError as e:
        error_msg = str(e)
        return GroupReviewResponse(
            success=False,
            groupId=request.groupId,
            error=error_msg,
            errorCode="token_limit" if _is_token_limit_error(error_msg) else "api_error",
        )
    except Exception as e:
        error_msg = str(e)
        return GroupReviewResponse(
            success=False,
            groupId=request.groupId,
            error=f"グループレビュー中にエラーが発生しました: {error_msg}",
            errorCode="token_limit" if _is_token_limit_error(error_msg) else None,
        )


@router.post("/review/integrate", response_model=IntegrateResponse)
async def integrate_reviews(request: IntegrateRequest):
    """
    結果統合（フェーズ3）

    全グループのレビュー結果を統合し、最終レポートを生成する。
    システムプロンプト設定に基づいて、AIがMarkdown形式のレビューレポートを生成する。
    """
    try:
        provider = get_llm_provider(request.llmConfig)

        # システムプロンプト構築（prompt_builder使用）
        # roleの設定（systemPrompt.roleがあれば使用）
        if request.systemPrompt and request.systemPrompt.role:
            role = request.systemPrompt.role
        else:
            role = INTEGRATE_DEFAULT_ROLE

        # purposeの設定（systemPrompt.purposeを引用して統合の目的を説明）
        if request.systemPrompt and request.systemPrompt.purpose:
            purpose = (
                "最終的な目的:\n"
                "```\n"
                f"{request.systemPrompt.purpose}\n"
                "```\n\n"
                "この目的に対するレビューを、作業効率のため複数の部分に分けて実施しました。"
                "各部分のレビュー結果（下書き）を元に、設計書の構造に沿った1つの最終レビューレポートを作成してください。"
            )
        else:
            purpose = INTEGRATE_DEFAULT_PURPOSE

        # output_formatの設定（systemPrompt.formatがあれば使用）
        if request.systemPrompt and request.systemPrompt.format:
            output_format = request.systemPrompt.format
        else:
            output_format = INTEGRATE_DEFAULT_FORMAT

        # 注意事項の構築
        notes_parts = list(INTEGRATE_DEFAULT_NOTES)

        # request.systemPromptがある場合は注意事項に追加
        if request.systemPrompt and request.systemPrompt.notes:
            notes_parts.extend([
                "",
                request.systemPrompt.notes,
            ])

        notes = "\n".join(notes_parts)

        system_prompt = build_system_prompt(role, purpose, output_format, notes)

        # ユーザーメッセージ構築（データのみ）
        user_parts = []

        # 部分レビュー結果（グループ構造を意識させないよう「部分N」で表記）
        user_parts.append("## 部分レビュー結果（下書き）\n")
        for i, gr in enumerate(request.groupReviews, 1):
            user_parts.extend([
                f"### 部分{i}（参考: {gr.groupName}）\n",
                gr.report if gr.report else f"**サマリー**: {gr.summary}\n",
                "",
            ])

        # 全体構造コンテキスト（参考情報として末尾に配置）
        if request.documentIndexMd or request.codeIndexMd:
            user_parts.append("\n## 全体構造情報（参考）\n")
            user_parts.append("以下は設計書・コード全体の構造です。統合時の参考にしてください。\n")
            if request.documentIndexMd:
                user_parts.extend([
                    "### 設計書全体の構造 (INDEX.md)\n",
                    request.documentIndexMd,
                    "",
                ])
            # MAP.jsonはINDEX.mdと情報が重複するため送信しない
            if request.codeIndexMd:
                user_parts.extend([
                    "### コード全体の構造 (INDEX.md)\n",
                    request.codeIndexMd,
                    "",
                ])
            # MAP.jsonはINDEX.mdと情報が重複するため送信しない

        user_message = "\n".join(user_parts)

        # LLM呼び出し
        response_text, input_tokens, output_tokens = provider.send_message(
            system_prompt, user_message
        )

        # IntegratedReport構築
        integrated_report = IntegratedReport(
            overallSummary=f"レビュー対象: {len(request.groupReviews)}グループ",
            consistencyScore=0.0,
            keyIssues=[],
            crossGroupIssues=[],
            statistics={
                "totalGroupsReviewed": len(request.groupReviews),
            },
            deduplicatedFindings=[],
        )

        # ReviewMeta構築（一括レビューと同様）
        review_meta_dict = build_review_meta(
            version=f"v{APP_VERSION}",
            model_id=provider.model_id,
            provider=provider.provider_name,
            designs=request.designs,
            codes=request.codes,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            review_mode="split",
        )
        review_meta = ReviewMeta(**review_meta_dict)

        groups = request.structureMatching.get("groups", []) if request.structureMatching else []
        review_info_markdown = build_review_info_markdown(review_meta_dict, groups=groups)

        return IntegrateResponse(
            success=True,
            report=review_info_markdown + response_text,
            integratedReport=integrated_report,
            reviewMeta=review_meta,
            tokensUsed={"input": input_tokens, "output": output_tokens},
        )

    except RuntimeError as e:
        error_msg = str(e)
        return IntegrateResponse(
            success=False,
            error=error_msg,
            errorCode="token_limit" if _is_token_limit_error(error_msg) else "api_error",
        )
    except Exception as e:
        error_msg = str(e)
        return IntegrateResponse(
            success=False,
            error=f"結果統合中にエラーが発生しました: {error_msg}",
            errorCode="token_limit" if _is_token_limit_error(error_msg) else None,
        )
