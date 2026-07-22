"""Pydantic スキーマ定義"""

from typing import Literal

from pydantic import BaseModel, Field, AliasChoices, ConfigDict, model_validator


class ConvertResponse(BaseModel):
    """変換APIのレスポンス"""

    success: bool
    markdown: str | None = None
    content: str | None = None
    filename: str
    line_count: int | None = None
    error: str | None = None


class SystemPrompt(BaseModel):
    """システムプロンプト設定"""

    role: str
    purpose: str
    format: str
    notes: str


class CodeFile(BaseModel):
    """レビュー対象のコードファイル"""

    filename: str
    contentWithLineNumbers: str
    lineCount: int | None = None


class DesignFile(BaseModel):
    """レビュー対象の設計書ファイル"""

    filename: str
    content: str
    isMain: bool | None = False
    type: str | None = None
    tool: str | None = "markitdown"


class LLMConfig(BaseModel):
    """LLM設定（オプション）

    リクエストにこの設定が含まれる場合、指定されたプロバイダーを使用する。
    含まれない場合はシステムLLM（環境変数で設定されたBedrock）を使用する。
    """

    model_config = ConfigDict(populate_by_name=True)

    provider: Literal["anthropic", "bedrock", "openai"]
    model: str
    apiKey: str | None = Field(default=None, validation_alias=AliasChoices("apiKey", "api_key"))  # Anthropic/OpenAI用
    baseUrl: str | None = Field(
        default=None,
        validation_alias=AliasChoices("baseUrl", "base_url"),
    )  # OpenAI互換API（Moonshot AI等）の接続先URL。未指定時はOpenAI公式API
    reasoningEffort: str | None = Field(
        default=None,
        validation_alias=AliasChoices("reasoningEffort", "reasoning_effort"),
    )  # 推論モデルの思考量（OpenAI用）。許容値はモデル依存のため検証せずAPIへパススルー
    accessKeyId: str | None = Field(
        default=None,
        validation_alias=AliasChoices("accessKeyId", "access_key_id"),
    )  # Bedrock用
    secretAccessKey: str | None = Field(
        default=None,
        validation_alias=AliasChoices("secretAccessKey", "secret_access_key"),
    )  # Bedrock用
    region: str | None = None  # Bedrock用
    maxTokens: int = Field(
        default=16384,
        validation_alias=AliasChoices("maxTokens", "max_tokens"),
    )


class ReviewRequest(BaseModel):
    """レビューAPIのリクエスト"""

    specMarkdown: str | None = None
    specFilename: str | None = None
    codeWithLineNumbers: str | None = None
    codeFilename: str | None = None
    codes: list[CodeFile] | None = None
    designs: list[DesignFile] | None = None
    systemPrompt: SystemPrompt
    llmConfig: LLMConfig | None = None  # オプション: 未指定時はシステムLLMを使用
    executedAt: str | None = None  # レビュー実行日時（ISO形式）- 指定時はその値を使用、未指定時はサーバー側で生成

    @model_validator(mode='after')
    def validate_code_sources(self):
        if not self.codes and not self.codeWithLineNumbers:
            raise ValueError("コードファイルが指定されていません。")
        return self

    @model_validator(mode='after')
    def validate_design_sources(self):
        if not self.designs and not self.specMarkdown:
            raise ValueError("設計書が指定されていません。")
        return self

    def get_code_blocks(self) -> list[dict]:
        """codes/旧フィールドを統一したリスト形式で取得する"""

        if self.codes:
            return [
                {
                    "filename": code.filename,
                    "contentWithLineNumbers": code.contentWithLineNumbers,
                }
                for code in self.codes
            ]

        if self.codeWithLineNumbers:
            return [
                {
                    "filename": self.codeFilename or "code",
                    "contentWithLineNumbers": self.codeWithLineNumbers,
                }
            ]

        return []

    def get_design_blocks(self) -> list[dict]:
        """designs/旧フィールドを統一したリスト形式で取得する"""

        if self.designs:
            return [
                {
                    "filename": design.filename,
                    "content": design.content,
                    "isMain": design.isMain,
                    "type": design.type,
                    "tool": design.tool,
                }
                for design in self.designs
            ]

        if self.specMarkdown:
            return [
                {
                    "filename": self.specFilename or "design",
                    "content": self.specMarkdown,
                    "isMain": True,  # 単一ファイルの場合はメイン
                    "type": None,
                    "tool": None,
                }
            ]

        return []


class DesignMeta(BaseModel):
    """レビュー対象の設計書メタ情報"""

    filename: str
    role: str
    isMain: bool
    type: str
    tool: str


class ProgramMeta(BaseModel):
    """レビュー対象のプログラムメタ情報"""

    filename: str


