# code2map fragment (non-buildable)
# original: docs/examples/python/user_management_service.py
# lines: 122-137
# symbol: UserManagementService#delete_user
# notes: references dataclasses.dataclass, re, typing.Optional; calls self._find_user_or_throw
    def delete_user(self, user_id: str) -> User:
        """
        ユーザーを削除する

        Args:
            user_id: 削除対象のユーザーID

        Returns:
            削除されたユーザー

        Raises:
            UserNotFoundException: ユーザーが見つからない場合
        """
        existing_user = self._find_user_or_throw(user_id)
        del self._users[user_id]
        return existing_user
