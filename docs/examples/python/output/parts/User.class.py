# code2map fragment (non-buildable)
# original: docs/examples/python/user_management_service.py
# lines: 22-27
# symbol: User
# notes: references dataclasses.dataclass, re, typing.Optional
class User:
    """ユーザーエンティティ"""
    user_id: str
    user_name: str
    email: str
    age: int
