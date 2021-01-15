import typing
import ast

class Type: pass

class TARR(Type):
    def __init__(self, ty):
        self.ty = ty
    
    def __str__(self):
        return f'List[{self.ty}]'
    
    def __repr__(self):
        return self.__str__()

class TTUP(Type):
    def __init__(self, ty):
        self.ty = ty

class TARROW(Type):
    def __init__(self, t1, t2):
        self.t1 = t1
        self.t2 = t2

class TPROD(Type):
    def __init__(self, *types):
        self.types = tuple(types)

TINT = typing.TypeVar('Int')
TBOOL = typing.TypeVar('Bool')
TSLICE = typing.TypeVar('Slice')
TANY = typing.TypeVar('Any')

def name_to_ast_type(node):
    return {
        'int' : TINT,
        'bool': TBOOL
    }.get(node.id, TANY)

def subscript_to_ast_type(node):
    ty_contr = node.value.id
    if node.slice == None:
        return TANY
    
    ty_arg = to_ast_type(node.slice.value)
    return {
        'List' : TARR,
        'Tuple': TTUP
    }.get(ty_contr, lambda _: TANY)(ty_arg)

def to_ast_type(ty):
    return {
            ast.Name        : name_to_ast_type,
            ast.Subscript   : subscript_to_ast_type
    }.get(type(ty), lambda _: TANY)(ty)

BUILT_IN_FUNC_TYPE = {
    'len' : TARROW(TARR, TINT)
}

SUPPORTED = typing.Union[TINT, TBOOL, TARR]