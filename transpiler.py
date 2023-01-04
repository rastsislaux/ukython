#! /bin/python3

import ast
import argparse
import os

class KotlinSourceBuilder:

    def __init__(self, indent = 4) -> None:
        self._kotlin_source = ""
        self._tab = 0
        self._indent = indent
        self._scope: list[list[str]] = []

    def _idn(self) -> None:
        self._tab += self._indent
        self._scope.append([])

    def _udn(self) -> None:
        self._tab -= self._indent
        self._scope.pop()

    def _insc(self, name: str):
        for i in self._scope:
            for j in i:
                if j == name: return True
        return False

    def _adsc(self, name: str):
        self._scope[len(self._scope) - 1].append(name)

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
                node: ast.Expr = node
                self.build(node.value)

            case ast.Assign:
                node: ast.Assign = node
                if len(node.targets) > 1:
                    raise Exception("Unpacking is not supported.")
                
                lvalue = node.targets[0].id
                keyw = ""
                if not self._insc(lvalue):
                    keyw = "var "
                    self._adsc(lvalue)



                rvalue = ""
                match type(node.value):
                    case ast.Constant:
                            node: ast.Constant = node.value
                            if (type(node.value) == str): rvalue = f'"{node.value}"'
                            else: rvalue = f"{node.value}"
                    case ast.Name:
                        node: ast.Name = node
                        rvalue = node.id
                    case ast.Call:
                        source = [f"{keyw}{lvalue} = "]
                        self._wl(source)
                        self._kotlin_source = self._kotlin_source[:-1]
                        self._kotlin_source = self._kotlin_source[:]
                        self.build(node.value)
                        return
                    case _: raise Exception(f"Unknown AST node in Assign args: {node.value}")

                source = [f"{keyw}{lvalue} = {rvalue}"]
                self._wl(source)

            case ast.AnnAssign:
                node: ast.AnnAssign = node
                lvalue = node.target.id
                keyw = ""
                if not self._insc(lvalue):
                    keyw = "var "
                    self._adsc(lvalue)

                rvalue = ""
                match type(node.value):
                    case ast.Constant:
                        node1: ast.Constant = node.value
                        if (type(node1.value) == str): rvalue = f'"{node1.value}"'
                        else: rvalue = f"{node1.value}"
                    case ast.Name:
                        node1: ast.Name = node.value
                        rvalue = node1.id
                    case _: raise Exception(f"Unknown AST node in AnnAssign args: {node1}")

                source = [f"{keyw}{lvalue}: {node.annotation.id} = {rvalue}"]
                self._wl(source)

            case ast.Call:
                node: ast.Call = node

                args = []
                for arg in node.args:
                    match type(arg):
                        case ast.Constant:
                            arg: ast.Constant = arg
                            if (type(arg.value) == str): args.append(f'"{arg.value}"')
                            else: args.append(f"{arg.value}")
                        case ast.Name:
                            arg: ast.Name = arg
                            args.append(arg.id)
                        case _: raise Exception(f"Unknown AST node in ast.Call args: {arg}")

                args_str = ", ".join(args)
                self._wl([f"{node.func.id}({args_str})"])

            case ast.Return:
                node: ast.Return = node
                rvalue = ""
                match type(node.value):
                    case ast.Constant:
                        node1: ast.Constant = node.value
                        if (type(node1.value) == str): rvalue = f'"{node1.value}"'
                        else: rvalue = f"{node1.value}"
                    case ast.Name:
                        node1: ast.Name = node.value
                        rvalue = node1.id
                    case _: raise Exception(f"Unknown AST node in ast.Return args: {node1}")
                self._wl([f"return {rvalue}"])

            case ast.FunctionDef:
                node: ast.FunctionDef = node
                source = [""]

                for decorator in node.decorator_list:
                    source.append(f"@{decorator.id}")

                args = []
                for arg in node.args.args:
                    args.append(f"{arg.arg}: {arg.annotation.id}")
                args_source = ", ".join(args)

                ret_type = ""
                if (node.returns is not None):
                    ret_type = f": {node.returns.id}"

                source.append(f"fun {node.name}({args_source}){ret_type}" + " {")
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
    
    try:
        kotlin = KotlinSourceBuilder().build(ast_tree)
    except Exception as e:
        print(e)
        return

    name: str = args.path.split('/').pop().split('.')[0]
    mainClass = f"{name.capitalize()}Kt"
    
    match (args.command):
        case "com":
            print(kotlin)
        case "run":
            with open(f"{name}.kt", 'w') as gen:
                gen.write(kotlin)
            os.system(f"kotlinc {name}.kt")
            os.system(f"kotlin {mainClass}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Kython to Kotlin transpiler')
    parser.add_argument('command', type=str, help="Command to run", choices=["com", "run"])
    parser.add_argument('path', type=str, help="File to transpile")
    args = parser.parse_args()
    main(args)
