from veripy.parser import syntax

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
            'not' : lambda: syntax.BinOp(BoolOps.Not, e),
            '-'   : lambda: syntax.BinOp(ArithOps.Neg, e)
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
        return syntax.FunctionCall(func_name.makeAST(), [x.makeAST() for x in args], native=False)

class ProcessQuantification(ASTBuilder):
    def __init__(self, tokens):
        self.value = tokens
    
    def makeAST(self):
        quantifier, var, expr = self.value
        if quantifier == 'exists':
            # exists x. Q <==> not forall x. not Q
            return syntax.UnOp(BoolOps.Not,
                        syntax.Quantification(var.makeAST(),
                                                syntax.UnOp(BoolOps.Not, expr.makeAST())))
        else:
            return syntax.Quantification(var.makeAST(), expr.makeAST())