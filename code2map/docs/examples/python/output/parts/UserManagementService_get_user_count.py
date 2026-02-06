# code2map fragment (non-buildable)
# id: CD13
# original: docs/examples/python/user_management_service.py
# lines: 194-201
# symbol: UserManagementService#get_user_count
# notes: references dataclasses.dataclass, re, typing.Optional; calls len
    def get_user_count(self) -> int:
        """
        登録ユーザー数を取得する

        Returns:
            登録ユーザー数
        """
        return len(self._users)
