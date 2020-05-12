import parser
import inspect
import ast
import veripy
from veripy import *
from veripy import invariant


@verify(
    [('n', types.TINT)], 
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
    inputs=[
        ('a', types.TINT),
        ('b', types.TINT)
    ],
    requires=[
        'a >= 0',
        'b >= 0'
    ],
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
        ('a', types.TINT),
        ('b', types.TINT)
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
        ('a', types.TINT),
        ('b', types.TINT)
    ],
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
        ('a', types.TINT),
        ('b', types.TINT),
        ('c', types.TINT),
    ],
    ensures=[
        'a < b and b < c ==> ans == c',
        'b < a and a < c ==> ans == c',
        'a < c and c < b ==> ans == b',
        'c < a and a < b ==> ans == b',
        'b < c and c < a ==> ans == a',
        'c < b and b < a ==> ans == a'
    ]
)
def max_of_three(a, b, c):
    ans = a
    if ans < b:
        ans = b
    if ans < c:
        ans = c
    return ans

@verify(
    inputs=[
        ('x', types.TINT)
    ],
    requires=[],
    ensures=[
        'ans >= 0'
    ]
)
def absolute_value(x):
    ans = x
    if x < 0:
        ans = -x
    return ans

@verify(
    inputs=[
        ('n', types.TINT)
    ],
    requires=[
        'n >= 0'
    ],
    ensures=[
        'ans == ((n + 1) * n) // 2'
    ]
)
def Summation(n):
    ans = 0
    i = 0
    while i <= n:
        invariant('i <= n + 1')
        invariant('i >= 0 and n >= 0')
        invariant('ans == i * (i - 1) // 2')
        ans = ans + i
        i = i + 1
    return ans