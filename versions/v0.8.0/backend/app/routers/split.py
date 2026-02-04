"""分割API (v0.8.0)

セマンティック分割機能のAPIエンドポイント。
Phase 2ではスタブ実装（ダミーデータを返す）。
"""

import uuid

from fastapi import APIRouter

from app.models.schemas import (
    SplitMarkdownRequest,
    SplitMarkdownResponse,
    SplitCodeRequest,
    SplitCodeResponse,
    PartsReviewRequest,
    PartsReviewResponse,
    PartsReviewProgress,
    DocumentPart,
    CodePart,
    ReviewMeta,
    DesignMeta,
    ProgramMeta,
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
    - maxDepthで分割深度を指定（デフォルト: H2まで）

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


@router.post("/review/parts", response_model=PartsReviewResponse)
async def review_parts(request: PartsReviewRequest):
    """
    分割されたパーツに対してレビューを実行する

    - フェーズ1: 構造マッチング（設計書INDEX + コードINDEX）
    - フェーズ2: ペアレビュー（関連するパーツ同士）
    - フェーズ3: 統合（全結果をまとめる）

    【Phase 2: スタブ実装】
    実際のレビューロジックは Phase 3 で実装。
    """
    session_id = str(uuid.uuid4())

    # スタブ: ダミーのレビュー結果を返す
    doc_count = len(request.documentParts) if request.documentParts else 0
    code_count = len(request.codeParts) if request.codeParts else 0

    report = f"""# 分割レビュー結果（スタブ）

## 概要

- 設計書パーツ数: {doc_count}
- コードパーツ数: {code_count}
- レビューモード: 分割レビュー

## フェーズ1: 構造マッチング結果

設計書とコードの構造を分析し、以下のペアリングを特定しました。

| 設計書セクション | 関連コード | 関連度 |
|------------------|------------|--------|
| 概要 | - | - |
| 機能要件 | UserService | 高 |
| 画面設計 | - | - |
| API設計 | UserService | 高 |
| データベース設計 | - | 中 |

## フェーズ2: ペアレビュー結果

### ペア1: 機能要件 × UserService

**整合性**: ✅ 良好

設計書の機能要件とUserServiceの実装は概ね整合しています。

**指摘事項**:
- L45-80: createUserメソッドにバリデーション処理が不足している可能性があります

### ペア2: API設計 × UserService

**整合性**: ⚠️ 要確認

**指摘事項**:
- L122-150: deleteUserメソッドの戻り値が設計書と異なる可能性があります

## フェーズ3: 統合サマリー

| 項目 | 結果 |
|------|------|
| 総合判定 | ⚠️ 軽微な不整合あり |
| 重大な問題 | 0件 |
| 要確認事項 | 2件 |
| 推奨事項 | 1件 |
"""

    review_meta = ReviewMeta(
        version="0.8.0",
        modelId="stub-model",
        provider="stub",
        executedAt=request.executedAt or "2026-02-04T12:00:00Z",
        designs=[
            DesignMeta(
                filename="design.md",
                role="メイン設計書",
                isMain=True,
                type="詳細設計書",
                tool="stub",
            )
        ],
        programs=[ProgramMeta(filename="UserService.java")],
        inputTokens=35000,
        outputTokens=2000,
    )

    return PartsReviewResponse(
        success=True,
        sessionId=session_id,
        report=report,
        reviewMeta=review_meta,
    )


@router.get("/review/parts/{session_id}/status", response_model=PartsReviewProgress)
async def get_parts_review_status(session_id: str):
    """
    分割レビューの進捗状況を取得する

    【Phase 2: スタブ実装】
    実際の進捗管理は Phase 3 で実装。
    """
    # スタブ: 完了状態を返す
    return PartsReviewProgress(
        sessionId=session_id,
        status="completed",
        totalPhases=3,
        currentPhase=3,
        phaseName="統合",
        totalPairs=5,
        completedPairs=5,
        partialResults=[],
    )
