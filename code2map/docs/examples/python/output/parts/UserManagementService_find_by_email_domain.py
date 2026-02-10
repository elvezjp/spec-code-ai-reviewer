# code2map fragment (non-buildable)
# id: CD12
# original: docs/examples/python/user_management_service.py
# lines: 177-192
# symbol: UserManagementService#find_by_email_domain
# notes: references dataclasses.dataclass, re, typing.Optional; calls result.append, self._users.values, user.email.endswith
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
