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
    # マッピングモード対応
    ReviewMode,
)
from app.services.llm_service import get_llm_provider
from app.services.prompt_builder import (
    build_system_prompt,
    build_review_meta,
    _build_structure_map_section,
)

# pyproject.tomlからバージョンを取得
APP_VERSION = version("spec-code-ai-reviewer-backend")

router = APIRouter()

# ---------------------------------------------------------------------------
# フォールバック用プロンプト定数（分割レビュー）
# request.systemPrompt で指定されなかった場合に使用するデフォルト値
# ---------------------------------------------------------------------------

# --- 構造マッチング（フェーズ1） ---
_SM_ROLE_DEFAULT = "設計書とソースコードの構造を分析する専門家"
_SM_ROLE_MAPPING = "設計書とソースコードのマッピングを行う専門家"

_SM_PURPOSE_DEFAULT = (
    "設計書の構造（セクション一覧）とコードの構造（シンボル一覧）を比較し、"
    "関連性の高い設計書セクションとコードシンボルをグループにまとめる"
)
_SM_PURPOSE_MAPPING = (
    "設計書の構造（セクション一覧）とコードの構造（シンボル一覧）を比較し、"
    "設計書の各項目がどのコード要素で実装されているかを推定してグループにまとめる"
)
_SM_PURPOSE_SUFFIX_DEFAULT = (
    "この目的を達成するため、まず設計書の構造（セクション一覧）と"
    "コードの構造（シンボル一覧）を比較し、"
    "関連性の高い設計書セクションとコードシンボルをグループにまとめてください。"
)
_SM_PURPOSE_SUFFIX_MAPPING = (
    "この目的を達成するため、設計書の構造（セクション一覧）と"
    "コードの構造（シンボル一覧）を比較し、"
    "設計書の各項目がどのコード要素で実装されているかを推定してグループにまとめてください。"
)

# --- グループレビュー（フェーズ2） ---
_GR_ROLE_DEFAULT = "設計書とソースコードの整合性をレビューする専門家"
_GR_ROLE_MAPPING = "設計書とソースコードのマッピングを行う専門家"

_GR_PURPOSE_DEFAULT = "設計書の記述とコード実装の整合性を確認し、指摘事項を報告する"
_GR_PURPOSE_MAPPING = "設計書の各項目がコードのどこで実装されているかを特定する"
_GR_PURPOSE_SUFFIX_DEFAULT = (
    "この目的を達成するため、以下のグループ（関連する設計書セクションとコード）について、"
    "設計書の記述とコード実装の整合性を確認し、指摘事項を報告してください。"
)
_GR_PURPOSE_SUFFIX_MAPPING = (
    "この目的を達成するため、以下のグループ（関連する設計書セクションとコード）について、"
    "設計書の各項目がコードのどこで実装されているかを特定してください。"
)

_GR_FORMAT_DEFAULT = """マークダウン形式で、以下の内容を出力してください：
1. サマリー（このグループの整合性評価）
2. 突合結果一覧（テーブル形式: 設計書箇所、コード箇所、判定、指摘内容）
3. 詳細（問題点と推奨事項）"""

_GR_FORMAT_MAPPING = """マークダウン形式で、以下の内容を出力してください：
1. マッピングサマリー（このグループのマッピング評価）
2. マッピング一覧（テーブル形式: 設計書項目、実装ファイル:行、実装要素、確信度、備考）
3. 未マッピング項目（実装箇所が特定できなかった項目）"""

# --- 結果統合（フェーズ3） ---
_INT_ROLE_DEFAULT = "レビュー結果を統合するエキスパート"
_INT_ROLE_MAPPING = "マッピング結果を統合するエキスパート"

_INT_PURPOSE_DEFAULT = (
    "複数のグループレビュー結果を統合し、最終的なレビューレポートを"
    "Markdown形式で生成する"
)
_INT_PURPOSE_MAPPING = (
    "複数のグループマッピング結果を統合し、最終的なマッピングレポートを"
    "Markdown形式で生成する"
)
_INT_PURPOSE_SUFFIX_DEFAULT = (
    "複数のグループに分けてレビューを行いました。"
    "各グループのレビュー結果を統合し、1つの最終的なレビューレポートを生成してください。"
)
_INT_PURPOSE_SUFFIX_MAPPING = (
    "複数のグループに分けてマッピングを行いました。"
    "各グループのマッピング結果を統合し、1つの最終的なマッピングレポートを生成してください。"
)

_INT_FORMAT_DEFAULT = "Markdown形式のレビューレポートを出力してください。"
_INT_FORMAT_MAPPING = (
    "Markdown形式のマッピングレポートを出力してください。"
    "全体のカバレッジ率を含めてください。"
)

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
# ユーティリティ（分割レビュー用）
# ---------------------------------------------------------------------------


