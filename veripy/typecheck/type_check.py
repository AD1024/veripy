from veripy.parser.syntax import *
from veripy.typecheck.types import *

def type_check_stmt(sigma, stmt):
    if isinstance(stmt, Skip):
        return sigma
    if isinstance(stmt, Seq):
        return type_check_stmt(type_check_stmt(sigma, stmt.s1), stmt.s2)
    if isinstance(stmt, Assign):
        ty = type_infer_expr(sigma, stmt.expr)
        if stmt.var not in sigma:
            sigma[stmt.var] = ty
            return sigma
        else:
            if sigma[stmt.var] != ty:
                raise TypeError(f'Mutating Type of {stmt.var}!')
            return sigma
    if isinstance(stmt, If):
        type_check_expr(sigma, TBOOL, stmt.cond)
        return type_check_stmt(type_check_stmt(sigma, stmt.lb), stmt.rb)
    if isinstance(stmt, Assert) or isinstance(stmt, Assume):
        type_check_expr(sigma, TBOOL, stmt.e)
        return sigma
    if isinstance(stmt, While):
        type_check_expr(sigma, TBOOL, stmt.cond)
        for i in stmt.invariants:
            type_check_expr(sigma, TBOOL, i)
        return type_check_stmt(sigma, stmt.body)

def type_check_expr(sigma: dict, expected, expr: Expr):
    actual = type_infer_expr(sigma, expr)
    if actual == expected:
        return expected
    else:
        raise TypeError(f'expected type {expected}, actual type {actual}')

###################
# Type Inference  #
###################

def type_infer_literal(sigma, expr):
    return {
        VBool: TBOOL,
        VInt : TINT,
    }.get(type(expr.value))

def type_infer_UnOp(sigma, expr):
    if expr.op == BoolOps.Not:
        return type_check_expr(sigma, TBOOL, expr.e)
    if expr.op == ArithOps.Neg:
        return type_check_expr(sigma, TINT, expr.e)

def type_infer_BinOp(sigma, expr):
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

def type_infer_Slice(sigma, expr):
    if expr.lower or expr.upper or expr.step:
        if expr.lower:
            type_check_expr(sigma, TINT, expr.lower)
        if expr.upper:
            type_check_expr(sigma, TINT, expr.upper)
        if expr.step:
            type_check_expr(sigma, TINT, expr.step)
        return TSLICE
    raise Exception('Slice must have at least one field that is not None')

def type_infer_FunctionCall(sigma, expr):
    pass

def type_infer_expr(sigma: dict, expr: Expr):
    if isinstance(expr, Literal):
        return type_infer_literal(sigma, expr)
    if isinstance(expr, Var):
        assert sigma is not None and expr.name in sigma
        return sigma[expr.name]
    if isinstance(expr, UnOp):
        return type_infer_UnOp(sigma, expr)
    if isinstance(expr, BinOp):
        return type_infer_BinOp(sigma, expr)
    if isinstance(expr, Slice):
        return type_infer_Slice(sigma, expr)

    raise NotImplementedError(f'Unknown expression: {expr}')
