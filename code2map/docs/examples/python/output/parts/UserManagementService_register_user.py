# code2map fragment (non-buildable)
# original: docs/examples/python/user_management_service.py
# lines: 50-81
# symbol: UserManagementService#register_user
# notes: references dataclasses.dataclass, re, typing.Optional; calls User, UserAlreadyExistsException, self._validate_age, self._validate_email, self._validate_user_id, self._validate_user_name
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
