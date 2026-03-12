from __future__ import annotations

from typing import List, Optional, Tuple

import tree_sitter_java as tsjava
from tree_sitter import Language, Node, Parser

from code2map.models.symbol import Symbol
from code2map.parsers.base_parser import BaseParser
from code2map.utils.file_utils import read_text

JAVA_LANGUAGE = Language(tsjava.language())

_CLASS_LIKE = {
    "class_declaration",
    "interface_declaration",
    "enum_declaration",
    "record_declaration",
    "annotation_type_declaration",
}


def _src(node: Node, source_bytes: bytes) -> str:
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _get_javadoc(node: Node, source_bytes: bytes) -> Optional[str]:
    """Return the first sentence of the Javadoc comment immediately preceding node."""
    parent = node.parent
    if parent is None:
        return None
    idx = next((i for i, c in enumerate(parent.children) if c.id == node.id), -1)
    if idx < 0:
        return None
    for i in range(idx - 1, -1, -1):
        sibling = parent.children[i]
        if sibling.type == "block_comment":
            text = _src(sibling, source_bytes)
            if not text.startswith("/**"):
                return None
            inner = text[3:]
            if inner.endswith("*/"):
                inner = inner[:-2]
            lines = [ln.strip().lstrip("*").strip() for ln in inner.splitlines()]
            joined = " ".join(ln for ln in lines if ln)
            for sep in [".", "\n"]:
                if sep in joined:
                    return joined.split(sep)[0].strip() or None
            return joined.strip() or None
        elif sibling.is_named and sibling.type not in ("line_comment",):
            break
    return None


def _get_param_type(param: Node, source_bytes: bytes) -> str:
    type_node = param.child_by_field_name("type")
    if type_node is None:
        return "?"
    return _src(type_node, source_bytes).strip()


def _collect_calls(node: Node, source_bytes: bytes) -> List[str]:
    calls: List[str] = []

    def walk(n: Node) -> None:
        if n.type == "method_invocation":
            name_node = n.child_by_field_name("name")
            obj_node = n.child_by_field_name("object")
            if name_node:
                name = _src(name_node, source_bytes)
                if obj_node:
                    calls.append(f"{_src(obj_node, source_bytes)}.{name}")
                else:
                    calls.append(name)
        for child in n.children:
            walk(child)

    walk(node)
    return calls


def _get_scoped_name(node: Node, source_bytes: bytes) -> str:
    if node.type == "scoped_identifier":
        scope = node.child_by_field_name("scope")
        name = node.child_by_field_name("name")
        if scope and name:
            return _get_scoped_name(scope, source_bytes) + "." + _src(name, source_bytes)
    return _src(node, source_bytes)


class JavaParser(BaseParser):
    def __init__(self) -> None:
        self._parser = Parser(JAVA_LANGUAGE)

    def parse(self, file_path: str) -> Tuple[List[Symbol], List[str]]:
        warnings: List[str] = []
        source = read_text(file_path)
        if "\ufffd" in source:
            warnings.append("Encoding error detected; replaced invalid characters.")

        source_bytes = source.encode("utf-8")
        tree = self._parser.parse(source_bytes)
        root = tree.root_node

        if root.has_error:
            def _find_error(n: Node) -> Optional[Node]:
                if n.type == "ERROR" or n.is_missing:
                    return n
                for c in n.children:
                    r = _find_error(c)
                    if r:
                        return r
                return None
            err = _find_error(root)
            if err:
                line = err.start_point[0] + 1
                col = err.start_point[1] + 1
                warnings.append(
                    f"Java parse warning: syntax error near line {line}, column {col}"
                    " (partial results may be incomplete)"
                )

        imports: List[str] = []
        for child in root.children:
            if child.type == "import_declaration":
                for c in child.children:
                    if c.type in ("scoped_identifier", "identifier"):
                        imports.append(_get_scoped_name(c, source_bytes))

        symbols: List[Symbol] = []

        def _add_method(node: Node, display_name: str, qualname: str) -> None:
            name_node = node.child_by_field_name("name")
            if name_node is None:
                return
            method_name = _src(name_node, source_bytes)
            params_node = node.child_by_field_name("parameters")
            param_types = []
            if params_node:
                for p in params_node.children:
                    if p.type == "formal_parameter":
                        param_types.append(_get_param_type(p, source_bytes))
            method_symbol = Symbol(
                name=method_name,
                kind="method",
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                original_file=file_path,
                language="java",
                parent=display_name,
                qualname=f"{qualname}#{method_name}",
                role=_get_javadoc(node, source_bytes),
                signature=f"{method_name}({', '.join(param_types)})",
            )
            body = node.child_by_field_name("body")
            method_symbol.calls = sorted(set(_collect_calls(body, source_bytes))) if body else []
            symbols.append(method_symbol)

        def _add_constructor(node: Node, display_name: str, qualname: str) -> None:
            params_node = node.child_by_field_name("parameters")
            param_types = []
            if params_node:
                for p in params_node.children:
                    if p.type == "formal_parameter":
                        param_types.append(_get_param_type(p, source_bytes))
            symbols.append(Symbol(
                name="<init>",
                kind="method",
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                original_file=file_path,
                language="java",
                parent=display_name,
                qualname=f"{qualname}#<init>",
                role=_get_javadoc(node, source_bytes),
                signature=f"{display_name}({', '.join(param_types)})",
            ))

        def _process_body(body_node: Node, display_name: str, qualname: str) -> None:
            for member in body_node.children:
                if member.type == "method_declaration":
                    _add_method(member, display_name, qualname)
                elif member.type == "constructor_declaration":
                    _add_constructor(member, display_name, qualname)
                elif member.type in _CLASS_LIKE:
                    add_class(member, parent=display_name, qualparent=qualname)
                elif member.type == "enum_body_declarations":
                    _process_body(member, display_name, qualname)

        def add_class(node: Node, parent: Optional[str], qualparent: Optional[str]) -> None:
            name_node = node.child_by_field_name("name")
            if name_node is None:
                return
            class_name = _src(name_node, source_bytes)

            if parent:
                qualname = f"{qualparent}.{class_name}"
                display_name = f"{parent}_{class_name}"
            else:
                qualname = class_name
                display_name = class_name

            symbols.append(Symbol(
                name=display_name,
                kind="class",
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                original_file=file_path,
                language="java",
                parent=None,
                qualname=qualname,
                role=_get_javadoc(node, source_bytes),
            ))

            body_node = node.child_by_field_name("body")
            if body_node is not None:
                _process_body(body_node, display_name, qualname)

        for child in root.children:
            if child.type in _CLASS_LIKE:
                add_class(child, parent=None, qualparent=None)

        for symbol in symbols:
            symbol.dependencies = sorted(set(imports))

        return symbols, warnings
