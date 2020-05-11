import typecheck
import parser

exprs = [
    ('1 + 2 - 3', None),
    ('1 * (2 + 3 / 5121) * 4', None),
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