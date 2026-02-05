"""分割API (v0.8.0)

セマンティック分割機能のAPIエンドポイント。
Phase 2ではスタブ実装（ダミーデータを返す）。
"""

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

router = APIRouter()


def _estimate_tokens(text: str) -> int:
    """簡易トークン数推定（日本語考慮）"""
    # 日本語は1文字あたり約1.5トークン、英数字は約0.25トークン
    japanese_chars = sum(1 for c in text if ord(c) > 0x3000)
    other_chars = len(text) - japanese_chars
    return int(japanese_chars * 1.5 + other_chars * 0.25)


@router.post("/split/markdown", response_model=SplitMarkdownResponse)
async def split_markdown(request: SplitMarkdownRequest):
    """
    Markdownをセクション単位で分割する（md2map相当）

    - 見出し（H1-H6）を基準に分割
    - maxDepthで分割の見出しレベルを指定（デフォルト: H2まで）

    【Phase 2: スタブ実装】
    実際のmd2map呼び出しは Phase 3 で実装。
    """
    # スタブ: ダミーの分割結果を返す
    dummy_parts = [
        DocumentPart(
            section="概要",
            level=2,
            path="概要",
            startLine=1,
            endLine=50,
            content="# 概要\n\nこのドキュメントは...",
            estimatedTokens=2000,
        ),
        DocumentPart(
            section="機能要件",
            level=2,
            path="機能要件",
            startLine=51,
            endLine=200,
            content="# 機能要件\n\n## ユーザー管理\n...",
            estimatedTokens=8000,
        ),
        DocumentPart(
            section="画面設計",
            level=2,
            path="画面設計",
            startLine=201,
            endLine=450,
            content="# 画面設計\n\n## ログイン画面\n...",
            estimatedTokens=12000,
        ),
        DocumentPart(
            section="API設計",
            level=2,
            path="API設計",
            startLine=451,
            endLine=600,
            content="# API設計\n\n## エンドポイント一覧\n...",
            estimatedTokens=7000,
        ),
        DocumentPart(
            section="データベース設計",
            level=2,
            path="データベース設計",
            startLine=601,
            endLine=750,
            content="# データベース設計\n\n## ER図\n...",
            estimatedTokens=6000,
        ),
    ]

    index_content = f"""# Index: {request.filename}

## Structure Tree

- {request.filename}
  - 概要 (L1-L50)
  - 機能要件 (L51-L200)
  - 画面設計 (L201-L450)
  - API設計 (L451-L600)
  - データベース設計 (L601-L750)

## Section Summary

| # | Section | Lines | Est. Tokens |
|---|---------|-------|-------------|
| 1 | 概要 | L1-L50 | ~2,000 |
| 2 | 機能要件 | L51-L200 | ~8,000 |
| 3 | 画面設計 | L201-L450 | ~12,000 |
| 4 | API設計 | L451-L600 | ~7,000 |
| 5 | データベース設計 | L601-L750 | ~6,000 |
"""

    return SplitMarkdownResponse(
        success=True,
        parts=dummy_parts,
        indexContent=index_content,
    )


@router.post("/split/code", response_model=SplitCodeResponse)
async def split_code(request: SplitCodeRequest):
    """
    コードをクラス・メソッド・関数単位で分割する（code2map相当）

    - ファイル拡張子から言語を自動判定
    - 対応言語: Python (.py), Java (.java)

    【Phase 2: スタブ実装】
    実際のcode2map呼び出しは Phase 3 で実装。
    """
    # 言語判定
    ext = request.filename.lower().split(".")[-1] if "." in request.filename else ""
    language = {"py": "python", "java": "java"}.get(ext)

    if not language:
        return SplitCodeResponse(
            success=False,
            error=f"未対応の言語です: .{ext} (対応: .py, .java)",
        )

    # スタブ: ダミーの分割結果を返す
    if language == "java":
        dummy_parts = [
            CodePart(
                symbol="UserService",
                symbolType="class",
                parentSymbol=None,
                startLine=1,
                endLine=250,
                content="public class UserService {\n    // ...\n}",
                estimatedTokens=5000,
            ),
            CodePart(
                symbol="createUser",
                symbolType="method",
                parentSymbol="UserService",
                startLine=45,
                endLine=80,
                content="public User createUser(String name) {\n    // ...\n}",
                estimatedTokens=1500,
            ),
            CodePart(
                symbol="updateUser",
                symbolType="method",
                parentSymbol="UserService",
                startLine=82,
                endLine=120,
                content="public User updateUser(Long id, String name) {\n    // ...\n}",
                estimatedTokens=1600,
            ),
            CodePart(
                symbol="deleteUser",
                symbolType="method",
                parentSymbol="UserService",
                startLine=122,
                endLine=150,
                content="public void deleteUser(Long id) {\n    // ...\n}",
                estimatedTokens=1200,
            ),
            CodePart(
                symbol="findById",
                symbolType="method",
                parentSymbol="UserService",
                startLine=152,
                endLine=180,
                content="public User findById(Long id) {\n    // ...\n}",
                estimatedTokens=1200,
            ),
        ]
    else:  # python
        dummy_parts = [
            CodePart(
                symbol="UserManager",
                symbolType="class",
                parentSymbol=None,
                startLine=10,
                endLine=150,
                content="class UserManager:\n    # ...",
                estimatedTokens=4000,
            ),
            CodePart(
                symbol="create_user",
                symbolType="method",
                parentSymbol="UserManager",
                startLine=25,
                endLine=50,
                content="def create_user(self, name: str) -> User:\n    # ...",
                estimatedTokens=1200,
            ),
            CodePart(
                symbol="update_user",
                symbolType="method",
                parentSymbol="UserManager",
                startLine=52,
                endLine=80,
                content="def update_user(self, user_id: int, name: str) -> User:\n    # ...",
                estimatedTokens=1300,
            ),
        ]

    index_content = f"""# Index: {request.filename}

## Language: {language.title()}

## Symbols

| # | Symbol | Type | Lines | Est. Tokens |
|---|--------|------|-------|-------------|
"""
    for i, part in enumerate(dummy_parts, 1):
        parent = f" ({part.parentSymbol})" if part.parentSymbol else ""
        index_content += f"| {i} | {part.symbol}{parent} | {part.symbolType} | L{part.startLine}-L{part.endLine} | ~{part.estimatedTokens:,} |\n"

    return SplitCodeResponse(
        success=True,
        parts=dummy_parts,
        indexContent=index_content,
        language=language,
    )


