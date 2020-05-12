import typing

class Type: pass

class TARR (Type):
    def __init__(self, ty):
        self.ty = ty

TINT = typing.TypeVar('Int')
TBOOL = typing.TypeVar('Bool')

SUPPORTED = typing.Union[TINT, TBOOL, TARR]