def _build_purpose(user_purpose: str | None, suffix: str, fallback: str) -> str:
    """systemPrompt.purposeの有無に応じてpurposeを構築する

    user_purposeがある場合はコードブロックで引用し、suffixを付加する。
    ない場合はfallbackをそのまま返す。
    """
    if user_purpose:
        return (
            "最終的な目的:\n"
            "```\n"
            f"{user_purpose}\n"
            "```\n\n"
            f"{suffix}"
        )
    return fallback


def _estimate_tokens(text: str) -> int:
    """簡易トークン数推定（日本語考慮）"""
    # 日本語は1文字あたり約1.5トークン、英数字は約0.25トークン
    japanese_chars = sum(1 for c in text if ord(c) > 0x3000)
    other_chars = len(text) - japanese_chars
    return int(japanese_chars * 1.5 + other_chars * 0.25)


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

    mode=mapping の場合はマッピング観点でグループ化する。
    """
    try:
        provider = get_llm_provider(request.llmConfig)

        # モード判定
        is_mapping_mode = request.mode == ReviewMode.MAPPING

        # システムプロンプト構築
        sp = request.systemPrompt
        role = (sp.role if sp and sp.role
                else (_SM_ROLE_MAPPING if is_mapping_mode else _SM_ROLE_DEFAULT))
        purpose = _build_purpose(
            sp.purpose if sp else None,
            _SM_PURPOSE_SUFFIX_MAPPING if is_mapping_mode else _SM_PURPOSE_SUFFIX_DEFAULT,
            _SM_PURPOSE_MAPPING if is_mapping_mode else _SM_PURPOSE_DEFAULT,
        )

        output_format = """以下のJSON形式で出力してください:

```json
{
  "groups": [
    {
      "id": "group1",
      "name": "グループの表示名",
      "doc_sections": [
        {
          "id": "MAP.jsonのid値をそのまま使用（例: MD1）",
          "title": "MAP.jsonのtitle値",
          "path": "MAP.jsonのpath値"
        }
      ],
      "code_symbols": [
        {
          "id": "MAP.jsonのid値をそのまま使用（例: CD1）",
          "filename": "MAP.jsonのoriginal_file値",
          "symbol": "MAP.jsonのsymbol値"
        }
      ],
      "reason": "グループ化の理由"
    }
  ]
}
```"""

        # 注意事項の構築
        notes_parts = [
            "- 必ず指定されたJSON形式のみで応答してください",
            "- 設計書の複数セクションと、複数のコード部分が、1つのグループに対応する場合もあります。",
            "- 同じ設計書セクション、コード部分が、複数のグループに対応する場合もあります。",
            "- 文字数の少ないセクション、コードシンボルは、情報が含まれていない可能性があります。他の部分と合わせてグループ化を検討してください。",
            "- 【重要】出力するdoc_sectionsのidは、設計書MAP.jsonに記載されたid値を正確にそのまま使用してください（例: MD1, MD2, ...）",
            "- 【重要】出力するcode_symbolsのidは、コードMAP.jsonに記載されたid値を正確にそのまま使用してください（例: CD1, CD2, ...）",
        ]

        notes = "\n".join(notes_parts)

        system_prompt = build_system_prompt(role, purpose, output_format, notes)

        # ユーザーメッセージ構築（データのみ）
        user_parts = [
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

        # JSON応答パース
        result = _extract_json(response_text)
        groups = []
        for i, g in enumerate(result.get("groups", [])):
            group_id = g.get("id", f"group_{i + 1}")
            group_name = g.get("name", group_id)

            doc_sections = [
                MatchedDocSection(
                    id=ds.get("id", ""),
                    title=ds.get("title", ""),
                    path=ds.get("path", ds.get("title", "")),
                )
                for ds in g.get("doc_sections", [])
            ]

            code_symbols = [
                MatchedCodeSymbol(
                    id=cs.get("id", ""),
                    filename=cs.get("filename", ""),
                    symbol=cs.get("symbol", ""),
                )
                for cs in g.get("code_symbols", [])
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
                    reason=g.get("reason", ""),
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

    mode=mapping の場合はマッピング用プロンプトを使用。
    """
    try:
        provider = get_llm_provider(request.llmConfig)

        # モード判定
        is_mapping_mode = request.mode == ReviewMode.MAPPING

        # システムプロンプト構築
        sp = request.systemPrompt
        role = (sp.role if sp and sp.role
                else (_GR_ROLE_MAPPING if is_mapping_mode else _GR_ROLE_DEFAULT))
        purpose = _build_purpose(
            sp.purpose if sp else None,
            _GR_PURPOSE_SUFFIX_MAPPING if is_mapping_mode else _GR_PURPOSE_SUFFIX_DEFAULT,
            _GR_PURPOSE_MAPPING if is_mapping_mode else _GR_PURPOSE_DEFAULT,
        )
        output_format = (sp.format if sp and sp.format
                         else (_GR_FORMAT_MAPPING if is_mapping_mode else _GR_FORMAT_DEFAULT))

        # 注意事項の構築
        notes_parts = [
            "- 提供されている設計書・コードは元ファイルの一部分であり、完全な情報が含まれていない可能性があります",
            "- 最後に複数グループのレビュー結果を統合するので、統合時への申し送り事項があれば記載してください",
        ]

        # ユーザー指定の注意事項を追加
        if sp and sp.notes:
            notes_parts.extend(["", sp.notes])

        notes = "\n".join(notes_parts)

        system_prompt = build_system_prompt(role, purpose, output_format, notes)

        # 構造マップ情報
        structure_section = ""
        if request.useStructureMap and request.structureMap:
            structure_section = f"""
## 構造マップ（参考情報）
{_build_structure_map_section(request.structureMap)}
"""

        # ユーザーメッセージ構築（データのみ）
        # documentContent, codeContent はフロントエンドで結合済みのテキスト
        user_parts = [
            f"## レビュー対象グループ: {request.groupName}\n",
            f"- グループID: {request.groupId}\n",
        ]

        # 構造マップがある場合は追加
        if structure_section:
            user_parts.append(structure_section)

        user_parts.extend([
            "## 設計書内容\n",
            request.documentContent,
            "\n## コード内容\n",
            request.codeContent,
        ])

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
        return GroupReviewResponse(
            success=False,
            groupId=request.groupId,
            error=str(e),
        )
    except Exception as e:
        return GroupReviewResponse(
            success=False,
            groupId=request.groupId,
            error=f"グループレビュー中にエラーが発生しました: {str(e)}",
        )


