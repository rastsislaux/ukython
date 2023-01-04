#! /bin/python3

import ast
import argparse

class KotlinSourceBuilder:

    def __init__(self, indent = 4) -> None:
        self._kotlin_source = ""
        self._tab = 0
        self._indent = indent

    def _idn(self) -> None:
        self._tab += self._indent

    def _udn(self) -> None:
        self._tab -= self._indent

    def _wl(self, lines: list[str]) -> None:
        for line in lines:
            for i in range(self._tab):
                self._kotlin_source += " "
            self._kotlin_source += f"{line}\n"
        lines.clear()


    def build(self, node: ast.AST) -> str:
        match type(node):

            case ast.Module:
                node: ast.Module = node
                for token in node.body:
                    self.build(token)

            case ast.ImportFrom:
                node: ast.ImportFrom = node
                source = []
                for name in node.names:
                    source.append(f"import {node.module}.{name.name}")
                    if name.asname is not None:
                        source[len(source) - 1] += f" as {name.asname}"
                self._wl(source)

            case ast.Expr:
                source = [f"JUST A PLACEHOLDER: {node}"]
                self._wl(source)

            case ast.FunctionDef:
                node: ast.FunctionDef = node
                source = [""]

                for decorator in node.decorator_list:
                    source.append(f"@{decorator.id}")

                args = []
                for arg in node.args.args:
                    args.append(f"{arg.arg}: {arg.annotation.id}")
                args_source = ", ".join(args)
                source.append(f"fun {node.name}({args_source})" + " {")
                self._wl(source)
                self._idn()

                for expr in node.body:
                    self.build(expr)
                self._udn()

                self._wl(["}"])

            case _:
                raise Exception(f"Unsupported AST node type: {type(node)}")

        return self._kotlin_source





def main(args = None):
    with open(args.path) as ky_file:
        ast_tree = ast.parse(ky_file.read())
    
    ksb = KotlinSourceBuilder()
    try:
        print(ksb.build(ast_tree))
    except Exception as e:
        print(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Kython to Kotlin transpiler')
    parser.add_argument('command', type=str, help="Command to run", choices=["com"])
    parser.add_argument('path', type=str, help="File to transpile")
    args = parser.parse_args()
    main(args)
