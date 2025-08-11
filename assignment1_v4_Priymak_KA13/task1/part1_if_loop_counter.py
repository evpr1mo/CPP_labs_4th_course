#############################################
#############################################
# YOUR CODE BELOW
#############################################

# Implement `my_counter` counting ifs and loops
# NOTE: elif is also considered "if"

import ast
import inspect
import textwrap

def my_counter(func):
    src_code = textwrap.dedent(inspect.getsource(func))
    parsed_tree = ast.parse(src_code)

    num_ifs, num_loops = 0, 0

    # Рекурсивна функція для підрахунку умов і циклів
    def count_ops(node):
        nonlocal num_ifs, num_loops
        if isinstance(node, ast.If):
            num_ifs += 1
        elif isinstance(node, (ast.For, ast.While)):
            num_loops += 1
        for child in ast.iter_child_nodes(node):
            count_ops(child)

    count_ops(parsed_tree)

    # Обгортка, яка зберігає результати підрахунку
    def wrapped_f(*args, **kwargs):
        return func(*args, **kwargs)

    # Зберігаємо кількість циклів і умов у функції
    wrapped_f.num_loops = num_loops
    wrapped_f.num_ifs = num_ifs
    return wrapped_f

#############################################


def test_no_loops_ifs():
    @my_counter
    def func(a, b):
        return a + b
    assert func.num_loops == 0, func.num_loops
    assert func.num_ifs == 0, func.num_ifs


def test_ifs():
    @my_counter
    def func(a, b):
        if a > b:
            return a + b
        elif a == b:
            return 0
        else:
            return 1
    assert func.num_loops == 0, func.num_loops
    assert func.num_ifs == 2, func.num_ifs
    

def test_loops():
    @my_counter
    def func(a, b):
        for i in range(a):
            j = 0
            while j < b:
                j += 1
    assert func.num_loops == 2, func.num_loops
    assert func.num_ifs == 0, func.num_ifs


def test_if_loops():
    @my_counter
    def func(a, b):
        for i in range(a):
            if i < 3:
                j = 0
                var_if = 3
                while j < b:
                    "while i < b"
                    j += 1

    assert func.num_loops == 2, func.num_loops
    assert func.num_ifs == 1, func.num_ifs

def test_big():
    @my_counter
    def func(a, b):
        var = "while"
        if a ** b < 1.0:
            var2 = " if a ** b < 1.0:\n"
            for i in range(a):
                if i < 3:
                    j = 0
                    var = "for i in range(333):"
                    while j < b:
                        j += 1
                elif b == 16:
                    return
        elif a // b == 0:
            while True:
                """
                while True:
                    if i > 50:
                        break
                """
                for i in range(100):
                    if i > 50:
                        break
                break
        else:
            return -333

    assert func.num_loops == 4, func.num_loops
    assert func.num_ifs == 5, func.num_ifs

