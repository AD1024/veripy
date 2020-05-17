import ast
import z3
import inspect
from typing import List, Tuple, TypeVar
from veripy.parser.syntax import *
from veripy.parser.parser import parse_assertion, parse_expr
from functools import wraps
from veripy.transformer import *
from functools import reduce
from veripy import typecheck as tc

class VerificationStore:
    def __init__(self):
        self.store = dict()
        self.scope = []
        self.switch = False
    
    def enable_verification(self):
        self.switch = True

    def push(self, scope):
        assert scope not in self.store
        self.scope.append(scope)
        self.store[scope] = {
            'func_attrs' : dict(),
            'vf'         : []
        }
    
    def current_scope(self):
        if self.scope:
            return self.scope[-1]
    
    def push_verification(self, verification_func):
        if self.switch:
            if not self.scope:
                raise Exception('No Scope Defined')
            self.store[self.scope[-1]]['vf'].append(verification_func)
    
    def verify(self, scope):
        if self.switch and self.store:
            print(f'=> Verifying Scope `{scope}`')
            verifications = self.store[scope]
            for f in verifications['vf']:
                f()
            print(f'=> End Of `{scope}`\n')
    
    def verify_all(self):
        if self.switch:
            while self.scope:
                self.verify(self.scope.pop())
    
    def insert_func_attr(self, scope, fname, inputs=[], requires=[], ensures=[]):
        if self.switch and self.store:
            self.store[scope]['func_attrs'][fname] = {
                'inputs' : dict(inputs),
                'ensures': fold_constraints(ensures),
                'requires': fold_constraints(requires)
            }
    
    def get_func_attr(self, fname):
        if self.store:
            return self.store[-1].get('func_attrs', dict()).get(fname)
        return None

STORE = VerificationStore()

def enable_verification():
    STORE.enable_verification()

def scope(name : str):
    STORE.push(name)

def do_verification(name : str):
    STORE.verify(name)

def verify_all():
    STORE.verify_all()

def invariant(inv):
    return parse_assertion(inv)

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
        BinOp(BinOp(combined_invars, BoolOps.And, cond), BoolOps.Implies, p),
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

def emit_smt(translator: Expr2Z3, solver, constraint : Expr, fail_msg : str):
    solver.push()
    const = translator.visit(UnOp(BoolOps.Not, constraint))
    solver.add(const)
    if str(solver.check()) == 'sat':
        model = solver.model()
        raise Exception(f'VerificationViolated on\n{const}\nModel: {model}\n{fail_msg}')
    solver.pop()

def fold_constraints(constraints : List[str]):
    fold_and_str = lambda x, y: BinOp(parse_assertion(x) if isinstance(x, str) else x,
                                BoolOps.And, parse_assertion(y) if isinstance(y, str) else y)
    
    return reduce(fold_and_str, constraints) if len(constraints) >= 2 \
                   else parse_assertion(constraints[0]) \
                        if len(constraints) > 0 else Literal(VBool(True))

def verify_func(func, inputs, ensures, requires):
    code = inspect.getsource(func)
    func_ast = ast.parse(code)
    target_language_ast = StmtTranslator().visit(func_ast)
    sigma = tc.type_check_stmt(dict(inputs), target_language_ast)

    user_precond = fold_constraints(ensures)
    user_postcond = fold_constraints(requires)

    (P, C) = wp(target_language_ast, user_postcond)
    check_P = BinOp(user_precond, BoolOps.Implies, P)

    solver = z3.Solver()
    translator = Expr2Z3(declare_consts(sigma))

    emit_smt(translator, solver, check_P, 'Precondition does not imply wp')
    for c in C:
        emit_smt(translator, solver, c, 'Side condition violated')
    print(f'{func.__name__} Verified!')


def declare_consts(sigma : dict):
    consts = dict()
    for (name, ty) in sigma.items():
        consts[name] = {
            tc.types.TINT: lambda:  z3.Int(name),
            tc.types.TBOOL: lambda: z3.Bool(name)
        }.get(ty)()
    return consts

def verify(inputs: List[Tuple[str, tc.types.SUPPORTED]], requires: List[str]=[], ensures: List[str]=[]):
    def verify_impl(func):
        @wraps(func)
        def caller(*args, **kargs):
            return func(*args, **kargs)
        STORE.insert_func_attr(STORE.current_scope(), func.__name__, inputs, requires, ensures)
        STORE.push_verification(lambda: verify_func(func, inputs, requires, ensures))
        return caller
    return verify_impl