import math
from my_vm.vm import VM, parse_string

def _cmp_floats(a, b, digits=2):
    a = int(round(a, digits) * 10**digits)
    b = int(round(b, digits) * 10**digits)
    return a == b


# 4 + 3
TEST1 = """\
LOAD_CONST 3
LOAD_CONST 4
ADD
"""

def test1():
    code = parse_string(TEST1)
    vm = VM()
    stack, variables = vm.run_code(code)
    assert len(stack) == 1
    assert stack[-1] == 3+4


# 3 * (7 // (4+3))
TEST2 = """\
LOAD_CONST 3
LOAD_CONST 4
ADD
LOAD_CONST 7
DIV
LOAD_CONST 3
MUL
"""

def test2():
    code = parse_string(TEST2)
    vm = VM()
    stack, variables = vm.run_code(code)
    assert len(stack) == 1
    assert stack[-1] == 3


# a = 7.0
# b = 2.0
# result = -sqrt(exp(a + b))
TEST3 = """\
LOAD_CONST 7.0
STORE_VAR "a"
LOAD_CONST 2.0
STORE_VAR "b"
LOAD_VAR "b"
LOAD_VAR "a"
SUB
EXP
SQRT
NEG
STORE_VAR "result"
"""

def test3():
    code = parse_string(TEST3)
    vm = VM()
    stack, variables = vm.run_code(code)
    assert "a" in variables
    assert "b" in variables
    assert "result" in variables
    assert len(stack) == 0
    assert _cmp_floats(variables["result"], -math.sqrt(math.exp(7.0 - 2.0)))