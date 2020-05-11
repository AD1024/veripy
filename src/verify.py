import ast
import z3
import inspect
from typing import List
from parser.syntax import *
from functools import wraps

def assume(C):
    if not C:
        raise RuntimeError('Assumption Violation')

def verify_func(func):
    code = inspect.getsource(func)
    func_ast = ast.parse(code)

def verify(requires: List[str], ensures: List[str]):
    def verify_impl(func):
        @wraps(func)
        def caller(*args, **kargs):
            return func(args, kargs)
        result = verify_func(func)
        return caller
    return verify_impl