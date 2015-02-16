"""Generator of dynamically typed stubs for arbitrary modules."""

import os.path

import mypy.parse
import mypy.traverser
from mypy.nodes import (
    IntExpr, UnaryExpr, StrExpr, BytesExpr, NameExpr, FloatExpr, MemberExpr,
    ARG_STAR, ARG_STAR2
)


def generate_stub(path, output_dir):
    source = open(path).read()
    ast = mypy.parse.parse(source)
    gen = StubGenerator()
    ast.accept(gen)
    with open(os.path.join(output_dir, os.path.basename(path)), 'w') as file:
        file.write(''.join(gen.output()))


class StubGenerator(mypy.traverser.TraverserVisitor):
    def __init__(self):
        self._output = []
        self._imports = []
        self._indent = ''

    def visit_func_def(self, o):
        self_inits = find_self_initializers(o)
        for init in self_inits:
            self.add_init(init)
        self.add("%sdef %s(" % (self._indent, o.name()))
        args = []
        for i, (arg, kind) in enumerate(zip(o.args, o.arg_kinds)):
            name = arg.name()
            init = o.init[i]
            if init:
                arg = '%s=' % name
                init = init.rvalue
                if isinstance(init, IntExpr):
                    arg += str(init.value)
                elif isinstance(init, StrExpr):
                    arg += "''"
                elif isinstance(init, BytesExpr):
                    arg += "b''"
                elif isinstance(init, FloatExpr):
                    arg += "0.0"
                elif isinstance(init, UnaryExpr):
                    arg += '-%s' % init.expr.value
                elif isinstance(init, NameExpr) and init.name == 'None':
                    arg += init.name
                else:
                    self.add_import("Undefined")
                    arg += 'Undefined'
            elif kind == ARG_STAR:
                arg = '*%s' % name
            elif kind == ARG_STAR2:
                arg = '**%s' % name
            else:
                arg = name
            args.append(arg)
        self.add(', '.join(args))
        self.add("): pass\n")

    def visit_class_def(self, o):
        self.add('class %s:\n' % o.name)
        self._indent += '    '
        super().visit_class_def(o)
        self._indent = self._indent[:-4]

    def visit_assignment_stmt(self, o):
        lvalue = o.lvalues[0]
        if isinstance(lvalue, NameExpr):
            self.add_init(lvalue.name)

    def add_init(self, lvalue):
        self.add('%s%s = Undefined(Any)\n' % (self._indent, lvalue))
        self.add_import('Undefined')
        self.add_import('Any')

    def add(self, string):
        self._output.append(string)

    def add_import(self, name):
        if name not in self._imports:
            self._imports.append(name)

    def output(self):
        if self._imports:
            imports = 'from typing import %s\n\n' % ", ".join(self._imports)
        else:
            imports = ''
        return imports + ''.join(self._output)


def find_self_initializers(fdef):
    results = []
    class SelfTraverser(mypy.traverser.TraverserVisitor):
        def visit_assignment_stmt(self, o):
            lvalue = o.lvalues[0]
            if (isinstance(lvalue, MemberExpr) and
                    isinstance(lvalue.expr, NameExpr) and
                    lvalue.expr.name == 'self'):
                results.append(lvalue.name)
    fdef.accept(SelfTraverser())
    return results
