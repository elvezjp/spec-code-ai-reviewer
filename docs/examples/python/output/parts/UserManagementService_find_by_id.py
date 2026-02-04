# code2map fragment (non-buildable)
# original: docs/examples/python/user_management_service.py
# lines: 139-149
# symbol: UserManagementService#find_by_id
# notes: references dataclasses.dataclass, re, typing.Optional; calls self._users.get
    def find_by_id(self, user_id: str) -> Optional[User]:
        """
        ユーザーIDでユーザーを検索する

        Args:
            user_id: 検索対象のユーザーID

        Returns:
            見つかったユーザー（見つからない場合はNone）
        """
        return self._users.get(user_id)
