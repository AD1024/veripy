import ast
import z3
from veripy.parser.syntax import *
from veripy.parser.parser import parse_assertion
from veripy.built_ins import BUILT_INS

def raise_exception(msg):
    raise Exception(msg)

class ExprTranslator:

    def fold_binops(self, op, values):
        result = BinOp(self.visit(values[0]), op, self.visit(values[1]))
        for e in values[2:]:
            result = BinOp(result, op, self.visit(e))
        return result

    def visit_Name(self, node):
        return Var(node.id)
    
    def visit_Num(self, node):
        return Literal (VInt (node.n))
    
    def visit_NameConstant(self, node):
        return Literal (VBool (node.value))

    def visit_Expr(self, node):
        return self.visit(node.value)
    
    def visit_BoolOp(self, node):
        op = {
                ast.And: lambda: BoolOps.And,
                ast.Or: lambda: BoolOps.Or,
                ast.Not: lambda: BoolOps.Not
             }.get(node.op)
        return self.fold_binops(op, node.values)
    
    def visit_Compare(self, node):
        '''
        Do not support multiple comparators
        because the expansion will cause inconsistent interpretation if
        parsed using PEP standard.
        Consider `1 in (1, 2) == True`.
        '''
        lv = self.visit(node.left)
        rv = self.visit(node.comparators[0])
        op = node.ops[0]
        return {
            ast.Lt: lambda: BinOp(lv, CompOps.Lt, rv),
            ast.LtE: lambda: BinOp(lv, CompOps.Le, rv),
            ast.Gt: lambda: BinOp(lv, CompOps.Gt, rv),
            ast.GtE: lambda: BinOp(lv, CompOps.Ge, rv),
            ast.Eq: lambda: BinOp(lv, CompOps.Eq, rv),
            ast.NotEq: lambda: BinOp(lv, CompOps.Neq, rv),
        }.get(type(op), lambda: raise_exception(f'Not Supported: {op}'))()

    def visit_BinOp(self, node):
        lv = self.visit(node.left)
        rv = self.visit(node.right)
        return {
            ast.Add: lambda: BinOp(lv, ArithOps.Add, rv),
            ast.Sub: lambda: BinOp(lv, ArithOps.Minus, rv),
            ast.Mult: lambda: BinOp(lv, ArithOps.Mult, rv),
            ast.Div: lambda: BinOp(lv, ArithOps.IntDiv, rv)
        }.get(type(node.op), lambda: raise_exception(f'Not Supported: {node.op}'))()
    
    def visit(self, node):
        return {
                ast.BinOp: lambda: self.visit_BinOp(node),
                ast.Name: lambda: self.visit_Name(node),
                ast.Compare: lambda: self.visit_Compare(node),
                ast.BoolOp: lambda: self.visit_BoolOp(node),
                ast.NameConstant: lambda: self.visit_NameConstant(node),
                ast.Num: lambda: self.visit_Num(node)
            }.get(type(node), lambda: raise_exception(f'Expr not supported: {node}'))()