@router.post("/review/structure-matching", response_model=StructureMatchingResponse)
async def structure_matching(request: StructureMatchingRequest):
    """
    構造マッチング（フェーズ1）

    設計書とコードの構造を比較し、関連性の高いグループを特定する。

    【Phase 2: スタブ実装】
    実際のLLM呼び出しは Phase 3 で実装。
    """
    # スタブ: ダミーのグループ情報を返す
    dummy_groups = [
        MatchedGroup(
            groupId="group_1",
            groupName="ユーザー管理",
            docSections=[
                MatchedDocSection(title="機能要件", path="機能要件"),
                MatchedDocSection(title="ユーザー管理", path="機能要件 > ユーザー管理"),
            ],
            codeSymbols=[
                MatchedCodeSymbol(filename="UserService.java", symbol="UserService"),
                MatchedCodeSymbol(filename="UserService.java", symbol="createUser"),
                MatchedCodeSymbol(filename="UserService.java", symbol="updateUser"),
            ],
            reason="ユーザー管理に関連する設計とコード",
            estimatedTokens=8500,
        ),
        MatchedGroup(
            groupId="group_2",
            groupName="API設計",
            docSections=[
                MatchedDocSection(title="API設計", path="API設計"),
            ],
            codeSymbols=[
                MatchedCodeSymbol(filename="UserService.java", symbol="deleteUser"),
                MatchedCodeSymbol(filename="UserService.java", symbol="findById"),
            ],
            reason="API仕様とエンドポイント実装",
            estimatedTokens=5200,
        ),
        MatchedGroup(
            groupId="group_3",
            groupName="データベース設計",
            docSections=[
                MatchedDocSection(title="データベース設計", path="データベース設計"),
            ],
            codeSymbols=[],
            reason="データベース設計（対応コードなし）",
            estimatedTokens=3000,
        ),
    ]

    return StructureMatchingResponse(
        success=True,
        groups=dummy_groups,
        totalGroups=len(dummy_groups),
    )


