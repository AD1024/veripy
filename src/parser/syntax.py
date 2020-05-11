from enum import Enum

class Op: pass

class ArithOps(Op, Enum):
    Add = '+'
    Minus = '-'
    Mult = '*'
    IntDiv = '//'
    Neg = '-'

class CompOps(Op, Enum):
    Eq = '=='
    Neq = '!='
    Lt = '<'
    Le = '<='
    Gt = '>'
    Ge = '>='

class BoolOps(Op, Enum):
    And = '&&'
    Or = '||'
    Not = '!'
    Implies = '==>'


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
        return f'Var {self.name}'

class Literal(Expr):
    def __init__(self, v : Value):
        self.value = v
    
    def __repr__(self):
        return f'(Literal {self.value})'

class BinOp(Expr):
    def __init__(self, l : Expr, op : Op, r : Expr):
        self.e1 = l
        self.e2 = r
        self.op = op
    
    def __repr__(self):
        return f'(BinOp {self.e1} {self.op} {self.e2})'

class UnOp(Expr):
    def __init__(self, op : Op, expr : Expr):
        self.op = op
        self.e = expr
    
    def __repr__(self):
        return f'(UnOp {self.op} {self.e})'

'''
Translating ASTs
'''
class Stmt: pass

class Skip(Stmt):
    def __repr__(self):
        return f'(Skip)'

class Assign(Stmt):
    def __init__(self, var, expr):
        self.var = var
        self.expr = expr
    
    def __repr__(self):
        return f'(Assign {self.var} {self.expr})'

class If(Stmt):
    def __init__(self, cond_expr : Expr, lb_stmt : Stmt, rb_stmt : Stmt):
        self.cond = cond_expr
        self.lb = lb_stmt if lb_stmt is not None else Skip()
        self.rb = rb_stmt if rb_stmt is not None else Skip()
    
    def __repr__(self):
        return f'(If {self.cond} {self.lb} {self.rb})'

class Seq(Stmt):
    def __init__(self, s1 : Stmt, s2 : Stmt):
        self.s1 = s1 if s1 is not None else Skip()
        self.s2 = s2 if s2 is not None else Skip()
    
    def __repr__(self):
        return f'(Seq {self.s1} {self.s2})'

class Assume(Stmt):
    def __init__(self, e : Expr):
        self.e = e
    
    def __repr__(self):
        return f'(Assume {self.e})'

class Assert(Stmt):
    def __init__(self, e):
        self.e = e
    
    def __repr__(self):
        return f'(Assert {self.e})'

class While(Stmt):
    def __init__(self, cond : Expr, body : Stmt):
        self.cond = cond
        self.body = body if body is not None else Skip()

    def __repr__(self):
        return f'(While {self.cond} {self.body})'