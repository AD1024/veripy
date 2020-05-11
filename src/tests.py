import typecheck
import parser
import inspect
import ast
import transformer
from prettyprint import pretty_print
from verify import verify, assume, invariant

def func(n):
    y = n
    x = 0
    while y > 0:
        invariant('y >= 0')
        x = x + 1
        y = y - 1
    assert x == n
    return x

print(inspect.getsource(func))
AST = ast.parse(inspect.getsource(func))

T_AST = transformer.StmtTranslator().visit(AST)
pretty_print(T_AST)

@verify([('n', typecheck.types.TINT)], ['n >= 10'], ['x == n'])
def test_func(n):
    y = n
    x = 0
    while y > 0:
        invariant('y >= 0')
        x = x + 1
        y = y - 1
    return x

exprs = [
    ('1 + 2 - 3', dict()),
    ('1 * (2 + 3 / 5121) * 4', dict()),
    ('(a + b == c) ==> (c == a + b)', {
        'a' : typecheck.types.TINT,
        'b' : typecheck.types.TINT,
        'c' : typecheck.types.TINT
    })
]

for e, sigma in exprs:
    print(f'Checking: {e}')
    print(typecheck.type_infer_expr(sigma, 
        parser.parse_expr(e)
    ))