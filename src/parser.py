import sys
import syntax
from functools import reduce
from pyparsing import *

ParserElement.enablePackrat()

Ops = syntax.Op

BINOP_DICT = {
    '+' : Ops.Add,
    '-' : Ops.Minus,
    '*' : Ops.Mult,
    '//': Ops.IntDiv,

    '<=' : Ops.Le,
    '<'  : Ops.Lt,
    '>=' : Ops.Ge,
    '>'  : Ops.Gt,
    '==' : Ops.Eq,
    '!=' : Ops.Neq,

    'and' : Ops.And,
    'or'  : Ops.Or,
    'not' : Ops.Not,
    '==>' : Ops.Implies
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
        return syntax.Literal (syntax.VInt(self.value[0]))

class ProcessBool(ASTBuilder):
    
    def makeAST(self):
        return syntax.Literal (syntax.VBool(self.value[0]))

class ProcessVar(ASTBuilder):
    
    def makeAST(self):
        return syntax.Literal (syntax.Var(self.value[0]))

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

AND, OR, NOT, IMPLIES = map(Literal, ('and', 'or', 'not', '==>'))

LT, LE, GT, GE, EQ, NEQ = map(Literal, ('<', '<=', '>', '>=', '==', '!='))

atom = INT | VAR

arith_expr = infixNotation(atom, [
    (NEG, 1, opAssoc.RIGHT, ProcessUnOp),
    (MULT, 2, opAssoc.LEFT, ProcessBinOp),
    (DIV, 2, opAssoc.LEFT, ProcessBinOp),
    (ADD, 2, opAssoc.LEFT, ProcessBinOp),
    (MINUS, 2, opAssoc.LEFT, ProcessBinOp),
])

arith_comp = infixNotation(arith_expr,[
    (LT, 2, opAssoc.LEFT, ProcessBinOp),
    (LE, 2, opAssoc.LEFT, ProcessBinOp),
    (GT, 2, opAssoc.LEFT, ProcessBinOp),
    (GE, 2, opAssoc.LEFT, ProcessBinOp),
    (EQ, 2, opAssoc.LEFT, ProcessBinOp),
    (NEQ, 2, opAssoc.LEFT, ProcessBinOp),
])

bool_expr = infixNotation(
    arith_comp | BOOL, [
        (NOT, 1, opAssoc.RIGHT, ProcessUnOp),
        (AND, 2, opAssoc.LEFT, ProcessBinOp),
        (OR, 2, opAssoc.LEFT, ProcessBinOp),
        (IMPLIES, 2, opAssoc.LEFT, ProcessBinOp)
    ]
)

assertion_expr = bool_expr | arith_comp
expr = assertion_expr | arith_expr