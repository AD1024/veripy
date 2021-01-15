import ast
import z3
import inspect
from typing import List, Tuple, TypeVar
from veripy.parser.syntax import *
from veripy.parser.parser import parse_assertion, parse_expr
from functools import wraps
from veripy.transformer import *
from functools import reduce
from veripy.prettyprint import pretty_print
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
    
    def push_verification(self, func_name, verification_func):
        if self.switch:
            if not self.scope:
                raise Exception('No Scope Defined')
            self.store[self.scope[-1]]['vf'].append((func_name, verification_func))
    
    def verify(self, scope, ignore_err):
        if self.switch and self.store:
            print(f'=> Verifying Scope `{scope}`')
            verifications = self.store[scope]
            for f_name, f in verifications['vf']:
                try:
                    f()
                except Exception as e:
                    print(f'Exception encountered while verifying {scope}::{f_name}')
                    if not ignore_err:
                        raise e
                    else:
                        print(e)
            print(f'=> End Of `{scope}`\n')
    
    def verify_all(self, ignore_err):
        if self.switch:
            try:
                while self.scope:
                    self.verify(self.scope.pop(), ignore_err)
            except Exception as e:
                if not ignore_err:
                    raise e
                else:
                    print(e)           
    
    def insert_func_attr(self, scope, fname, inputs=[], inputs_map={}, returns=tc.types.TANY, requires=[], ensures=[]):
        if self.switch and self.store:
            self.store[scope]['func_attrs'][fname] = {
                'inputs' : inputs_map,
                'ensures': ensures,
                'requires': requires,
                'returns' : returns,
                'func_type' : tc.types.TARROW(tc.types.TPROD(lambda i: i[1], inputs), returns)
            }
    
    def get_func_attr(self, fname):
        if self.store:
            return self.store[-1].get('func_attrs', dict()).get(fname)
        return None

    def current_func_attrs(self):
        if self.scope:
            return self.store[self.scope[-1]]['func_attrs']
    
    def get_func_attrs(self, scope, fname):
        if self.scope:
            return self.store[scope]['func_attrs'][fname]

STORE = VerificationStore()

def enable_verification():
    STORE.enable_verification()

def scope(name : str):
    STORE.push(name)

def do_verification(name : str, ignore_err : bool=True):
    STORE.verify(name, ignore_err)

def verify_all(ignore_err : bool=True):
    STORE.verify_all(ignore_err)

def invariant(inv):
    return parse_assertion(inv)

def assume(C):
    if not C:
        raise RuntimeError('Assumption Violation')

def wp_seq(sigma, stmt, Q):
    (p2, c2) = wp(sigma, stmt.s2, Q)
    (p1, c1) = wp(sigma, stmt.s1, p2)
    return (p1, c1.union(c2))

def wp_if(sigma, stmt, Q):
    (p1, c1) = wp(sigma, stmt.lb, Q)
    (p2, c2) = wp(sigma, stmt.rb, Q)
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

def wp(sigma, stmt, Q):
    return {
        Skip:   lambda: (Q, set()),
        Assume:  lambda: (BinOp(stmt.e, BoolOps.Implies, Q), set()),
        Assign: lambda: (subst(stmt.var, stmt.expr, Q), set()),
        Assert: lambda: (BinOp(Q, BoolOps.And, stmt.e), set()),
        Seq:    lambda: wp_seq(sigma, stmt, Q),
        If:     lambda: wp_if(sigma, stmt, Q),
        Havoc:  lambda: (Quantification(Var(stmt.var + '$0'), subst(stmt.var, Var(stmt.var + '$0'), Q), ty=sigma[stmt.var]), set())
    }.get(type(stmt), lambda: raise_exception(f'wp not implemented for {type(stmt)}'))()

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
    if len(constraints) >= 2:
        return reduce(fold_and_str, constraints)
    elif len(constraints) == 1:
        return parse_assertion(constraints[0])
    else:
        return Literal(VBool(True))

def verify_func(func, scope, inputs, requires, ensures):
    code = inspect.getsource(func)
    func_ast = ast.parse(code)
    target_language_ast = StmtTranslator().visit(func_ast)
    func_attrs = STORE.get_func_attrs(scope, func.__name__)
    sigma = tc.type_check_stmt(func_attrs['inputs'], func_attrs, target_language_ast)

    user_precond = fold_constraints(requires)
    user_postcond = fold_constraints(ensures)

    tc.type_check_expr(sigma, func_attrs, TBOOL, user_precond)
    tc.type_check_expr(sigma, func_attrs, TBOOL, user_postcond)

    (P, C) = wp(sigma, target_language_ast, user_postcond)
    check_P = BinOp(user_precond, BoolOps.Implies, P)

    solver = z3.Solver()
    translator = Expr2Z3(declare_consts(sigma))

    emit_smt(translator, solver, check_P, f'Precondition does not imply wp at {func.__name__}')
    for c in C:
        emit_smt(translator, solver, c, f'Side condition violated at {func.__name__}')
    print(f'{func.__name__} Verified!')


def declare_consts(sigma : dict):
    consts = dict()
    for (name, ty) in sigma.items():
        if type(ty) != dict:
            consts[name] = {
                tc.types.TINT: lambda:  z3.Int(name),
                tc.types.TBOOL: lambda: z3.Bool(name)
            }.get(ty)()
    return consts

def parse_func_types(func, inputs=[]):
    code = inspect.getsource(func)
    func_ast = ast.parse(code)
    func_def = func_ast.body[0]
    result = []
    provided = dict(inputs)
    for i in func_def.args.args:
        if i.annotation:
            result.append(tc.types.to_ast_type(i.annotation))
        else:
            result.append(provided.get(i.arg, tc.types.TANY))
        provided[i.arg] = result[-1]

    if func_def.returns:
        ret_type = tc.types.to_ast_type(func_def.returns)
        return (result, provided, ret_type)
    else:
        raise Exception('Return annotation is required for verifying functions')

def verify(inputs: List[Tuple[str, tc.types.SUPPORTED]]=[], requires: List[str]=[], ensures: List[str]=[]):
    def verify_impl(func):
        @wraps(func)
        def caller(*args, **kargs):
            return func(*args, **kargs)
        types = parse_func_types(func, inputs=inputs)
        scope = STORE.current_scope()
        STORE.insert_func_attr(scope, func.__name__, types[0], types[1], types[2], requires, ensures)
        STORE.push_verification(func.__name__, lambda: verify_func(func, scope, inputs, requires, ensures))
        return caller
    return verify_impl