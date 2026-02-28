from __future__ import annotations

from typing import List, Tuple

import javalang

from code2map.models.symbol import Symbol
from code2map.parsers.base_parser import BaseParser
from code2map.utils.file_utils import read_lines, read_text


def _find_brace_block_end(lines: List[str], start_line: int) -> int:
    line_index = max(start_line - 1, 0)
    found_open = False
    depth = 0
    for i in range(line_index, len(lines)):
        line = lines[i]
        for char in line:
            if char == "{":
                depth += 1
                found_open = True
            elif char == "}":
                if found_open:
                    depth -= 1
                    if depth == 0:
                        return i + 1
        # Continue to next line
    return start_line


def _extract_javadoc(lines: List[str], start_line: int) -> str | None:
    idx = start_line - 2
    while idx >= 0 and lines[idx].strip() == "":
        idx -= 1
    # Skip annotations
    while idx >= 0 and lines[idx].lstrip().startswith("@"):
        idx -= 1
    if idx < 0:
        return None
    if "*/" not in lines[idx]:
        return None
    # Walk up to find /**
    end_idx = idx
    while idx >= 0 and "/**" not in lines[idx]:
        idx -= 1
    if idx < 0:
        return None
    # Collect comment lines
    comment_lines = lines[idx : end_idx + 1]
    cleaned: List[str] = []
    for line in comment_lines:
        line = line.strip()
        if line.startswith("/**"):
            line = line[3:]
        if line.endswith("*/"):
            line = line[:-2]
        if line.startswith("*"):
            line = line[1:]
        cleaned.append(line.strip())
    text = " ".join([c for c in cleaned if c])
    if not text:
        return None
    # First sentence or line
    for sep in [".", "\n"]:
        if sep in text:
            return text.split(sep)[0].strip()
    return text.strip()


class JavaParser(BaseParser):
    def parse(self, file_path: str) -> Tuple[List[Symbol], List[str]]:
        warnings: List[str] = []
        source = read_text(file_path)
        if "\ufffd" in source:
            warnings.append("Encoding error detected; replaced invalid characters.")
        lines = source.splitlines()
        try:
            tree = javalang.parse.parse(source)
        except (javalang.parser.JavaSyntaxError, IndexError) as exc:
            warnings.append(f"Java parse error: {exc}")
            return [], warnings

        imports = [imp.path for imp in tree.imports]
        symbols: List[Symbol] = []

        def add_class(node, parent: str | None = None) -> None:
            if not node.position:
                return
            class_name = node.name
            if parent:
                qualname = f"{parent}.{class_name}"
                display_parent = f"{parent}_{class_name}"
            else:
                qualname = class_name
                display_parent = class_name

            start_line = node.position.line
            end_line = _find_brace_block_end(lines, start_line)
            role = _extract_javadoc(lines, start_line)
            class_symbol = Symbol(
                name=display_parent,
                kind="class",
                start_line=start_line,
                end_line=end_line,
                original_file=file_path,
                language="java",
                parent=None,
                qualname=qualname,
                role=role,
            )
            symbols.append(class_symbol)

            # Methods
            for method in node.methods:
                if not method.position:
                    continue
                method_name = method.name
                param_types = [param.type.name for param in method.parameters]
                signature = f"{method_name}({', '.join(param_types)})"
                method_start = method.position.line
                method_end = _find_brace_block_end(lines, method_start)
                method_role = _extract_javadoc(lines, method_start)
                method_symbol = Symbol(
                    name=method_name,
                    kind="method",
                    start_line=method_start,
                    end_line=method_end,
                    original_file=file_path,
                    language="java",
                    parent=display_parent,
                    qualname=f"{qualname}#{method_name}",
                    role=method_role,
                    signature=signature,
                )
                calls = []
                for _, invocation in method.filter(javalang.tree.MethodInvocation):
                    if invocation.qualifier:
                        calls.append(f"{invocation.qualifier}.{invocation.member}")
                    else:
                        calls.append(invocation.member)
                method_symbol.calls = sorted(set(calls))
                symbols.append(method_symbol)

            for constructor in node.constructors:
                if not constructor.position:
                    continue
                ctor_start = constructor.position.line
                param_types = [param.type.name for param in constructor.parameters]
                signature = f"{display_parent}({', '.join(param_types)})"
                ctor_end = _find_brace_block_end(lines, ctor_start)
                ctor_role = _extract_javadoc(lines, ctor_start)
                ctor_symbol = Symbol(
                    name="<init>",
                    kind="method",
                    start_line=ctor_start,
                    end_line=ctor_end,
                    original_file=file_path,
                    language="java",
                    parent=display_parent,
                    qualname=f"{qualname}#<init>",
                    role=ctor_role,
                    signature=signature,
                )
                symbols.append(ctor_symbol)

            for inner in node.body:
                if isinstance(inner, (javalang.tree.ClassDeclaration, javalang.tree.InterfaceDeclaration)):
                    add_class(inner, parent=display_parent)

        for type_node in tree.types:
            if isinstance(type_node, (javalang.tree.ClassDeclaration, javalang.tree.InterfaceDeclaration)):
                add_class(type_node)

        for symbol in symbols:
            symbol.dependencies = sorted(set(imports))

        return symbols, warnings
