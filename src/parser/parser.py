import sys
import parser.syntax as syntax
from functools import reduce
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
    '==>' : BoolOps.Implies
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

atom = BOOL | INT | VAR

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

def parse_expr(e):
    return expr.parseString(e)[0].makeAST()

def parse_asserstion(assertion):
    return assertion_expr.parseString(assertion)[0].makeAST()

def parse_comparison(comp):
    return arith_comp.parseString(comp)[0].makeAST()

def parse_bool_expr(bexp):
    return bool_expr.parseString(bexp)[0].makeAST()

def parse_arith_expr(aexp):
    return arith_expr.parseString(aexp)[0].makeAST()