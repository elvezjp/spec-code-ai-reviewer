"""クライアント指定のファイル名を安全に扱うためのユーティリティ。"""

import os

DEFAULT_FILENAME = "input"


def safe_filename(filename: str | None, default: str = DEFAULT_FILENAME) -> str:
    """クライアント由来のファイル名から、パス要素を取り除いた基底名を返す。

    ``os.path.join`` や ``pathlib`` の ``/`` 演算子は、右辺が絶対パスの場合に
    左辺を破棄する（``os.path.join("/tmp", "/etc/x")`` は ``"/etc/x"``）。
    そのため、クライアントが指定したファイル名をそのまま結合すると、
    一時ディレクトリの外へ書き込めてしまう。

    この関数はディレクトリ成分と ``.`` / ``..`` を取り除き、結合先が
    必ず意図したディレクトリ直下になるようにする。
    """
    if not filename:
        return default

    # Windows 形式の区切り文字も除去してから基底名を取る
    candidate = os.path.basename(filename.replace("\\", "/")).strip()

    if not candidate or candidate in (".", ".."):
        return default
    return candidate
