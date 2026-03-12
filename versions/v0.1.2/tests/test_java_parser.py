from code2map.parsers.java_parser import JavaParser


def test_java_parser_extracts_symbols():
    parser = JavaParser()
    symbols, warnings = parser.parse("tests/fixtures/sample.java")
    assert warnings == []
    names = {(s.kind, s.display_name()) for s in symbols}
    assert ("class", "Sample") in names
    assert ("method", "Sample#work") in names
