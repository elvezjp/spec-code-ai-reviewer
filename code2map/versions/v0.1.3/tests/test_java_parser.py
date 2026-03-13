from code2map.parsers.java_parser import JavaParser


def test_java_parser_extracts_symbols():
    parser = JavaParser()
    symbols, warnings = parser.parse("tests/fixtures/sample.java")
    assert warnings == []
    names = {(s.kind, s.display_name()) for s in symbols}
    assert ("class", "Sample") in names
    assert ("method", "Sample#work") in names


def test_java_parse_error_message_not_empty():
    parser = JavaParser()
    symbols, warnings = parser.parse("tests/fixtures/java8_syntax.java")
    assert symbols == []
    assert len(warnings) == 1
    assert warnings[0] != ""
    assert warnings[0] != "Java parse error: "


def test_java_parse_error_contains_description():
    parser = JavaParser()
    _, warnings = parser.parse("tests/fixtures/java8_syntax.java")
    assert any("Expected" in w for w in warnings)


def test_java_parse_error_contains_location():
    parser = JavaParser()
    _, warnings = parser.parse("tests/fixtures/java8_syntax.java")
    assert any("line" in w for w in warnings)
