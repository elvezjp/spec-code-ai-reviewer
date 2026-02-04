# code2map fragment (non-buildable)
# original: docs/examples/python/user_management_service.py
# lines: 83-120
# symbol: UserManagementService#update_user
# notes: references dataclasses.dataclass, re, typing.Optional; calls self._find_user_or_throw, self._validate_age, self._validate_email, self._validate_user_name
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
