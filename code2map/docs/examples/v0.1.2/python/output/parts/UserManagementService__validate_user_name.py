# code2map fragment (non-buildable)
# id: CD15
# original: docs/examples/python/user_management_service.py
# lines: 211-215
# symbol: UserManagementService#_validate_user_name
# notes: references dataclasses.dataclass, re, typing.Optional; calls ValueError, len, user_name.strip
    def _validate_user_name(self, user_name: str) -> None:
        if not user_name or not user_name.strip():
            raise ValueError("ユーザー名は必須です")
        if len(user_name) > self.MAX_USER_NAME_LENGTH:
            raise ValueError(f"ユーザー名は{self.MAX_USER_NAME_LENGTH}文字以内で入力してください")