class StmtTranslator:

    def __init__(self):
        self.expr_translator = ExprTranslator()

    def make_seq(self, stmts):
        if stmts:
            hd, *stmts = stmts
            t_node = self.visit(hd)
            while stmts:
                t2_node, stmts = self.visit(stmts[0]), stmts[1:]
                t_node = Seq(t_node, t2_node)
            if not isinstance(t_node, Seq):
                return Seq(t_node, Skip())
            return t_node
        else:
            return Skip()
    
    def visit_Call(self, node):
        func = node.func.id
        if func in BUILT_INS:
            if func == 'assume':
                return Assume(parse_assertion(node.args[0].s))
            if func == 'invariant':
                return parse_assertion(node.args[0].s)
        else:
            raise Exception('Currently function call is not supported')
    
    def visit_FunctionDef(self, node):
        return self.make_seq(node.body)
    
    def visit_Module(self, node):
        return self.make_seq(node.body)
    
    def visit_Return(self, node):
        return Skip()

    def visit_Assign(self, node):
        varname = node.targets[0].id
        expr = self.expr_translator.visit(node.value)
        return Assign(varname, expr)

    def visit_While(self, node):
        cond = self.expr_translator.visit(node.test)
        is_invariant = lambda y: isinstance(y, ast.Expr)\
                                and isinstance(y.value, ast.Call)\
                                and y.value.func.id == 'invariant'
        invars = [self.visit_Call(x.value) for x in filter(is_invariant, node.body)]
        body = self.make_seq(list(filter(lambda x: True if not isinstance(x, ast.Expr) or not isinstance(x.value, ast.Call)
                                                        else x.value.func.id not in BUILT_INS, node.body)))
        return While(invars, cond, body)
    
    def visit_If(self, node):
        cond = self.expr_translator.visit(node.test)
        lb = self.make_seq(node.body)
        rb = self.make_seq(node.orelse)
        return If(cond, lb, rb)
    
    def visit_Assert(self, node):
        return Assert(self.expr_translator.visit(node.test))
    
    def visit(self, node):
        return {
                ast.FunctionDef: lambda: self.visit_FunctionDef(node),
                ast.Module:      lambda: self.visit_Module(node),
                ast.If:          lambda: self.visit_If(node),
                ast.While:       lambda: self.visit_While(node),
                ast.Assert:      lambda: self.visit_Assert(node),
                ast.Assign:      lambda: self.visit_Assign(node),
                ast.Return:      lambda: self.visit_Return(node),
            }.get(type(node), lambda: raise_exception(f'Stmt not supported: {node}'))()


class Expr2Z3:

    def __init__(self, name_dict: dict):
        self.name_dict = name_dict

    def visit_Literal(self, lit):
        v = lit.value
        return {
            VBool: lambda: v.v,
            VInt: lambda: v.v
        }.get(type(v), lambda: raise_exception(f'Unsupported data: {v}'))()

    def visit_Var(self, node):
        return self.name_dict[node.name]
    
    def visit_BinOp(self, node):
        c1 = self.visit(node.e1)
        c2 = self.visit(node.e2)
        return {
            ArithOps.Add:       lambda: c1 + c2,
            ArithOps.Minus:     lambda: c1 - c2,
            ArithOps.Mult:      lambda: c1 * c2,
            ArithOps.IntDiv:    lambda: c1 / c2,
            
            BoolOps.And:        lambda: z3.And(c1, c2),
            BoolOps.Or:         lambda: z3.Or(c1, c2),
            BoolOps.Implies:    lambda: z3.Implies(c1, c2),
            BoolOps.Iff:        lambda: z3.And(z3.Implies(c1, c2), z3.Implies(c2, c1)),

            CompOps.Eq:         lambda: c1 == c2,
            CompOps.Neq:        lambda: z3.Not(c1 == c2),
            CompOps.Gt:         lambda: c1 > c2,
            CompOps.Ge:         lambda: c1 >= c2,
            CompOps.Lt:         lambda: c1 < c2,
            CompOps.Le:         lambda: c1 <= c2
        }.get(node.op, lambda: raise_exception(f'Unsupported Operator: {node.op}'))()
    
    def visit_UnOp(self, node):
        c = self.visit(node.e)
        return {
            ArithOps.Neg: lambda: -c,
            BoolOps.Not:  lambda: z3.Not(c)
        }.get(node.op, lambda: raise_exception(f'Unsupported Operator: {node.op}'))()

    def visit(self, expr):
        return {
            Literal: lambda: self.visit_Literal(expr),
            Var:     lambda: self.visit_Var(expr),
            BinOp:   lambda: self.visit_BinOp(expr),
            UnOp:    lambda: self.visit_UnOp(expr)
        }.get(type(expr), lambda: raise_exception(f'Unsupported AST: {expr}'))()