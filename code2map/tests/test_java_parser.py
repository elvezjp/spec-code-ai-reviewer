from code2map.parsers.java_parser import JavaParser


def test_java_parser_extracts_symbols():
    parser = JavaParser()
    symbols, warnings = parser.parse("tests/fixtures/sample.java")
    assert warnings == []
    names = {(s.kind, s.display_name()) for s in symbols}
    assert ("class", "Sample") in names
    assert ("method", "Sample#work") in names


def test_java8_syntax_parses_successfully():
    # tree-sitter は Java 8+構文を正常にパースできる
    parser = JavaParser()
    symbols, warnings = parser.parse("tests/fixtures/java8_syntax.java")
    assert warnings == []
    names = {(s.kind, s.display_name()) for s in symbols}
    assert ("class", "Java8Syntax") in names
    assert ("class", "Java8Syntax_Status") in names
    assert ("method", "Java8Syntax_Status#getKeys") in names


def test_java8_syntax_constructor_extracted():
    parser = JavaParser()
    symbols, _ = parser.parse("tests/fixtures/java8_syntax.java")
    names = {(s.kind, s.display_name()) for s in symbols}
    assert ("method", "Java8Syntax_Status#<init>") in names


def test_java_syntax_error_returns_warning():
    # 構文エラーがある場合、warnings にメッセージが返ること
    parser = JavaParser()
    _, warnings = parser.parse("tests/fixtures/java_syntax_error.java")
    assert len(warnings) >= 1
    assert warnings[0] != ""


def test_java_syntax_error_warning_contains_location():
    # 構文エラーの warning に行番号が含まれること
    parser = JavaParser()
    _, warnings = parser.parse("tests/fixtures/java_syntax_error.java")
    assert any("line" in w for w in warnings)
