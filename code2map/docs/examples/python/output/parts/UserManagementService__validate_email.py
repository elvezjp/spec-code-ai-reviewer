# code2map fragment (non-buildable)
# id: CD16
# original: docs/examples/python/user_management_service.py
# lines: 217-221
# symbol: UserManagementService#_validate_email
# notes: references dataclasses.dataclass, re, typing.Optional; calls ValueError, email.strip, self.EMAIL_PATTERN.match
    def _validate_email(self, email: str) -> None:
        if not email or not email.strip():
            raise ValueError("メールアドレスは必須です")
        if not self.EMAIL_PATTERN.match(email):
            raise ValueError("メールアドレスの形式が不正です")
