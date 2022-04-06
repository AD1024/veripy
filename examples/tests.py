import parser
import inspect
import ast
import veripy
from veripy import *
from veripy import invariant
from typing import List

veripy.enable_verification()
veripy.scope('test')

veripy.scope('loops')

@verify(
    requires=['n >= 0'], 
    ensures=['x == n'])
def test_func(n) -> int:
    y = n
    x = 0
    while y > 0:
        invariant('x + y == n')
        invariant('y >= 0')
        x = x + 1
        y = y - 1
    return x

@verify(
    requires=[
        'a >= 0',
        'b >= 0'
    ],
    ensures=['ans == a * b']
)
def test_func1(a : int, b : int) -> int:
    ans = 0
    n = a
    while n > 0:
        invariant('n >= 0')
        invariant('ans == (a - n) * b')
        ans = ans + b
        n = n - 1
    return ans

@verify(
    requires=[
        'a >= 0',
        'b >= 0'
    ],
    ensures=[
        'ans == a * b'
    ]
)
def test_func2(a : int, b : int) -> int:
    ans = 0
    i = a
    while i > 0:
        invariant('i >= 0')
        invariant('a >= 0')
        invariant('b >= 0')
        invariant('ans == (a - i) * b')
        j = b
        while j > 0:
            invariant('j >= 0')
            invariant('(i > 0) ==> (ans == ((a - i) * b) + (b - j))')
            ans = ans + 1
            j = j - 1
        i = i - 1
    return ans

veripy.scope('if-then-else')

@verify(
    ensures=[
        'a < b ==> (ans == b)',
        'b <= a ==> (ans == a)',
    ]
)
def Max_Func(a : int, b : int) -> int:
    ans = a
    if a < b:
        ans = b
    return ans

@verify(
    ensures=[
        'a < b and b < c ==> ans == c',
        'b < a and a < c ==> ans == c',
        'a < c and c < b ==> ans == b',
        'c < a and a < b ==> ans == b',
        'b < c and c < a ==> ans == a',
        'c < b and b < a ==> ans == a'
    ]
)
def max_of_three(a : int, b : int, c : int) -> int:
    ans = a
    if ans < b:
        ans = b
    if ans < c:
        ans = c
    return ans

@verify(
    requires=[],
    ensures=[
        'ans >= 0'
    ]
)
def absolute_value(x : int) -> int:
    ans = x
    if x < 0:
        ans = -x
    return ans

veripy.scope('summation')

@verify(
    requires=[
        'n >= 0'
    ],
    ensures=[
        'ans == ((n + 1) * n) // 2'
    ]
)
def Summation(n : int) -> int:
    ans = 0
    i = 0
    while i <= n:
        invariant('i <= n + 1')
        invariant('ans == i * (i - 1) // 2')
        ans = ans + i
        i = i + 1
    return ans

veripy.scope('mod')

@verify(
    requires=['n >= 0'],
    ensures=['ans <==> True']
)
def test_mod(n) -> bool:
    m = (n * 2) % 2
    ans = (m == 0)
    return ans

veripy.scope('quantifiers')
@verify(
    ensures=['forall x : int :: x > 0 ==> n + x > n']
)
def test_quantifier(n : int) -> int:
    return n

@verify(
    ensures=['forall x :: forall y :: x + y == y + x']
)
def plus_comm() -> None:
    pass

@verify(
    ensures=[
        'forall x :: forall y :: (x % 2 == 0) and (y % 2 == 1) ==> (x + y) % 2 == 1',
        'forall x :: exists y :: y > x and x - y < 0'
    ]
)
def some_properties() -> None:
    pass

@verify(
    ensures=[
        'forall x :: forall y :: not (x and y) <==> (not x) or (not y)'
    ]
)
def de_morgan() -> None:
    pass

@verify(
    ensures=[
        'forall x :: (not (not x)) <==> x',
        'forall x :: x or (not x) <==> True',
        'forall x :: forall y :: (x ==> y) ==> (y ==> x) ==> (x <==> y)'
    ]
)
def make_intuitionists_mad() -> None:
    pass

veripy.scope('lists')

@verify(
    requires=['len(xs) > 0'],
    ensures=['ans == 111']
)
def simpl_array_operations(xs: List[int]) -> int:
    xs[0] = 111
    ans = xs[0]
    return ans

# veripy.verify_all()
veripy.do_verification('summation')
# veripy.do_verification('lists', ignore_err=False)