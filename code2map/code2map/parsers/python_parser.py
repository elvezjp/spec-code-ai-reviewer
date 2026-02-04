from __future__ import annotations

import ast
from typing import Dict, List, Tuple

from code2map.models.symbol import Symbol
from code2map.parsers.base_parser import BaseParser
from code2map.utils.file_utils import read_text


class _PythonSymbolVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.symbols: List[Symbol] = []
        self._current_symbol: List[Symbol] = []
        self._module_imports: List[str] = []
        self._ignore_new_symbol: int = 0
        self._function_depth: int = 0

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._module_imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            if module:
                self._module_imports.append(f"{module}.{alias.name}")
            else:
                self._module_imports.append(alias.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        parent = self._current_symbol[-1] if self._current_symbol else None
        name = node.name
        qualname = node.name
        parent_name = None
        if parent and parent.kind == "class":
            # Nested class: split as its own symbol with flattened name.
            name = f"{parent.name}_{node.name}"
            qualname = f"{parent.qualname}.{node.name}" if parent.qualname else name
            parent_name = parent.name

        symbol = Symbol(
            name=node.name,
            kind="class",
            start_line=getattr(node, "lineno", 1),
            end_line=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
            original_file=self.file_path,
            language="python",
            parent=parent_name,
            qualname=qualname,
            role=ast.get_docstring(node),
        )
        # Use the derived name for nested classes.
        symbol.name = name
        self.symbols.append(symbol)
        self._current_symbol.append(symbol)
        self.generic_visit(node)
        self._current_symbol.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._handle_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_function(node)

    def _handle_function(self, node: ast.AST) -> None:
        if self._ignore_new_symbol > 0:
            self._function_depth += 1
            self.generic_visit(node)
            self._function_depth -= 1
            return

        if self._function_depth > 0:
            # Nested function: keep in parent part (do not create a symbol).
            self._function_depth += 1
            self.generic_visit(node)
            self._function_depth -= 1
            return

        if self._current_symbol and self._current_symbol[-1].kind == "class":
            parent = self._current_symbol[-1]
            symbol = Symbol(
                name=node.name,
                kind="method",
                start_line=getattr(node, "lineno", 1),
                end_line=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
                original_file=self.file_path,
                language="python",
                parent=parent.name,
                qualname=f"{parent.name}#{node.name}",
                role=ast.get_docstring(node),
            )
        else:
            symbol = Symbol(
                name=node.name,
                kind="function",
                start_line=getattr(node, "lineno", 1),
                end_line=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
                original_file=self.file_path,
                language="python",
                parent=None,
                qualname=node.name,
                role=ast.get_docstring(node),
            )

        self.symbols.append(symbol)
        self._current_symbol.append(symbol)
        self._function_depth += 1
        self.generic_visit(node)
        self._function_depth -= 1
        self._current_symbol.pop()

    def visit_Call(self, node: ast.Call) -> None:
        if self._current_symbol:
            name = self._call_name(node.func)
            if name:
                self._current_symbol[-1].calls.append(name)
        self.generic_visit(node)

    def _call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            value = self._call_name(node.value)
            if value:
                return f"{value}.{node.attr}"
            return node.attr
        return ""

    def finalize(self) -> List[Symbol]:
        for symbol in self.symbols:
            symbol.dependencies = sorted(set(self._module_imports))
            symbol.calls = sorted(set(symbol.calls))
        return self.symbols


class PythonParser(BaseParser):
    def parse(self, file_path: str) -> Tuple[List[Symbol], List[str]]:
        warnings: List[str] = []
        try:
            source = read_text(file_path)
            if "\ufffd" in source:
                warnings.append("Encoding error detected; replaced invalid characters.")
            tree = ast.parse(source)
        except SyntaxError as exc:
            warnings.append(f"Python parse error at line {exc.lineno}: {exc.msg}")
            return [], warnings

        visitor = _PythonSymbolVisitor(file_path)
        visitor.visit(tree)
        return visitor.finalize(), warnings
