import typing

class Type: pass

class TARR (Type):
    def __init__(self, ty):
        self.ty = ty

class TARROW (Type):
    def __init__(self, t1, t2):
        self.t1 = t1
        self.t2 = t2

class TPROD(Type):
    def __init__(self, *types):
        self.types = tuple(types)

TINT = typing.TypeVar('Int')
TBOOL = typing.TypeVar('Bool')
TSLICE = typing.TypeVar('Slice')

BUILT_IN_FUNC_TYPE = {
    'len' : TARROW(TARR, TINT)
}

SUPPORTED = typing.Union[TINT, TBOOL, TARR]