"""LLM プロバイダー抽象基底クラス"""

from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """LLM プロバイダーの抽象基底クラス

    各プロバイダー（OpenAI, Anthropic, Bedrock）はこのクラスを継承し、
    send_message を実装する。
    """

    @abstractmethod
    def send_message(self, system_prompt: str, user_message: str) -> str:
        """メッセージを送信してレスポンステキストを返す

        Args:
            system_prompt: システムプロンプト
            user_message: ユーザーメッセージ

        Returns:
            LLM からのレスポンステキスト

        Raises:
            RuntimeError: API 呼び出しに失敗した場合
        """
        raise NotImplementedError