class ReviewMeta(BaseModel):
    """レビュー実行時のメタ情報"""

    version: str
    modelId: str
    provider: str | None = None  # プロバイダー名 (bedrock/anthropic/openai)
    executedAt: str
    designs: list[DesignMeta]
    programs: list[ProgramMeta]
    inputTokens: int
    outputTokens: int
    reviewMode: Literal["batch", "split"] | None = None


class ReviewResponse(BaseModel):
    """レビューAPIのレスポンス"""

    success: bool
    report: str | None = None
    reviewMeta: ReviewMeta | None = None
    error: str | None = None


class LLMStatus(BaseModel):
    """LLM接続状態"""

    provider: str
    model: str | None = None
    status: Literal["connected", "error"]
    error: str | None = None


class HealthResponse(BaseModel):
    """ヘルスチェックのレスポンス"""

    status: str
    version: str
    llm: LLMStatus


class ToolInfo(BaseModel):
    """ツール情報"""

    name: str
    display_name: str


class AvailableToolsResponse(BaseModel):
    """利用可能ツールAPIのレスポンス"""

    tools: list[ToolInfo]


class TestConnectionRequest(BaseModel):
    """LLM接続テストのリクエスト

    provider/modelが未指定の場合はシステムLLM（Bedrock）をテストする。
    """

    model_config = ConfigDict(populate_by_name=True)

    provider: Literal["anthropic", "bedrock", "openai"] | None = None
    model: str | None = None
    apiKey: str | None = None
    baseUrl: str | None = Field(
        default=None,
        validation_alias=AliasChoices("baseUrl", "base_url"),
    )
    reasoningEffort: str | None = Field(
        default=None,
        validation_alias=AliasChoices("reasoningEffort", "reasoning_effort"),
    )
    accessKeyId: str | None = None
    secretAccessKey: str | None = None
    region: str | None = None


class TestConnectionResponse(BaseModel):
    """LLM接続テストのレスポンス"""

    status: Literal["connected", "error"]
    provider: str
    model: str | None = None
    error: str | None = None


class MarkdownSourceInfo(BaseModel):
    """Markdown整理対象のソース情報"""

    filename: str
    tool: str = "markitdown"


class OrganizeMarkdownRequest(BaseModel):
    """Markdown整理APIのリクエスト"""

    markdown: str
    policy: str
    source: MarkdownSourceInfo | None = None
    llmConfig: LLMConfig | None = None


class OrganizeMarkdownWarning(BaseModel):
    """Markdown整理APIの警告"""

    code: str
    message: str


class OrganizeMarkdownResponse(BaseModel):
    """Markdown整理APIのレスポンス"""

    success: bool
    organizedMarkdown: str | None = None
    warnings: list[OrganizeMarkdownWarning] = []
    error: str | None = None
    errorCode: str | None = None


# =============================================================================
# Split API スキーマ
# =============================================================================


class HeadingsRequest(BaseModel):
    """見出し一覧取得APIのリクエスト"""

    content: str  # Markdownテキスト


class HeadingInfo(BaseModel):
    """見出し情報"""

    title: str
    level: int
    startLine: int
    endLine: int
    estimatedChars: int


class HeadingsResponse(BaseModel):
    """見出し一覧取得APIのレスポンス"""

    success: bool = True
    headings: list[HeadingInfo] = []
    error: str | None = None


class SplitSettingsDetail(BaseModel):
    """分割設定の詳細（事前重要指定セクション用 / 通常セクション用）"""

    splitMode: Literal["ai", "heading", "nlp"] | None = None
    headingLevel: int | None = None
    splitInstructions: str | None = None
    maxSubsections: int | None = None
    summaryMode: Literal["text", "ai"] | None = None       # サマリー生成モード
    summaryMaxChars: int | None = Field(default=None, ge=10, le=1000)  # テキストモード時の文字数上限


class SplitMarkdownRequest(BaseModel):
    """Markdown分割APIのリクエスト"""

    content: str  # Markdownテキスト
    filename: str  # 元ファイル名
    maxDepth: int = Field(default=2, ge=1, le=6)  # 分割の見出しレベル (H1-H6)
    splitMode: Literal["ai", "heading", "nlp"] = "ai"  # 分割モード
    llmConfig: LLMConfig | None = None  # AIモード用LLM設定
    aiPromptExtraNotes: str | None = None  # AIサブスプリットの注意事項に追記するテキスト（AIモード専用）
    maxSubsections: int | None = None  # グローバル最大サブスプリット数（デフォルト: 5）
    # 事前重要指定関連フィールド
    preImportantSections: list[int] | None = None  # 事前重要指定セクションの start_line リスト
    preImportantSplitSettings: SplitSettingsDetail | None = None  # 事前重要指定セクション向け分割設定
    normalSplitSettings: SplitSettingsDetail | None = None  # 通常セクション向け分割設定
    # 事前除外関連フィールド
    preExcludedSections: list[int] | None = None  # 事前除外セクションの start_line リスト
    # サマリー生成関連フィールド
    summaryMode: Literal["text", "ai"] | None = None  # グローバルサマリーモード（デフォルト: text）
    summaryMaxChars: int | None = Field(default=None, ge=10, le=1000)  # グローバル文字数上限（デフォルト: 100）


