from code2map.parsers.python_parser import PythonParser


def test_python_parser_extracts_symbols():
    parser = PythonParser()
    symbols, warnings = parser.parse("tests/fixtures/sample.py")
    assert warnings == []
    names = {(s.kind, s.display_name()) for s in symbols}
    assert ("function", "helper") in names
    assert ("class", "Foo") in names
    assert ("method", "Foo#work") in names
