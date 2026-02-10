# code2map fragment (non-buildable)
# id: CD17
# original: docs/examples/python/user_management_service.py
# lines: 223-225
# symbol: UserManagementService#_validate_age
# notes: references dataclasses.dataclass, re, typing.Optional; calls ValueError
    def _validate_age(self, age: int) -> None:
        if age < 0 or age > 150:
            raise ValueError("年齢は0以上150以下で入力してください")