@router.post("/review/integrate", response_model=IntegrateResponse)
async def integrate_reviews(request: IntegrateRequest):
    """
    結果統合（フェーズ3）

    全グループのレビュー結果を統合し、最終レポートを生成する。
    システムプロンプト設定に基づいて、AIがMarkdown形式のレビューレポートを生成する。

    mode=mapping の場合はマッピング結果を統合する。
    """
    try:
        provider = get_llm_provider(request.llmConfig)

        # モード判定
        is_mapping_mode = request.mode == ReviewMode.MAPPING

        # システムプロンプト構築
        sp = request.systemPrompt
        role = (sp.role if sp and sp.role
                else (_INT_ROLE_MAPPING if is_mapping_mode else _INT_ROLE_DEFAULT))
        purpose = _build_purpose(
            sp.purpose if sp else None,
            _INT_PURPOSE_SUFFIX_MAPPING if is_mapping_mode else _INT_PURPOSE_SUFFIX_DEFAULT,
            _INT_PURPOSE_MAPPING if is_mapping_mode else _INT_PURPOSE_DEFAULT,
        )
        output_format = (sp.format if sp and sp.format
                         else (_INT_FORMAT_MAPPING if is_mapping_mode else _INT_FORMAT_DEFAULT))

        # 注意事項の構築
        notes_parts = [
            "- 各グループの結果を統合し、重複を排除してください",
            "- グループ分けは参考に止め、元々の設計書、コードの記載、構造を尊重してください。",
            "- 出力形式の指定に従い、全体を一括実行した場合と同様になるよう出力してください。",
            "- マッチング処理やグループレビューで統合実行用に付与された付加情報は、レポートに含めないでください。",
        ]

        # ユーザー指定の注意事項を追加
        if sp and sp.notes:
            notes_parts.extend(["", sp.notes])

        notes = "\n".join(notes_parts)

        system_prompt = build_system_prompt(role, purpose, output_format, notes)

        # ユーザーメッセージ構築（データのみ）
        user_parts = []

        # 構造マップ情報（全体）
        if request.useStructureMap and request.structureMap:
            user_parts.extend([
                "## 全体構造マップ（参考情報）\n",
                _build_structure_map_section(request.structureMap),
                "\n",
            ])

        # 構造マッチング結果
        user_parts.extend([
            "## 構造マッチング結果\n",
            "```json",
            json.dumps(
                request.structureMatching, ensure_ascii=False, indent=2
            ),
            "```\n",
        ])

        # グループレビュー結果
        result_label = "グループマッピング結果" if is_mapping_mode else "グループレビュー結果"
        user_parts.append(f"## {result_label}\n")
        for gr in request.groupReviews:
            user_parts.extend([
                f"### {gr.groupName} ({gr.groupId})\n",
                gr.report if gr.report else f"**サマリー**: {gr.summary}\n",
                "",
            ])

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
            designs=[],  # 分割レビューでは構造マッチング結果に含まれる
            codes=[],    # 分割レビューでは構造マッチング結果に含まれる
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        review_meta = ReviewMeta(**review_meta_dict)

        return IntegrateResponse(
            success=True,
            report=response_text,
            rawOutput=response_text,
            integratedReport=integrated_report,
            reviewMeta=review_meta,
            tokensUsed={"input": input_tokens, "output": output_tokens},
        )

    except RuntimeError as e:
        return IntegrateResponse(
            success=False,
            error=str(e),
        )
    except Exception as e:
        return IntegrateResponse(
            success=False,
            error=f"結果統合中にエラーが発生しました: {str(e)}",
        )
