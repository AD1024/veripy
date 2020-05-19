from veripy.parser.syntax import *


def print_line(level, content):
    print((' ' * 4) * level, content)

def _print(level, content):
    print((' ' * 4) * level, content)

def pretty_print_seq(level, ast):
    print_line(level, 'Seq(')
    pretty_print_impl(level + 1, ast.s1)
    pretty_print_impl(level + 1, ast.s2)
    print_line(level, ')')

def pretty_print_if(level, ast):
    print_line(level, 'If(')
    print_line(level + 1, ast.cond)
    pretty_print_impl(level + 1, ast.lb)
    pretty_print_impl(level + 1, ast.rb)
    print_line(level, ')')

def pretty_print_while(level, ast):
    print_line(level, 'While(')
    print_line(level + 1, ast.cond)
    print_line(level + 1, f'Invariants: {ast.invariants}')
    pretty_print_impl(level + 1, ast.body)
    print_line(level, ')')

def pretty_print_assert(level, ast):
    print_line(level, 'Assert(')
    print_line(level + 1, ast.e)
    print_line(level, ')')

def pretty_print_assume(level, ast):
    print_line(level, 'Assume(')
    print_line(level + 1, ast.e)
    print_line(level, ')')

def pretty_print_assign(level, ast):
    print_line(level, 'Assign(')
    print_line(level + 1, ast.var)
    print_line(level + 1, ast.expr)
    print_line(level, ')')

def pretty_print_skip(level, ast):
    print_line(level, 'Skip()')

def pretty_print_havoc(level, ast):
    print_line(level, f'Havoc({ast.var})')

def pretty_print_impl(level, ast):
    {
        Seq: lambda: pretty_print_seq(level, ast),
        If: lambda: pretty_print_if(level, ast),
        While: lambda: pretty_print_while(level, ast),
        Assign: lambda: pretty_print_assign(level, ast),
        Assert: lambda: pretty_print_assert(level, ast),
        Assume: lambda: pretty_print_assume(level, ast),
        Skip:   lambda: pretty_print_skip(level, ast),
        Havoc:  lambda: pretty_print_havoc(level, ast)
    }.get(type(ast), lambda: None)()

def pretty_print(ast):
    pretty_print_impl(0, ast)