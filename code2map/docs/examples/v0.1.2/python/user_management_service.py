"""
ユーザー管理システム
ユーザーの登録、更新、削除、検索機能を提供する
"""

import re
from dataclasses import dataclass
from typing import Optional


class UserAlreadyExistsException(Exception):
    """ユーザーが既に存在する場合の例外"""
    pass


class UserNotFoundException(Exception):
    """ユーザーが見つからない場合の例外"""
    pass


@dataclass
class User:
    """ユーザーエンティティ"""
    user_id: str
    user_name: str
    email: str
    age: int


class UserManagementService:
    """
    ユーザー管理サービス

    ユーザーの登録、更新、削除、検索機能を提供する
    """

    # メールアドレスの正規表現パターン
    EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$")

    # ユーザーIDの最大長
    MAX_USER_ID_LENGTH = 20

    # ユーザー名の最大長
    MAX_USER_NAME_LENGTH = 50

    def __init__(self):
        """ユーザー格納用の辞書（キー: ユーザーID）"""
        self._users: dict[str, User] = {}

    def register_user(self, user_id: str, user_name: str, email: str, age: int) -> User:
        """
        新規ユーザーを登録する

        Args:
            user_id: ユーザーID（必須、20文字以内）
            user_name: ユーザー名（必須、50文字以内）
            email: メールアドレス（必須、形式チェックあり）
            age: 年齢（0以上150以下）

        Returns:
            登録されたユーザー

        Raises:
            ValueError: 入力値が不正な場合
            UserAlreadyExistsException: 同一IDのユーザーが既に存在する場合
        """
        # 入力値検証
        self._validate_user_id(user_id)
        self._validate_user_name(user_name)
        self._validate_email(email)
        self._validate_age(age)

        # 重複チェック
        if user_id in self._users:
            raise UserAlreadyExistsException(f"ユーザーID '{user_id}' は既に登録されています")

        # ユーザー作成・登録
        new_user = User(user_id, user_name, email, age)
        self._users[user_id] = new_user

        return new_user

    def update_user(
        self,
        user_id: str,
        user_name: Optional[str] = None,
        email: Optional[str] = None,
        age: Optional[int] = None,
    ) -> User:
        """
        ユーザー情報を更新する

        Args:
            user_id: 更新対象のユーザーID
            user_name: 新しいユーザー名（Noneの場合は更新しない）
            email: 新しいメールアドレス（Noneの場合は更新しない）
            age: 新しい年齢（Noneの場合は更新しない）

        Returns:
            更新されたユーザー

        Raises:
            UserNotFoundException: ユーザーが見つからない場合
        """
        existing_user = self._find_user_or_throw(user_id)

        # 各フィールドの更新（Noneでない場合のみ）
        if user_name is not None and user_name:
            self._validate_user_name(user_name)
            existing_user.user_name = user_name

        if email is not None and email:
            self._validate_email(email)
            existing_user.email = email

        if age is not None:
            self._validate_age(age)
            existing_user.age = age

        return existing_user

    def delete_user(self, user_id: str) -> User:
        """
        ユーザーを削除する

        Args:
            user_id: 削除対象のユーザーID

        Returns:
            削除されたユーザー

        Raises:
            UserNotFoundException: ユーザーが見つからない場合
        """
        existing_user = self._find_user_or_throw(user_id)
        del self._users[user_id]
        return existing_user

    def find_by_id(self, user_id: str) -> Optional[User]:
        """
        ユーザーIDでユーザーを検索する

        Args:
            user_id: 検索対象のユーザーID

        Returns:
            見つかったユーザー（見つからない場合はNone）
        """
        return self._users.get(user_id)

    def find_all(self) -> list[User]:
        """
        全ユーザーを取得する

        Returns:
            全ユーザーのリスト
        """
        return list(self._users.values())

    def find_by_age_range(self, min_age: int, max_age: int) -> list[User]:
        """
        年齢範囲でユーザーを検索する

        Args:
            min_age: 最小年齢（含む）
            max_age: 最大年齢（含む）

        Returns:
            条件に一致するユーザーのリスト
        """
        result = []
        for user in self._users.values():
            if min_age <= user.age <= max_age:
                result.append(user)
        return result

    def find_by_email_domain(self, domain: str) -> list[User]:
        """
        メールドメインでユーザーを検索する

        Args:
            domain: メールドメイン（例: "example.com"）

        Returns:
            条件に一致するユーザーのリスト
        """
        result = []
        domain_suffix = f"@{domain}"
        for user in self._users.values():
            if user.email.endswith(domain_suffix):
                result.append(user)
        return result

    def get_user_count(self) -> int:
        """
        登録ユーザー数を取得する

        Returns:
            登録ユーザー数
        """
        return len(self._users)

    # --- バリデーションメソッド ---

    def _validate_user_id(self, user_id: str) -> None:
        if not user_id or not user_id.strip():
            raise ValueError("ユーザーIDは必須です")
        if len(user_id) > self.MAX_USER_ID_LENGTH:
            raise ValueError(f"ユーザーIDは{self.MAX_USER_ID_LENGTH}文字以内で入力してください")

    def _validate_user_name(self, user_name: str) -> None:
        if not user_name or not user_name.strip():
            raise ValueError("ユーザー名は必須です")
        if len(user_name) > self.MAX_USER_NAME_LENGTH:
            raise ValueError(f"ユーザー名は{self.MAX_USER_NAME_LENGTH}文字以内で入力してください")

    def _validate_email(self, email: str) -> None:
        if not email or not email.strip():
            raise ValueError("メールアドレスは必須です")
        if not self.EMAIL_PATTERN.match(email):
            raise ValueError("メールアドレスの形式が不正です")

    def _validate_age(self, age: int) -> None:
        if age < 0 or age > 150:
            raise ValueError("年齢は0以上150以下で入力してください")

    def _find_user_or_throw(self, user_id: str) -> User:
        user = self._users.get(user_id)
        if user is None:
            raise UserNotFoundException(f"ユーザーID '{user_id}' が見つかりません")
        return user
