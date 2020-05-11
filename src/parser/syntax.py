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
        super().__init__(v == 'True')
    
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