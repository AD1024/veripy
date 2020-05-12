import parser
import inspect
import ast
from veripy import *


@verify(
    [('n', typecheck.types.TINT)], 
    ['n >= 0'], 
    ['x == n'])
def test_func(n):
    y = n
    x = 0
    while y > 0:
        invariant('x + y == n')
        invariant('y >= 0')
        x = x + 1
        y = y - 1
    return x

@verify(
    inputs=[('a', typecheck.types.TINT),
     ('b', typecheck.types.TINT)],
    requires=['a >= 0', 'b >= 0'],
    ensures=['ans == a * b']
)
def test_func1(a, b):
    ans = 0
    n = a
    while n > 0:
        invariant('n >= 0')
        invariant('ans == (a - n) * b')
        ans = ans + b
        n = n - 1
    return ans

@verify(
    inputs=[
        ('a', typecheck.types.TINT),
        ('b', typecheck.types.TINT)
    ],
    requires=[
        'a >= 0',
        'b >= 0'
    ],
    ensures=[
        'ans == a * b'
    ]
)
def test_func2(a, b):
    ans = 0
    i = a
    while i > 0:
        invariant('i >= 0')
        invariant('a >= 0')
        invariant('b >= 0')
        invariant('ans == (a - i) * b')
        j = b
        while j > 0:
            invariant('i > 0')
            invariant('j >= 0')
            invariant('a >= 0')
            invariant('b >= 0')
            invariant('(i > 0) ==> (ans == ((a - i) * b) + (b - j))')
            ans = ans + 1
            j = j - 1
        i = i - 1
    return ans

@verify(
    inputs=[
        ('a', typecheck.types.TINT),
        ('b', typecheck.types.TINT)
    ],
    requires=[],
    ensures=[
        'a < b ==> (ans == b)',
        'b <= a ==> (ans == a)',
    ]
)
def Max_Func(a, b):
    ans = a
    if a < b:
        ans = b
    return ans

@verify(
    inputs=[
        ('n', typecheck.types.TINT)
    ],
    requires=[
        'n >= 0'
    ],
    ensures=[
        'ans == ((0 + n) * n) // 2'
    ]
)
def Summation(n):
    ans = 0
    i = 0
    while i <= n:
        invariant('i <= n + 1')
        invariant('i >= 0')
        invariant('n >= 0')
        invariant('ans >= 0')
        invariant('i > 0 ==> ans == ((0 + (i - 1)) * (i - 1)) // 2')
        ans = ans + i
        i = i + 1
    return ans