"""Sample module"""

import os
import json


def helper(x):
    """Helper function."""
    print(x)
    return json.dumps({"x": x})


class Foo:
    """Foo class."""

    def __init__(self, value):
        self.value = value

    def work(self, value):
        """Do work."""
        return helper(value)
