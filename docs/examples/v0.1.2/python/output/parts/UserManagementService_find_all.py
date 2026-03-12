# code2map fragment (non-buildable)
# id: CD10
# original: docs/examples/python/user_management_service.py
# lines: 151-158
# symbol: UserManagementService#find_all
# notes: references dataclasses.dataclass, re, typing.Optional; calls list, self._users.values
    def find_all(self) -> list[User]:
        """
        全ユーザーを取得する

        Returns:
            全ユーザーのリスト
        """
        return list(self._users.values())