class DocumentPart(BaseModel):
    """分割された設計書パーツ"""

    id: str  # セクションID (MD1, MD2, ...)
    section: str  # セクション名
    displayName: str  # 表示用名称（subsplit時はsubsplit_title）
    level: int  # 見出しレベル (1-6)
    path: str  # パス (親セクション > 子セクション)
    startLine: int
    endLine: int
    content: str  # パーツの内容
    estimatedTokens: int
    preImportant: bool = False  # 事前重要指定セクションに属するか


class SplitMarkdownResponse(BaseModel):
    """Markdown分割APIのレスポンス"""

    success: bool
    parts: list[DocumentPart] = []
    indexContent: str | None = None  # INDEX.md相当の内容
    mapJson: list[dict] | None = None  # md2map生成のMAP.json
    warnings: list[str] = []  # パース時の警告メッセージ
    error: str | None = None


class SplitCodeRequest(BaseModel):
    """コード分割APIのリクエスト"""

    content: str  # 元のコード（行番号なし）
    filename: str  # ファイル名（拡張子で言語判定）


class CodePart(BaseModel):
    """分割されたコードパーツ"""

    id: str  # シンボルID (CD1, CD2, ...)
    symbol: str  # シンボル名 (クラス名、関数名など)
    symbolType: str  # class, method, function
    parentSymbol: str | None = None  # 親シンボル (メソッドの場合のクラス名)
    startLine: int
    endLine: int
    content: str  # パーツの内容
    estimatedTokens: int


class SplitCodeResponse(BaseModel):
    """コード分割APIのレスポンス"""

    success: bool
    parts: list[CodePart] = []
    indexContent: str | None = None  # INDEX.md相当の内容
    mapJson: list[dict] | None = None  # code2map生成のMAP.json
    language: str | None = None  # 検出された言語
    warnings: list[str] = []  # パース時の警告メッセージ
    error: str | None = None


# =============================================================================
# Structure Matching API スキーマ
# =============================================================================


class DocumentMapSection(BaseModel):
    """設計書のMAP.jsonセクション情報"""

    title: str
    level: int
    path: str
    startLine: int
    endLine: int


class CodeMapSymbol(BaseModel):
    """コードのMAP.jsonシンボル情報"""

    name: str
    symbolType: str
    parentSymbol: str | None = None
    startLine: int
    endLine: int


class DocumentStructure(BaseModel):
    """設計書の構造情報"""

    indexMd: str
    mapJson: dict  # { sections: list[DocumentMapSection] }


class CodeFileStructure(BaseModel):
    """コードファイルの構造情報"""

    filename: str
    indexMd: str
    mapJson: dict  # { symbols: list[CodeMapSymbol] }


class StructureMatchingRequest(BaseModel):
    """構造マッチングAPIのリクエスト"""

    document: DocumentStructure
    codeFiles: list[CodeFileStructure]
    systemPrompt: SystemPrompt | None = None  # ユーザー指定のシステムプロンプト
    llmConfig: LLMConfig | None = None


class MatchedDocSection(BaseModel):
    """マッチングされた設計書セクション"""

    id: str  # セクションID (MD1, MD2, ...)
    title: str
    path: str


class MatchedCodeSymbol(BaseModel):
    """マッチングされたコードシンボル"""

    id: str  # シンボルID (CD1, CD2, ...)
    filename: str
    symbol: str


class MatchedGroup(BaseModel):
    """マッチングされたグループ"""

    groupId: str
    groupName: str  # グループの表示名
    docSections: list[MatchedDocSection]
    codeSymbols: list[MatchedCodeSymbol]
    reason: str
    estimatedTokens: int


class StructureMatchingResponse(BaseModel):
    """構造マッチングAPIのレスポンス"""

    success: bool
    groups: list[MatchedGroup] = []
    totalGroups: int = 0
    tokensUsed: dict = {}  # トークン使用量 {"input": N, "output": M}
    error: str | None = None


# =============================================================================
# Group Review API スキーマ
# =============================================================================


