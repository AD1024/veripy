import sys
from functools import reduce, wraps
from pyparsing import *
from veripy.parser.ast_builder import *

ParserElement.enablePackrat()

ppc = pyparsing_common
sys.setrecursionlimit(114 * 514)

# Basic Tokens
INT = ppc.integer
INT.setParseAction(ProcessInt)

BOOL = oneOf('True False')
BOOL.setParseAction(ProcessBool)

VAR = ppc.identifier
VAR.setParseAction(ProcessVar)

NEG = Literal('-')
ADD, MINUS = map(Literal, ('+', '-'))
MULT, DIV, MOD = map(Literal, ('*', '//', '%'))

AND, OR, NOT, IMPLIES, IFF = map(Literal, ('and', 'or', 'not', '==>', '<==>'))

LT, LE, GT, GE, EQ, NEQ = map(Literal, ('<', '<=', '>', '>=', '==', '!='))

'''
In case of reusing the rules, make them lazily generated
'''
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
def arith_expr_rules():
    return [
            (NEG, 1, opAssoc.RIGHT, ProcessUnOp),
            (MOD, 2, opAssoc.LEFT, ProcessBinOp),
            (MULT, 2, opAssoc.LEFT, ProcessBinOp),
            (DIV, 2, opAssoc.LEFT, ProcessBinOp),
            (ADD, 2, opAssoc.LEFT, ProcessBinOp),
            (MINUS, 2, opAssoc.LEFT, ProcessBinOp),
    ]

@lazy
def arith_comp_rules():
    return [
            (LT, 2, opAssoc.LEFT, ProcessBinOp),
            (LE, 2, opAssoc.LEFT, ProcessBinOp),
            (GT, 2, opAssoc.LEFT, ProcessBinOp),
            (GE, 2, opAssoc.LEFT, ProcessBinOp),
            (EQ, 2, opAssoc.LEFT, ProcessBinOp),
            (NEQ, 2, opAssoc.LEFT, ProcessBinOp),
    ]

@lazy
def bool_expr_rules():
    return [
            (NOT, 1, opAssoc.RIGHT, ProcessUnOp),
            (AND, 2, opAssoc.LEFT, ProcessBinOp),
            (OR, 2, opAssoc.LEFT, ProcessBinOp),
            (IMPLIES, 2, opAssoc.RIGHT, ProcessBinOp),
            (IFF, 2, opAssoc.RIGHT, ProcessBinOp)
    ]

'''
Syntax of Assertions
'''
expr = Forward()
arith_expr = Forward()
bool_expr = Forward()
assertion_expr = Forward()

built_in_call = VAR + Suppress('(') + expr + Optional(Suppress(',') + expr) + Suppress(')')
built_in_call.setParseAction(ProcessFnCall)

subscript_expr = VAR + OneOrMore(
            (Literal('[') + 
                ((arith_expr + Optional(Literal(':') + Optional(arith_expr))) ^
                (Optional(Optional(arith_expr) + Literal(':')) + arith_expr))
            + Literal(']'))
        )

quantification = (Literal('forall') ^ Literal('exists')) + VAR \
                + (Optional(Suppress(':') + VAR)) + Suppress('::') + assertion_expr
quantification.setParseAction(ProcessQuantification)

atom =  built_in_call    \
        | subscript_expr \
        | BOOL           \
        | INT            \
        | VAR

subscript_expr.setParseAction(ProcessSubscript)

arith_expr <<= (infixNotation(atom, arith_expr_rules()))

arith_comp = infixNotation(arith_expr, arith_comp_rules())

bool_expr <<= infixNotation(
                quantification
                | arith_comp
                | subscript_expr
                | BOOL, bool_expr_rules())

assertion_expr <<= \
            (quantification
            | bool_expr
            | arith_comp)

expr <<= (assertion_expr
        | arith_expr)

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