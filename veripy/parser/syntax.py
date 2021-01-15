from enum import Enum

class Op: pass

class ArithOps(Op, Enum):
    Add = '+'
    Minus = '-'
    Mult = '*'
    IntDiv = '/'
    Neg = '-'
    Mod = '%'

class CompOps(Op, Enum):
    Eq = '='
    Neq = '!='
    Lt = '<'
    Le = '<='
    Gt = '>'
    Ge = '>='

class BoolOps(Op, Enum):
    And = 'and'
    Or = 'or'
    Not = 'not'
    Implies = '==>'
    Iff = '<==>'


class Value:
    __slots__ = ['v']
    def __init__(self, v):
        self.v = v

class VInt(Value):
    def __init__(self, v):
        super().__init__(int(v))
    
    def __str__(self):
        return f'VInt {self.v}'
    
    def __repr__(self):
        return f'VInt {self.v}'

class VBool(Value):
    def __init__(self, v):
        super().__init__(v == 'True' or v == True)
    
    def __str__(self):
        return f'VBool {self.v}'
    
    def __repr__(self):
        return f'VBool {self.v}'

class Expr: pass

class Var(Expr):
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return f'(Var {self.name})'
    
    def variables(self):
        return {self.name}

class Literal(Expr):
    def __init__(self, v : Value):
        self.value = v
    
    def __repr__(self):
        return f'(Literal {self.value})'
    
    def variables(self):
        return set()

class BinOp(Expr):
    def __init__(self, l : Expr, op : Op, r : Expr):
        self.e1 = l
        self.e2 = r
        self.op = op
    
    def __repr__(self):
        return f'(BinOp {self.e1} {self.op} {self.e2})'
    
    def variables(self):
        return {*self.e1.variables(), *self.e2.variables()}

class UnOp(Expr):
    def __init__(self, op : Op, expr : Expr):
        self.op = op
        self.e = expr
    
    def __repr__(self):
        return f'(UnOp {self.op} {self.e})'
    
    def variables(self):
        return {*self.e.variables()}

class Pi(Expr):
    def __init__(self, e1, e2):
        self.car = e1
        self.cdr = e2
    
    def __repr__(self):
        return f'(Pi {self.e1} {self.e2})'
    
    def variables(self):
        return {*self.e1.variables, *self.e2.variables}

class Slice(Expr):
    def __init__(self, lower, upper, step):
        self.lower = lower if lower is not None else Literal(VInt(0))
        self.upper = upper
        self.step  = step if step is not None else Literal(VInt(1))
    
    def __repr__(self):
        return f'(Slice {self.lower} -> {self.upper} (step={self.step}))'

class FunctionCall(Expr):
    def __init__(self, func_name, args, native=True):
        self.func_name = func_name
        self.args = args
        self.native = native
    
    def __repr__(self):
        return f'(Call {self.func_name} with ({self.args}))'
    
    def variables(self):
        return set()

class Subscript(Expr):
    def __init__(self, var, subscript):
        self.var = var
        self.subscript = subscript
    
    def __repr__(self):
        return f'(Subscript {self.var} {self.subscript})'
    
    def variables(self):
        return self.var.variables().union(self.subscript.variables())

class Quantification(Expr):
    '''
    Since we are using SMT solver, we convert existential quantification
    to the negation of a universal quantification.
    '''
    def __init__(self, var, expr, ty=None):
        self.var = var
        self.ty = ty
        self.expr = expr
    
    def __repr__(self):
        return f'(∀{self.var} : {self.ty}. {self.expr})'

'''
Translating ASTs
'''
class Stmt: pass

class Skip(Stmt):
    def __repr__(self):
        return f'(Skip)'
    
    def variables(self):
        return set()

class Assign(Stmt):
    def __init__(self, var, expr):
        self.var = var
        self.expr = expr
    
    def __repr__(self):
        return f'(Assign {self.var} {self.expr})'
    
    def variables(self):
        return {self.var, *self.expr.variables()}

class If(Stmt):
    def __init__(self, cond_expr : Expr, lb_stmt : Stmt, rb_stmt : Stmt):
        self.cond = cond_expr
        self.lb = lb_stmt if lb_stmt is not None else Skip()
        self.rb = rb_stmt if rb_stmt is not None else Skip()
    
    def __repr__(self):
        return f'(If {self.cond} {self.lb} {self.rb})'
    
    def variables(self):
        return {*self.cond.variables(), *self.lb.variables(), *self.rb.variables()}

class Seq(Stmt):
    def __init__(self, s1 : Stmt, s2 : Stmt):
        self.s1 = s1 if s1 is not None else Skip()
        self.s2 = s2 if s2 is not None else Skip()
    
    def __repr__(self):
        return f'(Seq {self.s1} {self.s2})'
    
    def variables(self):
        return {*self.s1.variables(), *self.s2.variables()}

class Assume(Stmt):
    def __init__(self, e : Expr):
        self.e = e
    
    def __repr__(self):
        return f'(Assume {self.e})'
    
    def variables(self):
        return {*self.e.variables()}

class Assert(Stmt):
    def __init__(self, e):
        self.e = e
    
    def __repr__(self):
        return f'(Assert {self.e})'
    
    def variables(self):
        return {*self.e.variables()}

class While(Stmt):
    def __init__(self, invs, cond : Expr, body : Stmt):
        self.cond = cond
        self.invariants = invs
        self.body = body if body is not None else Skip()

    def __repr__(self):
        return f'(While {self.cond} {self.body})'
    
    def variables(self):
        return {*self.body.variables()}

class Havoc(Stmt):
    def __init__(self, var):
        self.var = var
    
    def __repr__(self):
        return f'(Havoc {self.var})'
    
    def variables(self):
        return set()