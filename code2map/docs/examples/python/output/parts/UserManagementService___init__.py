# code2map fragment (non-buildable)
# original: docs/examples/python/user_management_service.py
# lines: 46-48
# symbol: UserManagementService#__init__
# notes: references dataclasses.dataclass, re, typing.Optional
    def __init__(self):
        """ユーザー格納用の辞書（キー: ユーザーID）"""
        self._users: dict[str, User] = {}
