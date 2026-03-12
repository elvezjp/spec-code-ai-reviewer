# code2map fragment (non-buildable)
# id: CD2
# original: docs/examples/v0.2.0/python/user_management_service.py
# lines: 16-18
# symbol: UserNotFoundException
# notes: references dataclasses.dataclass, re, typing.Optional
class UserNotFoundException(Exception):
    """ユーザーが見つからない場合の例外"""
    pass