@router.post("/review/group", response_model=GroupReviewResponse)
async def review_group(request: GroupReviewRequest):
    """
    グループレビュー（フェーズ2）

    1グループ（関連する設計書パーツ + コードパーツ）をレビューする。

    【Phase 2: スタブ実装】
    実際のLLM呼び出しは Phase 3 で実装。
    """
    # スタブ: ダミーのレビュー結果を返す
    doc_titles = [p.title for p in request.documentParts]
    code_symbols = [p.symbol for p in request.codeParts]

    dummy_findings = []

    # グループに応じたダミー指摘を生成
    if request.groupId == "group_1":
        dummy_findings = [
            ReviewFinding(
                id="F001",
                findingType="inconsistency",
                severity="warning",
                docLocation={"section": "ユーザー管理", "line": 165},
                codeLocation={"filename": "UserService.java", "symbol": "createUser", "line": 25},
                description="設計書では「メールアドレスは必須」と記載されているが、コードではnull許容になっている",
                recommendation="コードにメールアドレスの必須チェックを追加するか、設計書を修正する",
            ),
            ReviewFinding(
                id="F002",
                findingType="missing_in_code",
                severity="error",
                docLocation={"section": "機能要件", "line": 78},
                codeLocation=None,
                description="設計書に記載の「パスワード強度チェック」がコードに実装されていない",
                recommendation="PasswordValidatorクラスを作成し、createUserメソッドから呼び出す",
            ),
        ]
        summary = "設計書とコードは概ね整合しているが、バリデーション仕様に差異あり"
    elif request.groupId == "group_2":
        dummy_findings = [
            ReviewFinding(
                id="F003",
                findingType="inconsistency",
                severity="warning",
                docLocation={"section": "API設計", "line": 45},
                codeLocation={"filename": "UserService.java", "symbol": "deleteUser", "line": 122},
                description="設計書ではDELETEメソッドの戻り値は204だが、コードでは200を返している",
                recommendation="HTTPステータスコードを設計書に合わせて修正する",
            ),
        ]
        summary = "APIの仕様とコードは概ね整合しているが、ステータスコードに差異あり"
    else:
        summary = "対応するコードがないため、設計書のみの確認となります"

    result = GroupReviewResult(
        summary=summary,
        findings=dummy_findings,
        statistics={
            "totalFindings": len(dummy_findings),
            "errors": sum(1 for f in dummy_findings if f.severity == "error"),
            "warnings": sum(1 for f in dummy_findings if f.severity == "warning"),
            "info": sum(1 for f in dummy_findings if f.severity == "info"),
        },
    )

    return GroupReviewResponse(
        success=True,
        groupId=request.groupId,
        reviewResult=result,
        tokensUsed={"input": 6500, "output": 1200},
    )


@router.post("/review/integrate", response_model=IntegrateResponse)
async def integrate_reviews(request: IntegrateRequest):
    """
    結果統合（フェーズ3）

    全グループのレビュー結果を統合し、最終レポートを生成する。
    システムプロンプト設定に基づいて、AIがMarkdown形式のレビューレポートを生成する。

    【Phase 2: スタブ実装】
    実際のLLM呼び出しは Phase 3 で実装。
    """
    # スタブ: ダミーの統合レポートを返す
    total_findings = sum(len(gr.findings) for gr in request.groupReviews)
    total_errors = sum(
        sum(1 for f in gr.findings if f.severity == "error")
        for gr in request.groupReviews
    )
    total_warnings = sum(
        sum(1 for f in gr.findings if f.severity == "warning")
        for gr in request.groupReviews
    )

    integrated_report = IntegratedReport(
        overallSummary=f"全体として設計書とコードの整合性は良好（適合率78%）。主要な課題はバリデーション仕様の不一致。レビュー対象: {len(request.groupReviews)}グループ",
        consistencyScore=0.78,
        keyIssues=[
            KeyIssue(
                priority=1,
                title="バリデーション仕様の不一致",
                affectedGroups=["group_1"],
                description="ユーザー登録時のバリデーションが設計書とコードで異なる",
                relatedFindings=["F001", "F002"],
            ),
            KeyIssue(
                priority=2,
                title="HTTPステータスコードの不整合",
                affectedGroups=["group_2"],
                description="API設計書と実装でステータスコードが異なる",
                relatedFindings=["F003"],
            ),
        ],
        crossGroupIssues=[],
        statistics={
            "totalGroupsReviewed": len(request.groupReviews),
            "totalFindings": total_findings,
            "bySeverity": {
                "error": total_errors,
                "warning": total_warnings,
                "info": 0,
            },
        },
        deduplicatedFindings=[],
    )

    # AIが生成するMarkdownレポート（スタブ）
    markdown_report = f"""# 設計書-コード整合性レビュー結果

## 1. 全体サマリー

{integrated_report.overallSummary}

**整合性スコア**: {integrated_report.consistencyScore * 100:.0f}%

## 2. 重要な課題

"""
    for issue in integrated_report.keyIssues:
        markdown_report += f"""### 優先度{issue.priority}: {issue.title}

- **影響グループ**: {', '.join(issue.affectedGroups)}
- **説明**: {issue.description}
- **関連指摘**: {', '.join(issue.relatedFindings)}

"""

    markdown_report += f"""## 3. 指摘事項一覧

| ID | 種別 | 重要度 | 説明 |
|----|------|--------|------|
"""
    for gr in request.groupReviews:
        for finding in gr.findings:
            markdown_report += f"| {finding.id} | {finding.findingType} | {finding.severity} | {finding.description} |\n"

    markdown_report += f"""
## 4. 統計情報

- **レビュー対象グループ数**: {len(request.groupReviews)}
- **総指摘件数**: {total_findings}
  - エラー: {total_errors}
  - 警告: {total_warnings}
  - 情報: 0
"""

    return IntegrateResponse(
        success=True,
        report=markdown_report,
        integratedReport=integrated_report,
        tokensUsed={"input": 4500, "output": 2000},
    )
