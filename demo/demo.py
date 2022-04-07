import veripy
from veripy import *
from veripy import invariant
from typing import List

veripy.enable_verification()
veripy.scope('demo')

@verify(
    requires=['n >= 0'], 
    ensures=['x == n'])
def counter(n) -> int:
    y = n
    x = 0
    while y > 0:
        invariant('x + y == n')
        invariant('y >= 0')
        x = x + 1
        y = y - 1
    return x

veripy.verify_all()