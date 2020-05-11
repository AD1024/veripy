from parser.syntax import *
from typecheck.types import *

def type_check_expr(sigma: dict, expected, expr: Expr):
    actual = type_infer_expr(sigma, expr)
    if actual == expected:
        return expected
    else:
        raise TypeError(f'expected type {expected}, actual type {actual}')

def type_infer_expr(sigma: dict, expr: Expr):
    if isinstance(expr, Literal):
        return {
            VBool: TBOOL,
            VInt : TINT,
        }.get(type(expr.value))
    if isinstance(expr, Var):
        assert sigma is not None and expr.name in sigma
        return sigma[expr.name]
    if isinstance(expr, UnOp):
        if expr.op == 'not':
            return type_check_expr(sigma, TBOOL, expr.e)
        if expr.op == '-':
            return type_check_expr(sigma, TINT, expr.e)
    if isinstance(expr, BinOp):
        if isinstance(expr.op, ArithOps):
            type_check_expr(sigma, TINT, expr.e1)
            return type_check_expr(sigma, TINT, expr.e2)
        if isinstance(expr.op, CompOps):
            type_check_expr(sigma, TINT, expr.e1)
            type_check_expr(sigma, TINT, expr.e2)
            return TBOOL
        if isinstance(expr.op, BoolOps):
            type_check_expr(sigma, TBOOL, expr.e1)
            return type_check_expr(sigma, TBOOL, expr.e2)
    raise NotImplementedError(f'Unknown expression: {expr}')