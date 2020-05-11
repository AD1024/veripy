import ast
import z3
import inspect
from typing import List, Tuple, TypeVar
from parser.syntax import *
from parser import parse_asserstion
from functools import wraps
from transformer import *
from functools import reduce
import typecheck as tc

def invariant(inv):
    return parse_asserstion(inv)

def assume(C):
    if not C:
        raise RuntimeError('Assumption Violation')

def subst(this, withThis, inThis):
    if isinstance(inThis, Var):
        if inThis.name == this:
            return withThis
        else:
            return inThis
    if isinstance(inThis, BinOp):
        return BinOp(subst(this, withThis, inThis.e1), inThis.op, subst(this, withThis, inThis.e2))
    if isinstance(inThis, Literal):
        return inThis
    if isinstance(inThis, UnOp):
        return UnOp(inThis.op, subst(this, withThis, inThis.e))

def wp_seq(stmt, Q):
    (p2, c2) = wp(stmt.s2, Q)
    (p1, c1) = wp(stmt.s1, p2)
    return (p1, c1.union(c2))

def wp_if(stmt, Q):
    (p1, c1) = wp(stmt.lb, Q)
    (p2, c2) = wp(stmt.rb, Q)
    return (
        BinOp(
            BinOp(stmt.cond, BoolOps.Implies, p1),
            BoolOps.And,
            BinOp(
                UnOp(BoolOps.Not, stmt.cond), BoolOps.Implies, p2
            )
        ),
        c1.union(c2)
    )

def wp_while(stmt, Q):
    cond = stmt.cond
    s = stmt.body
    invars = stmt.invariants
    combined_invars = Literal (VBool (True)) if not invars \
                      else reduce(lambda i1, i2: BinOp(i1, BoolOps.And, i2), invars)
    
    (p, c) = wp(s, combined_invars)
    return (combined_invars, c.union({
        BinOp(BinOp(combined_invars, BoolOps.And, cond), BoolOps.Implies, cond),
        BinOp(BinOp(combined_invars, BoolOps.And, (UnOp(BoolOps.Not, cond))), BoolOps.Implies, Q)
    }))

def wp(stmt, Q):
    return {
        Skip: lambda: (Q, set()),
        Assign: lambda: (subst(stmt.var, stmt.expr, Q), set()),
        Assert: lambda: (BinOp(Q, BoolOps.And, stmt.e), set()),
        Seq:    lambda: wp_seq(stmt, Q),
        While:  lambda: wp_while(stmt, Q),
        If:     lambda: wp_if(stmt, Q)
    }.get(type(stmt), (None, None))()

def verify_func(func, inputs, pre_cond, post_cond):
    code = inspect.getsource(func)
    func_ast = ast.parse(code)
    target_language_ast = StmtTranslator().visit(func_ast)
    sigma = tc.type_check_stmt(dict(inputs), target_language_ast)
    fold_and_str = lambda x, y: BinOp(parse_asserstion(x), BoolOps.And, parse_asserstion(y))
    fold_and = lambda x, y: BinOp(x, BoolOps.And, y)

    user_precond = reduce(fold_and_str, pre_cond)
    user_postcond = reduce(fold_and_str, post_cond)

    (P, C) = wp(target_language_ast, user_postcond)
    check_P = BinOp(user_precond, BoolOps.Implies, P)
    check_C = reduce(fold_and, C)

    print(check_P)
    print(check_C)


def verify(inputs: List[Tuple[str, tc.types.SUPPORTED]], requires: List[str], ensures: List[str]):
    def verify_impl(func):
        @wraps(func)
        def caller(*args, **kargs):
            return func(args, kargs)
        result = verify_func(func, inputs, requires, ensures)
        return caller
    return verify_impl