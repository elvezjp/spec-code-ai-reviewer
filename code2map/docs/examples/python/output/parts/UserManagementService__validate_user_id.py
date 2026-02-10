# code2map fragment (non-buildable)
# id: CD14
# original: docs/examples/python/user_management_service.py
# lines: 205-209
# symbol: UserManagementService#_validate_user_id
# notes: references dataclasses.dataclass, re, typing.Optional; calls ValueError, len, user_id.strip
    def _validate_user_id(self, user_id: str) -> None:
        if not user_id or not user_id.strip():
            raise ValueError("ユーザーIDは必須です")
        if len(user_id) > self.MAX_USER_ID_LENGTH:
            raise ValueError(f"ユーザーIDは{self.MAX_USER_ID_LENGTH}文字以内で入力してください")
