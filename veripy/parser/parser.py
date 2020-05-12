import sys
from veripy.parser import syntax
from functools import reduce, wraps
from pyparsing import *

ParserElement.enablePackrat()

ArithOps = syntax.ArithOps
CompOps = syntax.CompOps
BoolOps = syntax.BoolOps

BINOP_DICT = {
    '+' : ArithOps.Add,
    '-' : ArithOps.Minus,
    '*' : ArithOps.Mult,
    '//': ArithOps.IntDiv,

    '<=' : CompOps.Le,
    '<'  : CompOps.Lt,
    '>=' : CompOps.Ge,
    '>'  : CompOps.Gt,
    '==' : CompOps.Eq,
    '!=' : CompOps.Neq,

    'and' : BoolOps.And,
    'or'  : BoolOps.Or,
    'not' : BoolOps.Not,
    '==>' : BoolOps.Implies,
    '<==>': BoolOps.Iff
}

def unpackTokens(tokenlist):
    it = iter(tokenlist)
    while 1:
        try:
            yield (next(it), next(it))
        except StopIteration:
            break

class ASTBuilder:
    def __init__(self, tokens):
        self.value = tokens[0]
    
    def makeAST(self):
        raise NotImplementedError('Abstract Builder')

class ProcessInt(ASTBuilder):
    def makeAST(self):
        return syntax.Literal (syntax.VInt(self.value))

class ProcessBool(ASTBuilder):
    def makeAST(self):
        return syntax.Literal (syntax.VBool(self.value))

class ProcessVar(ASTBuilder):
    def makeAST(self):
        return syntax.Var(self.value)

class ProcessUnOp(ASTBuilder):
    def __init__(self, tokens):
        self.op, self.value = tokens[0]
    
    def makeAST(self):
        e = self.value.makeAST()
        {
            'not' : lambda: syntax.BinOp(Ops.Not, e),
            '-'   : lambda: syntax.BinOp(Ops.Neg, e)
        }.get(self.op, lambda: None)()

class ProcessBinOp(ASTBuilder):
    def makeAST(self):
        e1 = self.value[0].makeAST()
        for (op, e2) in unpackTokens(self.value[1:]):
            e2 = e2.makeAST()
            e1 = syntax.BinOp(e1, BINOP_DICT[op], e2)
        return e1
            

class ProcessSubscript(ASTBuilder):
    def __init__(self, tokens):
        self.var, *self.subscripts = tokens

    def makeAST(self):
        var = self.var.makeAST()
        if not self.subscripts:
            raise Exception('No subscript found')
        
        result = None
        while self.subscripts:
            lbrk, *self.subscripts = self.subscripts
            assert lbrk == '['
            store = []
            while self.subscripts and self.subscripts[0] != ']':
                store.append(self.subscripts[0])
                self.subscripts = self.subscripts[1:]
            if len(store) == 3:
                subscript = syntax.Slice(store[0], store[2])
            elif len(store) == 2:
                fst, snd = store
                if fst == ':':
                    subscript = syntax.Slilce(None, snd)
                else:
                    subscript = syntax.Slice(fst, None)
            else:
                subscript = store[0]
            if result is None:
                result = syntax.Subscript(var, subscript)
            else:
                result = syntax.Subscript(result, subscript)
            if self.subscripts:
                self.subscripts = self.subscripts[1:]
        return result
            

ppc = pyparsing_common
sys.setrecursionlimit(114 * 514)

INT = ppc.integer
INT.setParseAction(ProcessInt)

BOOL = oneOf('True False')
BOOL.setParseAction(ProcessBool)

VAR = ppc.identifier
VAR.setParseAction(ProcessVar)

NEG = Literal('-')
ADD, MINUS = map(Literal, ('+', '-'))
MULT, DIV = map(Literal, ('*', '//'))
# LPAREN, RPAREN = map(Suppress, (''))

AND, OR, NOT, IMPLIES, IFF = map(Literal, ('and', 'or', 'not', '==>', '<==>'))

LT, LE, GT, GE, EQ, NEQ = map(Literal, ('<', '<=', '>', '>=', '==', '!='))

atom = BOOL | INT | VAR

def lazy(func):
    '''
    Make sure the function only evaluates once
    '''
    @wraps(func)
    def wrapper(*args, **kargs):
        store = None
        def ret():
            nonlocal store
            if store is None:
                store = func(*args, **kargs)
            return store
        return ret()
    return wrapper

@lazy
def subscript_expr():
    result = VAR + OneOrMore(
            (Literal('[') + 
                ((arith_expr() + Optional(Literal(':') + Optional(arith_expr()))) ^
                (Optional(Optional(arith_expr()) + Literal(':')) + arith_expr()))
            + Literal(']'))
        )
    result.setParseAction(ProcessSubscript)
    return result

@lazy
def arith_expr():
    return infixNotation(atom, [
            (NEG, 1, opAssoc.RIGHT, ProcessUnOp),
            (MULT, 2, opAssoc.LEFT, ProcessBinOp),
            (DIV, 2, opAssoc.LEFT, ProcessBinOp),
            (ADD, 2, opAssoc.LEFT, ProcessBinOp),
            (MINUS, 2, opAssoc.LEFT, ProcessBinOp),
        ])

@lazy
def arith_comp():
    return infixNotation(arith_expr(), [
        (LT, 2, opAssoc.LEFT, ProcessBinOp),
        (LE, 2, opAssoc.LEFT, ProcessBinOp),
        (GT, 2, opAssoc.LEFT, ProcessBinOp),
        (GE, 2, opAssoc.LEFT, ProcessBinOp),
        (EQ, 2, opAssoc.LEFT, ProcessBinOp),
        (NEQ, 2, opAssoc.LEFT, ProcessBinOp),
    ])

@lazy
def bool_expr():
    return infixNotation(
        arith_comp() | BOOL, [
            (NOT, 1, opAssoc.RIGHT, ProcessUnOp),
            (AND, 2, opAssoc.LEFT, ProcessBinOp),
            (OR, 2, opAssoc.LEFT, ProcessBinOp),
            (IMPLIES, 2, opAssoc.RIGHT, ProcessBinOp),
            (IFF, 2, opAssoc.RIGHT, ProcessBinOp)
        ]
    )

@lazy
def assertion_expr():
    return (bool_expr()) | (arith_comp())

@lazy
def expr():
    return assertion_expr() | arith_expr()

def parse_expr(e):
    return expr().parseString(e)[0].makeAST()

def parse_assertion(assertion):
    return assertion_expr().parseString(assertion)[0].makeAST()

def parse_comparison(comp):
    return arith_comp().parseString(comp)[0].makeAST()

def parse_bool_expr(bexp):
    return bool_expr().parseString(bexp)[0].makeAST()

def parse_arith_expr(aexp):
    return arith_expr().parseString(aexp)[0].makeAST()

def parse_subscript_expr(sexp):
    return subscript_expr().parseString(sexp)[0].makeAST()