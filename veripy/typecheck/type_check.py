from typing import List
from veripy.parser.syntax import *
from veripy.typecheck.types import *
from veripy.built_ins import FUNCTIONS
from veripy.log import log
import typing_utils

def type_check_stmt(sigma : dict, func_sigma : dict, stmt : Stmt):
    if isinstance(stmt, Skip):
        return sigma
    if isinstance(stmt, Seq):
        return type_check_stmt(type_check_stmt(sigma, func_sigma, stmt.s1), func_sigma, stmt.s2)
    if isinstance(stmt, Assign):
        ty = type_infer_expr(sigma, func_sigma, stmt.expr)
        if stmt.var not in sigma:
            sigma[stmt.var] = ty
            return sigma
        else:
            if sigma[stmt.var] == TANY:
                sigma[stmt.var] = ty
            elif sigma[stmt.var] != ty:
                raise TypeError(f'Mutating Type of {stmt.var}!')
            return sigma
    if isinstance(stmt, If):
        type_check_expr(sigma, func_sigma, TBOOL, stmt.cond)
        return type_check_stmt(type_check_stmt(sigma, func_sigma, stmt.lb), func_sigma, stmt.rb)
    if isinstance(stmt, Assert) or isinstance(stmt, Assume):
        type_check_expr(sigma, func_sigma, TBOOL, stmt.e)
        return sigma
    if isinstance(stmt, While):
        type_check_expr(sigma, func_sigma, TBOOL, stmt.cond)
        for i in stmt.invariants:
            type_check_expr(sigma, func_sigma, TBOOL, i)
        return type_check_stmt(sigma, func_sigma, stmt.body)
    if isinstance(stmt, Havoc):
        return sigma
    
    raise NotImplementedError(f'type check not implemented for: {type(stmt)}')

def type_check_expr(sigma: dict, func_sigma : dict, expected, expr: Expr):
    actual = type_infer_expr(sigma, func_sigma, expr)
    if actual == TANY and isinstance(expr, Var):
        sigma[expr.name] = expected
        return expected
    if actual == expected or typing_utils.issubtype(actual, expected):
        return actual
    else:
        raise TypeError(f'{expr}: expected type {expected}, actual type {actual};\
                        issubtype({actual}, {expected})={typing_utils.issubtype(actual, expected)}')

###############################################
#               Type Inference                #
###############################################

def type_infer_Subscript(sigma, func_sigma, expr: Subscript):
    obj = expr.var
    exact_type = type_check_expr(sigma, func_sigma, List, obj)
    # Assume subscripts are integer indices for now
    type_check_expr(sigma, func_sigma, TINT, expr.subscript)
    type_args = typing.get_args(exact_type)
    if type_args:
        return type_args[0]
    else:
        return TANY

def type_infer_literal(sigma, func_sigma, expr: Literal):
    return {
        VBool: TBOOL,
        VInt : TINT,
    }.get(type(expr.value))

def type_infer_UnOp(sigma, func_sigma, expr: UnOp):
    if expr.op == BoolOps.Not:
        return type_check_expr(sigma, func_sigma, TBOOL, expr.e)
    if expr.op == ArithOps.Neg:
        return type_check_expr(sigma, func_sigma, TINT, expr.e)

def type_infer_BinOp(sigma, func_sigma, expr: BinOp):
    if isinstance(expr.op, ArithOps):
        type_check_expr(sigma, func_sigma, TINT, expr.e1)
        return type_check_expr(sigma, func_sigma, TINT, expr.e2)
    if isinstance(expr.op, CompOps):
        type_check_expr(sigma, func_sigma, TINT, expr.e1)
        type_check_expr(sigma, func_sigma, TINT, expr.e2)
        return TBOOL
    if isinstance(expr.op, BoolOps):
        type_check_expr(sigma, func_sigma, TBOOL, expr.e1)
        return type_check_expr(sigma, func_sigma, TBOOL, expr.e2)

def type_infer_Slice(sigma, func_sigma, expr: Slice):
    if expr.lower or expr.upper or expr.step:
        if expr.lower:
            type_check_expr(sigma, func_sigma, TINT, expr.lower)
        if expr.upper:
            type_check_expr(sigma, func_sigma, TINT, expr.upper)
        if expr.step:
            type_check_expr(sigma, func_sigma, TINT, expr.step)
        return TSLICE
    raise Exception('Slice must have at least one field that is not None')

def type_infer_FunctionCall(sigma, func_sigma: typing.Dict[str, TARROW], expr: FunctionCall):
    func_name = expr.func_name
    func_type: TARROW = func_sigma[func_name]
    

def type_infer_quantification(sigma, func_sigma, expr: Quantification):
    sigma[expr.var.name] = TANY if expr.ty is None else expr.ty
    type_check_expr(sigma, func_sigma, TBOOL, expr.expr)
    if sigma[expr.var.name] == TANY:
        raise Exception(f'Cannot infer type for {expr.var} in {expr}')
    expr.ty = sigma[expr.var.name]
    sigma.pop(expr.var.name)
    return TBOOL

def type_infer_expr(sigma: dict, func_sigma : dict, expr: Expr):
    if isinstance(expr, Literal):
        return type_infer_literal(sigma, func_sigma, expr)
    if isinstance(expr, Var):
        assert sigma is not None
        assert expr.name in sigma
        return sigma[expr.name]
    if isinstance(expr, UnOp):
        return type_infer_UnOp(sigma, func_sigma, expr)
    if isinstance(expr, BinOp):
        return type_infer_BinOp(sigma, func_sigma, expr)
    if isinstance(expr, Slice):
        return type_infer_Slice(sigma, func_sigma, expr)
    if isinstance(expr, Quantification):
        return type_infer_quantification(sigma, func_sigma, expr)
    if isinstance(expr, Subscript):
        return type_infer_Subscript(sigma, func_sigma, expr)

    raise NotImplementedError(f'Unknown expression: {expr}')
