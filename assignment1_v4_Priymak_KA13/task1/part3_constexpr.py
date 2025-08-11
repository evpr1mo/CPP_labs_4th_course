
#############################################
#############################################
# YOUR CODE BELOW
#############################################

# Implement `constexpr` and `eval_const_exprs`
import math
import ast
import inspect
import operator
import textwrap


def constexpr(func):
    func.is_const = True
    return func

def eval_const_exprs(func):
    src_code = textwrap.dedent(inspect.getsource(func))
    parsed_tree = ast.parse(src_code)
    parsed_tree.body[0].decorator_list = []

    def is_static_expr(expr):
        return isinstance(expr, (ast.Constant, ast.Num)) or (
            isinstance(expr, ast.UnaryOp) and isinstance(expr.operand, ast.Constant)
        )

    def eval_expr(expr):
        if isinstance(expr, ast.Constant):
            return expr.value
        elif isinstance(expr, ast.UnaryOp):
            expr_options = {ast.USub: operator.neg}
            return expr_options[type(expr.op)](eval_expr(expr.operand))
        elif isinstance(expr, ast.BinOp):
            expr_left = eval_expr(expr.left)
            expr_right = eval_expr(expr.right)
            expr_options = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Pow: operator.pow,
            }
            return expr_options[type(expr.op)](expr_left, expr_right)
        raise TypeError("Unsupported expression")

    def call_modifier(call_node):
        if isinstance(call_node, ast.Call):
            f_name = call_node.func.id if isinstance(call_node.func, ast.Name) else None
            if f_name in scope_vars:
                f_called = scope_vars[f_name]
                if getattr(f_called, 'is_const', False):
                    constants = []
                    for arg in call_node.args:
                        if isinstance(arg, ast.Call):
                            nested_call = call_modifier(arg)
                            if isinstance(nested_call, ast.Constant):
                                constants.append(nested_call)
                            else:
                                return call_node
                        elif is_static_expr(arg):
                            constants.append(arg)
                        elif isinstance(arg, ast.BinOp):
                            val = eval_expr(arg)
                            constants.append(ast.Constant(value=val))
                        else:
                            return call_node
                    list_eval = [eval_expr(arg) for arg in constants]
                    f_result = f_called(*list_eval)
                    return ast.Constant(value=f_result)
        return call_node

    def tree_modifier(tree):
        for node in ast.walk(tree):
            for node_field, node_val in ast.iter_fields(node):
                if isinstance(node_val, list):
                    for i, item in enumerate(node_val):
                        if isinstance(item, ast.AST):
                            node_val[i] = call_modifier(item)
                elif isinstance(node_val, ast.AST):
                    setattr(node, node_field, call_modifier(node_val))
        return tree

    scope_vars = inspect.currentframe().f_back.f_locals
    final_tree = tree_modifier(parsed_tree)
    ast.fix_missing_locations(final_tree)
    exec(compile(final_tree, filename="<ast>", mode="exec"), scope_vars)

    return scope_vars[func.__name__]
#############################################


# Execution Marker is only used for instrumentation
# and tests, do not consider it as a state change. In
# other words, it does not make a pure function "not pure".
class ExecutionMarker:
    def __init__(self):
        self.counter = 0
    def mark(self):
        self.counter += 1
    def reset(self):
        self.counter = 0


def test_simple():
    _m = ExecutionMarker()

    @constexpr
    def f(a, b):
        _m.mark()
        return a + b

    @eval_const_exprs
    def my_function(a):
        return f(3, 6) + f(a, 3)

    _m.reset()
    result = my_function(8)
    assert result == 3+6 + 8+3, f"Res {result}"
    assert _m.counter == 1, _m.counter


def test_larger():
    _m = ExecutionMarker()

    @constexpr
    def f(a, b):
        _m.mark()
        return int(math.exp(a + b))

    @constexpr
    def g(a, b):
        _m.mark()
        return a - b

    @eval_const_exprs
    def my_function(a):
        result = f(-3, 3)
        result = result + f(a, 8)
        return g(result, 2) + g(333, 330)

    _m.reset()
    res = my_function(-8)
    assert res == 3, res
    assert _m.counter == 2, _m.counter


def test_multi():
    _m = ExecutionMarker()

    @constexpr
    def f(a, b):
        _m.mark()
        return int(math.exp(a + b))

    @constexpr
    def g(a, b):
        _m.mark()
        return a - b

    @eval_const_exprs
    def my_function(a):
        result = f(g(0, 3), 3) + g(3, a)
        return result

    _m.reset()
    res = my_function(3)
    assert res == 1, res
    assert _m.counter == 1, _m.counter


# Extra points.
def test_advanced():
    _m = ExecutionMarker()

    @constexpr
    def f(a, b):
        _m.mark()
        return int(math.exp(a + b))

    @eval_const_exprs
    def my_function(a):
        result = f(3-3, 0) + f(3, a)
        return result

    _m.reset()
    res = my_function(-3)
    assert res == 2, res
    assert _m.counter == 1, _m.counter