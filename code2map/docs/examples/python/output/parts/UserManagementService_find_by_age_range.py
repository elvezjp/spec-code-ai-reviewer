# code2map fragment (non-buildable)
# original: docs/examples/python/user_management_service.py
# lines: 160-175
# symbol: UserManagementService#find_by_age_range
# notes: references dataclasses.dataclass, re, typing.Optional; calls result.append, self._users.values
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