class GroupReviewRequest(BaseModel):
    """グループレビューAPIのリクエスト

    documentContent, codeContent はフロントエンドで結合済みのテキストを受け取る。
    これにより、片方のみ分割の場合でも全体テキストを渡せる。
    """

    groupId: str
    groupName: str
    documentContent: str  # 結合済みの設計書内容
    codeContent: str  # 結合済みのコード内容
    reviewOptions: dict = {}
    systemPrompt: SystemPrompt | None = None  # ユーザー指定のシステムプロンプト
    llmConfig: LLMConfig | None = None
    # 全体構造コンテキスト（他グループの存在を把握するため）
    documentIndexMd: str | None = None    # 設計書全体のINDEX.md
    documentMapJson: dict | None = None   # 設計書全体のMAP.json
    codeIndexMd: str | None = None        # コード全体のINDEX.md
    codeMapJson: list[dict] | None = None  # コード全体のMAP.json
    allGroups: list[dict] | None = None   # 構造マッチング結果の全グループ情報


class ReviewFinding(BaseModel):
    """レビュー指摘事項"""

    id: str
    findingType: str  # inconsistency, missing_in_code, missing_in_doc, suggestion
    severity: str  # error, warning, info
    docLocation: dict | None = None  # { section: str, line: int }
    codeLocation: dict | None = None  # { filename: str, symbol: str, line: int }
    description: str
    recommendation: str


class GroupReviewResult(BaseModel):
    """グループレビュー結果"""

    report: str = ""  # AIが生成したMarkdown形式のレビューレポート


class GroupReviewResponse(BaseModel):
    """グループレビューAPIのレスポンス"""

    success: bool
    groupId: str
    reviewResult: GroupReviewResult | None = None
    tokensUsed: dict = {}  # { input: int, output: int }
    error: str | None = None
    errorCode: str | None = None  # "token_limit" | "api_error" | None


# =============================================================================
# Integrate API スキーマ
# =============================================================================


class GroupReviewSummary(BaseModel):
    """統合用のグループレビューサマリー"""

    groupId: str
    groupName: str
    report: str = ""  # グループレビューのMarkdownレポート


class IntegrateRequest(BaseModel):
    """結果統合APIのリクエスト"""

    structureMatching: dict  # 構造マッチング結果
    groupReviews: list[GroupReviewSummary]
    integrationOptions: dict = {}  # { deduplicateFindings, checkCrossGroupIssues }
    systemPrompt: SystemPrompt | None = None  # ユーザー指定のシステムプロンプト
    llmConfig: LLMConfig | None = None
    designs: list[dict] = []  # 設計書ファイル情報（review_info_markdown生成用）
    codes: list[dict] = []  # プログラムファイル情報（review_info_markdown生成用）
    # 全体構造コンテキスト（統合時の参考情報）
    documentIndexMd: str | None = None    # 設計書全体のINDEX.md
    documentMapJson: dict | None = None   # 設計書全体のMAP.json
    codeIndexMd: str | None = None        # コード全体のINDEX.md
    codeMapJson: list[dict] | None = None  # コード全体のMAP.json


class KeyIssue(BaseModel):
    """主要な課題"""

    priority: int
    title: str
    affectedGroups: list[str]
    description: str
    relatedFindings: list[str]


class CrossGroupIssue(BaseModel):
    """グループ間の課題"""

    title: str
    groups: list[str]
    description: str


class IntegratedReport(BaseModel):
    """統合レポート"""

    overallSummary: str
    consistencyScore: float
    keyIssues: list[KeyIssue] = []
    crossGroupIssues: list[CrossGroupIssue] = []
    statistics: dict = {}
    deduplicatedFindings: list[str] = []


class IntegrateResponse(BaseModel):
    """結果統合APIのレスポンス"""

    success: bool
    report: str | None = None  # AIが生成した統合レビューレポート（Markdown形式）
    integratedReport: IntegratedReport | None = None
    reviewMeta: ReviewMeta | None = None  # 一括レビューと同様のメタ情報
    tokensUsed: dict = {}
    error: str | None = None
    errorCode: str | None = None  # "token_limit" | "api_error" | None


# =============================================================================
# Summarize API スキーマ
# =============================================================================


class SummarizeRequest(BaseModel):
    """要約APIのリクエスト"""

    text: str                          # 要約対象テキスト
    targetType: str                    # "design" | "code" | "review_result"
    llmConfig: LLMConfig | None = None  # LLM設定


class SummarizeResponse(BaseModel):
    """要約APIのレスポンス"""

    success: bool
    summarizedText: str | None = None
    originalTokens: int | None = None    # 元テキストの推定トークン数
    summarizedTokens: int | None = None  # 要約後の推定トークン数
    tokensUsed: dict | None = None       # LLM消費トークン
    error: str | None = None
