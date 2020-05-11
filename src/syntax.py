from enum import Enum

class Op(Enum):
    Add = 1
    Minus = 2
    Mult = 3
    IntDiv = 4
    Neg = 5

    And = 11
    Or = 12
    Not = 13
    Implies = 14

    Eq = 21
    Neq = 22
    Lt = 23
    Le = 24
    Gt = 25
    Ge = 26


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