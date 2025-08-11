#############################################
#############################################
# YOUR CODE BELOW
#############################################

# Implement `has_recursion`.
import ast
import inspect


def has_recursion(f):
    checked = set()

    def detector(c, target, scope):
        if c.__name__ in checked:
            return False
        checked.add(c.__name__)

        code = inspect.getsource(c).strip()
        tree = ast.parse(code)
        found = False

        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                if n.func.id == target:
                    return True
                funcs = {k: v for k, v in scope.items() if inspect.isfunction(v)}
                called_func = funcs.get(n.func.id)
                if called_func and detector(called_func, target, scope):
                    found = True
        return found

    scope = inspect.currentframe().f_back.f_locals
    return detector(f, f.__name__, scope)
#############################################

def test_simple():
    def func(i):
        if i > 0:
            func(i - 1)
    
    assert has_recursion(func)

    def func():
        return 5
    
    assert not has_recursion(func)

    def factorial(x):
        """This is a recursive function
        to find the factorial of an integer"""

        if x == 1:
            return 1
        else:
            return (x * factorial(x-1))

    assert has_recursion(factorial)


def test_coupled():
    def func1(i):
        if i > 0:
            func2(i)
    
    def func2(i):
        if i > 0:
            func1(i)

    def func3(i):
        func1(i)

    assert has_recursion(func1)
    assert has_recursion(func2)
    assert not has_recursion(func3)


def test_big():
    def func1(i, j):
        if i > 0:
            func2(i-1, j)
        else:
            func6()
    
    def func2(i, j):
        if j > 0:
            func3(i, j-1)
        if i > 0:
            func4(i-1, j)

    def func3(i, j, run_func1=False):
        if j > 0:
            func2(i, j)

        if run_func1:
            func1(0, 0)
    
    def func4(i, j):
        if i == 0 and j == 0:
            func1(0, 0, run_func1=True)
        else:
            func5()
    
    def func5():
        """
        func6()
        """
        return

    def func6():
        func5()
    
    assert has_recursion(func1)
    assert has_recursion(func2)
    assert has_recursion(func3)
    assert has_recursion(func4)
    assert not has_recursion(func5)
    assert not has_recursion(func6)


# Unnecessary test for extra points!
def test_alias():
    def func1(i):
        function_alias = func1
        if i > 0:
            function_alias(i - 1)

    def func2(i):
        function_alias = func2
        return function_alias
    
    assert has_recursion(func1)
    assert not has_recursion(func2)