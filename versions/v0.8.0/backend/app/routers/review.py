"""レビューAPI"""

import json
import re
from importlib.metadata import version

from fastapi import APIRouter

from app.models.schemas import (
    LLMConfig,
    ReviewRequest,
    ReviewResponse,
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
    """
    try:
        provider = get_llm_provider(request.llmConfig)

        system_prompt = (
            "あなたは設計書とソースコードの構造を分析する専門家です。\n"
            "設計書の構造（セクション一覧）とコードの構造（シンボル一覧）を比較し、\n"
            "関連性の高い設計書セクションとコードシンボルをグループにまとめてください。\n"
            "必ず指定されたJSON形式のみで応答してください。\n\n"
            "【重要】出力するdoc_sectionsのidは、設計書MAP.jsonに記載された"
            "id値を正確にそのまま使用してください（例: MD1, MD2, ...）。\n"
            "【重要】出力するcode_symbolsのidは、コードMAP.jsonに記載された"
            "id値を正確にそのまま使用してください（例: CD1, CD2, ...）。"
        )

        # ユーザーメッセージ構築
        user_parts = [
            "# 構造マッチング依頼\n",
            "以下の設計書構造とコード構造を比較し、関連性の高いグループを特定してください。",
            "設計書の複数セクションと、複数のコード部分が対応する場合もあります。\n",
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

        user_parts.extend([
            "\n## 出力形式\n",
            "以下のJSON形式で出力してください:",
            "",
            "**注意**: doc_sectionsのidは設計書MAP.jsonのid値を、"
            "code_symbolsのidはコードMAP.jsonのid値を、"
            "正確にそのまま使用してください（後工程でのマッチングに使用されます）。\n",
            "```json",
            json.dumps(
                {
                    "groups": [
                        {
                            "id": "group1",
                            "name": "グループの表示名",
                            "doc_sections": [
                                {
                                    "id": "MAP.jsonのid値をそのまま使用（例: MD1）",
                                    "title": "MAP.jsonのtitle値",
                                    "path": "MAP.jsonのpath値",
                                }
                            ],
                            "code_symbols": [
                                {
                                    "id": "MAP.jsonのid値をそのまま使用（例: CD1）",
                                    "filename": "MAP.jsonのoriginal_file値",
                                    "symbol": "MAP.jsonのsymbol値",
                                }
                            ],
                            "reason": "グループ化の理由",
                        }
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            "```",
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

        system_prompt = (
            "あなたは設計書とソースコードの整合性をレビューする専門家です。\n"
            "設計書の記述とコード実装の整合性を確認し、指摘事項を報告してください。\n"
            "必ず指定されたJSON形式のみで応答してください。"
        )

        # ユーザーメッセージ構築
        user_parts = [
            "# レビュー依頼\n",
            "以下の設計書セクションとコードの整合性をレビューしてください。\n",
            f"## レビュー対象グループ: {request.groupName}\n",
            f"- グループID: {request.groupId}",
            f"- 設計書セクション: {', '.join(p.title for p in request.documentParts)}",
            f"- 対応コード: {', '.join(p.symbol for p in request.codeParts)}\n",
        ]

        # 設計書内容
        user_parts.append("## 設計書内容\n")
        for part in request.documentParts:
            user_parts.extend([
                f"### {part.title} (L{part.startLine}-L{part.endLine})\n",
                part.content,
                "",
            ])

        # コード内容
        user_parts.append("## コード内容\n")
        for part in request.codeParts:
            user_parts.extend([
                f"### {part.filename}:{part.symbol} ({part.symbolType}, L{part.startLine}-L{part.endLine})\n",
                f"```\n{part.content}\n```\n",
            ])

        # レビュー観点
        user_parts.extend([
            "## レビュー観点\n",
            "1. 設計書の記述とコード実装の整合性",
            "2. 設計書に記載があるがコードに実装されていない機能",
            "3. コードに実装があるが設計書に記載がない機能",
            "4. 命名の一貫性",
            "5. その他の懸念事項\n",
        ])

        # 出力形式
        user_parts.extend([
            "## 出力形式\n",
            "以下のJSON形式で出力してください:",
            "```json",
            json.dumps(
                {
                    "summary": "全体的な整合性の評価",
                    "findings": [
                        {
                            "id": "F001",
                            "type": "inconsistency|missing_in_code|missing_in_doc|suggestion",
                            "severity": "error|warning|info",
                            "doc_location": {
                                "section": "セクション名",
                                "line": 25,
                            },
                            "code_location": {
                                "filename": "ファイル名",
                                "symbol": "シンボル名",
                                "line": 45,
                            },
                            "description": "指摘内容",
                            "recommendation": "推奨対応",
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            "```",
            "\n指摘がない場合はfindingsを空配列にしてください。",
        ])

        user_message = "\n".join(user_parts)

        # LLM呼び出し
        response_text, input_tokens, output_tokens = provider.send_message(
            system_prompt, user_message
        )

        # JSON応答パース
        result = _extract_json(response_text)

        findings = []
        for f in result.get("findings", []):
            findings.append(
                ReviewFinding(
                    id=f.get("id", ""),
                    findingType=f.get("type", "suggestion"),
                    severity=f.get("severity", "info"),
                    docLocation=f.get("doc_location"),
                    codeLocation=f.get("code_location"),
                    description=f.get("description", ""),
                    recommendation=f.get("recommendation", ""),
                )
            )

        review_result = GroupReviewResult(
            summary=result.get("summary", ""),
            findings=findings,
            statistics={
                "totalFindings": len(findings),
                "errors": sum(
                    1 for f in findings if f.severity == "error"
                ),
                "warnings": sum(
                    1 for f in findings if f.severity == "warning"
                ),
                "info": sum(
                    1 for f in findings if f.severity == "info"
                ),
            },
        )

        return GroupReviewResponse(
            success=True,
            groupId=request.groupId,
            reviewResult=review_result,
            tokensUsed={"input": input_tokens, "output": output_tokens},
        )

    except json.JSONDecodeError as e:
        return GroupReviewResponse(
            success=False,
            groupId=request.groupId,
            error=f"AIの応答をJSONとして解析できませんでした: {str(e)}",
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
    """
    try:
        provider = get_llm_provider(request.llmConfig)

        system_prompt = (
            "あなたはレビュー結果を統合するエキスパートです。\n"
            "複数のグループレビュー結果を統合し、最終的なレビューレポートを"
            "Markdown形式で生成してください。"
        )

        # ユーザーメッセージ構築
        user_parts = [
            "# レビュー結果統合依頼\n",
            "以下のグループレビュー結果を統合し、最終レポートを生成してください。\n",
        ]

        # システムプロンプト設定（注意事項・出力フォーマット）
        if request.systemPrompt:
            user_parts.extend([
                "## システムプロンプト設定\n",
                "以下の注意事項・出力フォーマットに従ってレポートを作成してください:\n",
                request.systemPrompt,
                "",
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
        user_parts.append("## グループレビュー結果\n")
        for gr in request.groupReviews:
            user_parts.extend([
                f"### {gr.groupName} ({gr.groupId})\n",
                f"**サマリー**: {gr.summary}\n",
            ])
            if gr.findings:
                user_parts.append("**指摘事項**:\n")
                for f in gr.findings:
                    user_parts.append(
                        f"- [{f.severity}] {f.id}: {f.description}"
                    )
                user_parts.append("")

        # 統合指示
        user_parts.extend([
            "## 統合指示\n",
            "1. 各グループのレビュー結果を統合し、重複する指摘を排除してください",
            "2. グループ間にまたがる問題があれば特定してください",
            "3. 全体的な整合性評価を記述してください",
        ])

        if request.systemPrompt:
            user_parts.append(
                "4. システムプロンプト設定に記載された出力フォーマットに"
                "従って最終レポートを生成してください"
            )

        user_parts.extend([
            "\n## 出力\n",
            "Markdown形式のレビューレポートを出力してください。",
        ])

        user_message = "\n".join(user_parts)

        # LLM呼び出し
        response_text, input_tokens, output_tokens = provider.send_message(
            system_prompt, user_message
        )

        # 統計情報をグループレビュー結果から集計
        total_findings = sum(
            len(gr.findings) for gr in request.groupReviews
        )
        total_errors = sum(
            sum(1 for f in gr.findings if f.severity == "error")
            for gr in request.groupReviews
        )
        total_warnings = sum(
            sum(1 for f in gr.findings if f.severity == "warning")
            for gr in request.groupReviews
        )
        total_info = sum(
            sum(1 for f in gr.findings if f.severity == "info")
            for gr in request.groupReviews
        )

        # IntegratedReport構築
        # 重複指摘の検出
        seen_descriptions = set()
        deduplicated = []
        for gr in request.groupReviews:
            for f in gr.findings:
                if f.description not in seen_descriptions:
                    seen_descriptions.add(f.description)
                else:
                    deduplicated.append(f.id)

        integrated_report = IntegratedReport(
            overallSummary=f"レビュー対象: {len(request.groupReviews)}グループ, "
            f"総指摘件数: {total_findings}件",
            consistencyScore=0.0,  # AIレポートから抽出可能だが、簡易実装
            keyIssues=[],
            crossGroupIssues=[],
            statistics={
                "totalGroupsReviewed": len(request.groupReviews),
                "totalFindings": total_findings,
                "bySeverity": {
                    "error": total_errors,
                    "warning": total_warnings,
                    "info": total_info,
                },
            },
            deduplicatedFindings=deduplicated,
        )

        return IntegrateResponse(
            success=True,
            report=response_text,
            integratedReport=integrated_report,
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
