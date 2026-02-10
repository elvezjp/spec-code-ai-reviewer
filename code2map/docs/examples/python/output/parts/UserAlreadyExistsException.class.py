# code2map fragment (non-buildable)
# id: CD1
# original: docs/examples/python/user_management_service.py
# lines: 11-13
# symbol: UserAlreadyExistsException
# notes: references dataclasses.dataclass, re, typing.Optional
class UserAlreadyExistsException(Exception):
    """ユーザーが既に存在する場合の例外"""
    pass
