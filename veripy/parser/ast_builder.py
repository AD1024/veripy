from veripy.parser import syntax
from veripy.typecheck.types import to_ast_type

ArithOps = syntax.ArithOps
CompOps = syntax.CompOps
BoolOps = syntax.BoolOps

BINOP_DICT = {
    '+' : ArithOps.Add,
    '-' : ArithOps.Minus,
    '*' : ArithOps.Mult,
    '//': ArithOps.IntDiv,
    '%' : ArithOps.Mod,

    '<=' : CompOps.Le,
    '<'  : CompOps.Lt,
    '>=' : CompOps.Ge,
    '>'  : CompOps.Gt,
    '==' : CompOps.Eq,
    '!=' : CompOps.Neq,

    'and' : BoolOps.And,
    'or'  : BoolOps.Or,
    '==>' : BoolOps.Implies,
    '<==>': BoolOps.Iff
}

UNOP_DICT = {
    'not' : BoolOps.Not,
    '-'   : ArithOps.Neg
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
        return syntax.UnOp(UNOP_DICT[self.op], e)

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
                    subscript = syntax.Slilce(None, snd.makeAST())
                else:
                    subscript = syntax.Slice(fst.makeAST(), None)
            else:
                subscript = store[0].makeAST()
            if result is None:
                result = syntax.Subscript(var, subscript)
            else:
                result = syntax.Subscript(result, subscript)
            if self.subscripts:
                self.subscripts = self.subscripts[1:]
        return result

class ProcessFnCall(ASTBuilder):
    def __init__(self, tokens):
        self.value = tokens

    def makeAST(self):
        func_name, *args = self.value
        func_name = func_name.makeAST()
        if func_name.name in UNOP_DICT:
            return syntax.UnOp(UNOP_DICT[func_name.name], args[0].makeAST())
        return syntax.FunctionCall(func_name, [x.makeAST() for x in args], native=False)

class ProcessQuantification(ASTBuilder):
    def __init__(self, tokens):
        self.value = tokens
    
    def makeAST(self):
        import veripy.transformer as trans
        ty = None
        if len(self.value) == 3:
            quantifier, var, expr = self.value
        elif len(self.value) == 4:
            quantifier, var, ty, expr = self.value
        if ty is not None:
            ty = ty.makeAST()
            ty = to_ast_type(ty.name)

        ori = var.makeAST()
        bounded = syntax.Var(ori.name + '$$0')
        e = trans.subst(ori.name, bounded, expr.makeAST())
        if quantifier == 'exists':
            # exists x. Q <==> not forall x. not Q
            return syntax.UnOp(BoolOps.Not,
                        syntax.Quantification(bounded,
                                                syntax.UnOp(BoolOps.Not, e), ty=ty))
        else:
            return syntax.Quantification(bounded, e, ty=ty)