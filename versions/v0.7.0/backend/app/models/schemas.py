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

    provider: Literal["anthropic", "bedrock", "openai"] | None = None
    model: str | None = None
    apiKey: str | None = None
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
