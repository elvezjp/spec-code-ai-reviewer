"""行番号付与サービス（add-line-numbersを使用）"""

from add_line_numbers import add_line_numbers_to_content


def add_line_numbers(content: str) -> tuple[str, int]:
    """
    テキストに行番号を付与する

    add-line-numbers の add_line_numbers_to_content 関数を使用

    Args:
        content: 行番号を付与する元のテキスト

    Returns:
        tuple: (行番号付きテキスト, 行数)
    """
    return add_line_numbers_to_content(content)
