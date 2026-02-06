"""分割API (v0.8.0)

セマンティック分割機能のAPIエンドポイント。
md2map / code2map ライブラリを使用してファイルを分割し、
LLMを使用して構造マッチング・グループレビュー・結果統合を行う。
"""

import json
import os
import re
import tempfile

from fastapi import APIRouter

from app.models.schemas import (
    SplitMarkdownRequest,
    SplitMarkdownResponse,
    SplitCodeRequest,
    SplitCodeResponse,
    DocumentPart,
    CodePart,
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
    KeyIssue,
)
from app.services.llm_service import get_llm_provider

router = APIRouter()


# ---------------------------------------------------------------------------
# ユーティリティ
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
# 分割API
# ---------------------------------------------------------------------------


@router.post("/split/markdown", response_model=SplitMarkdownResponse)
async def split_markdown(request: SplitMarkdownRequest):
    """
    Markdownをセクション単位で分割する（md2map使用）

    - 見出し（H1-H6）を基準に分割
    - maxDepthで分割の見出しレベルを指定（デフォルト: H2まで）
    """
    try:
        from md2map.generators.index_generator import (
            generate_index as md2map_generate_index,
        )
        from md2map.generators.parts_generator import (
            generate_parts as md2map_generate_parts,
        )
        from md2map.parsers.markdown_parser import MarkdownParser
        from md2map.utils.file_utils import read_file as md2map_read_file

        with tempfile.TemporaryDirectory() as tmpdir:
            # 入力ファイルを書き込み
            input_path = os.path.join(tmpdir, request.filename or "input.md")
            with open(input_path, "w", encoding="utf-8") as f:
                f.write(request.content)

            # パース
            parser = MarkdownParser()
            sections, warnings = parser.parse(input_path, request.maxDepth)

            if not sections:
                return SplitMarkdownResponse(
                    success=True,
                    parts=[],
                    indexContent="# No sections found\n",
                )

            # 行を読み込み（md2mapはkeepends=Trueの行リストを返す）
            lines, _ = md2map_read_file(input_path)
            if lines is None:
                return SplitMarkdownResponse(
                    success=False,
                    error="ファイルの読み込みに失敗しました",
                )

            # パーツ生成（section.part_fileを設定するために必要）
            out_dir = os.path.join(tmpdir, "output")
            md2map_generate_parts(sections, lines, out_dir)

            # INDEX.md生成
            index_path = os.path.join(out_dir, "INDEX.md")
            md2map_generate_index(
                sections, warnings, index_path, request.filename
            )

            # INDEX.md読み取り
            with open(index_path, "r", encoding="utf-8") as f:
                index_content = f.read()

            # DocumentPartリスト構築
            parts = []
            for section in sections:
                content = "".join(
                    lines[section.start_line - 1 : section.end_line]
                )
                parts.append(
                    DocumentPart(
                        section=section.title,
                        level=section.level,
                        path=section.path,
                        startLine=section.start_line,
                        endLine=section.end_line,
                        content=content,
                        estimatedTokens=_estimate_tokens(content),
                    )
                )

        return SplitMarkdownResponse(
            success=True,
            parts=parts,
            indexContent=index_content,
        )

    except Exception as e:
        return SplitMarkdownResponse(
            success=False,
            error=f"Markdown分割中にエラーが発生しました: {str(e)}",
        )


@router.post("/split/code", response_model=SplitCodeResponse)
async def split_code(request: SplitCodeRequest):
    """
    コードをクラス・メソッド・関数単位で分割する（code2map使用）

    - ファイル拡張子から言語を自動判定
    - 対応言語: Python (.py), Java (.java)
    """
    # 言語判定
    ext = (
        request.filename.lower().split(".")[-1]
        if "." in request.filename
        else ""
    )
    language = {"py": "python", "java": "java"}.get(ext)

    if not language:
        return SplitCodeResponse(
            success=False,
            error=f"未対応の言語です: .{ext} (対応: .py, .java)",
        )

    try:
        from code2map.generators.index_generator import (
            generate_index as code2map_generate_index,
        )
        from code2map.generators.parts_generator import (
            generate_parts as code2map_generate_parts,
        )
        from code2map.utils.file_utils import (
            read_lines as code2map_read_lines,
            slice_lines,
        )

        if language == "python":
            from code2map.parsers.python_parser import PythonParser

            code_parser = PythonParser()
        else:
            from code2map.parsers.java_parser import JavaParser

            code_parser = JavaParser()

        with tempfile.TemporaryDirectory() as tmpdir:
            # 入力ファイルを書き込み
            input_path = os.path.join(tmpdir, request.filename)
            with open(input_path, "w", encoding="utf-8") as f:
                f.write(request.content)

            # パース
            symbols, warnings = code_parser.parse(input_path)

            if not symbols:
                return SplitCodeResponse(
                    success=True,
                    parts=[],
                    indexContent="# No symbols found\n",
                    language=language,
                )

            # 行を読み込み（code2mapはsplitlines()の行リストを返す）
            c2m_lines = code2map_read_lines(input_path)

            # パーツ生成（symbol.part_fileを設定するために必要）
            out_dir = os.path.join(tmpdir, "output")
            code2map_generate_parts(symbols, c2m_lines, out_dir)

            # INDEX.md生成
            index_path = os.path.join(out_dir, "INDEX.md")
            code2map_generate_index(
                symbols, warnings, c2m_lines, index_path, request.filename
            )

            # INDEX.md読み取り
            with open(index_path, "r", encoding="utf-8") as f:
                index_content = f.read()

            # CodePartリスト構築
            parts = []
            for symbol in symbols:
                content = slice_lines(
                    c2m_lines, symbol.start_line, symbol.end_line
                )
                parts.append(
                    CodePart(
                        symbol=symbol.name,
                        symbolType=symbol.kind,
                        parentSymbol=symbol.parent,
                        startLine=symbol.start_line,
                        endLine=symbol.end_line,
                        content=content,
                        estimatedTokens=_estimate_tokens(content),
                    )
                )

        return SplitCodeResponse(
            success=True,
            parts=parts,
            indexContent=index_content,
            language=language,
        )

    except Exception as e:
        return SplitCodeResponse(
            success=False,
            error=f"コード分割中にエラーが発生しました: {str(e)}",
        )


# ---------------------------------------------------------------------------
# レビューAPI
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
            "【重要】出力するdoc_sectionsのtitleとpathは、設計書MAP.jsonに記載された"
            "titleとpathの値を正確にそのまま使用してください。\n"
            "【重要】出力するcode_symbolsのfilenameとsymbolは、コードMAP.jsonに記載された"
            "original_fileとsymbolの値を正確にそのまま使用してください。"
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
            "**注意**: doc_sectionsのtitle/pathは設計書MAP.jsonの値を、"
            "code_symbolsのfilename/symbolはコードMAP.jsonの値を、"
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
                                    "title": "MAP.jsonのtitle値をそのまま使用",
                                    "path": "MAP.jsonのpath値をそのまま使用",
                                }
                            ],
                            "code_symbols": [
                                {
                                    "filename": "MAP.jsonのoriginal_file値をそのまま使用",
                                    "symbol": "MAP.jsonのsymbol値をそのまま使用",
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
                    title=ds.get("title", ""),
                    path=ds.get("path", ds.get("title", "")),
                )
                for ds in g.get("doc_sections", [])
            ]

            code_symbols = [
                MatchedCodeSymbol(
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
