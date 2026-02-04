# code2map fragment (non-buildable)
# original: docs/examples/python/user_management_service.py
# lines: 227-231
# symbol: UserManagementService#_find_user_or_throw
# notes: references dataclasses.dataclass, re, typing.Optional; calls UserNotFoundException, self._users.get
    def _find_user_or_throw(self, user_id: str) -> User:
        user = self._users.get(user_id)
        if user is None:
            raise UserNotFoundException(f"ユーザーID '{user_id}' が見つかりません")
        return user
