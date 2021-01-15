from z3.z3 import Z3
from veripy.verify import invariant, parse_func_types
from veripy import *
from veripy.prettyprint import pretty_print
from typing import List
import inspect
import ast

def func(n):
    y = n
    x = 0
    while y > 0:
        invariant('y >= 0')
        x = x + 1
        y = y - 1
    assert x == n
    return x

def find_max(a : List[int]) -> int:
    i = 0
    j = 0
    while j < len(a):
        invariant('0 <= j <= len(a)')
        if a[i] < a[j]:
            i = j
        j = j + 1
    return i

print(inspect.getsource(func))
AST = ast.parse(inspect.getsource(func))

T_AST = transformer.StmtTranslator().visit(AST)
pretty_print(T_AST)

exprs = [
    ('1 + 2 - 3', dict()),
    ('1 * (2 + 3 // 5121) * 4', dict()),
    ('n >= 1000', dict({'n' : types.TINT})),
    ('(a + b == c) ==> (c == a + b)', {
        'a' : types.TINT,
        'b' : types.TINT,
        'c' : types.TINT
    })
]

for e, sigma in exprs:
    print(f'Checking: {e}')
    print(typecheck.type_infer_expr(sigma, {}, 
        parser.parse_expr(e)
    ))

AST = ast.parse(inspect.getsource(find_max))

T_AST = transformer.StmtTranslator().visit(ast.parse(inspect.getsource(find_max)))
pretty_print(T_AST)
print(parse_func_types(find_max))