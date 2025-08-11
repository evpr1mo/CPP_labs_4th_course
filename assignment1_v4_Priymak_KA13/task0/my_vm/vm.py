import math
import json
import pickle


def parser_json(json_text):

    cmd_list = []
    json_load = json.loads(json_text)

    point_of_entry = json_load.get("$entrypoint$")

    if point_of_entry:
        for cmd in point_of_entry:
            opcode = cmd["op"]
            arg = cmd.get("arg", "")
            if arg:
                arg = f'"{arg}"'
            cmd_list.append((opcode, (arg,)))

    return cmd_list


def parse_string(text):
    opcode_list = []

    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        splitlines = line.split()
        opcode = splitlines[0]
        obj = tuple(splitlines[1:]) if len(splitlines) > 1 else ()

        opcode_list.append((opcode, obj))

    return opcode_list

class VM:
    def __init__(self, input_fn=None, print_fn=None):
        self.stack = []
        self.vars = {}
        self.labels = {}

        self.exec_ptr = 0
        self.stack_call = []

        self.code = 0
        self.code_entry = 0

        self.input_fn = input_fn or input
        self.print_fn = print_fn or print

    def run_code_from_json(self, path_to_file):

        with open(path_to_file, 'r') as file:
            file_text = file.read()

        cmd_list = parser_json(file_text)
        return self.run_code(cmd_list)

    def run_code(self, code: list):
        self.code = code

        if isinstance(code, dict) and code:
            for group in code.values():
                self.parser_labels(group)

            self.code_entry = code["$entrypoint$"]

            while self.exec_ptr < len(self.code_entry):
                opcode, args = self.code_entry[self.exec_ptr]
                self.start_exec(opcode, args)
                self.exec_ptr += 1

        else:
            self.parser_labels(code)
            while self.exec_ptr < len(code):
                opcode, args = self.code[self.exec_ptr]
                self.start_exec(opcode, args)
                self.exec_ptr += 1

        return self.stack, self.vars

    def parser_labels(self, code):
        for index, (opcode, args) in enumerate(code):
            if opcode == 'LABEL':
                lb_name = args[0].strip('"')
                self.labels[lb_name] = index

    def start_exec(self, opcode, args):

        if opcode == 'LOAD_CONST':
            if args[0].startswith('"') and args[0].endswith('"'):
                self.stack.append(args[0].strip('"'))
            else:
                try:
                    self.stack.append(int(args[0]))
                except ValueError:
                    self.stack.append(float(args[0]))

        elif opcode == 'INPUT_STRING':
            input_new = self.input_fn("Enter a string: ")
            self.stack.append(input_new)

        elif opcode == 'INPUT_NUMBER':
            input_new = self.input_fn("Enter a number: ")
            self.stack.append(input_new)

        elif opcode == 'PRINT':
            val = self.stack.pop()
            self.print_fn(val)

        elif opcode == 'LOAD_VAR':
            var_new = args[0].strip('"')
            self.stack.append(self.vars[var_new])

        elif opcode == 'STORE_VAR':
            var_new = args[0].strip('"')
            self.vars[var_new] = self.stack.pop()

        elif opcode == 'ADD':
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.append(a + b)

        elif opcode == 'SUB':
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.append(a - b)

        elif opcode == 'MUL':
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.append(a * b)

        elif opcode == 'DIV':
            a = self.stack.pop()
            b = self.stack.pop()
            if isinstance(a, int) and isinstance(b, int):
                self.stack.append(a // b)
            else:
                self.stack.append(a / b)

        elif opcode == 'EXP':
            a = self.stack.pop()
            self.stack.append(math.exp(a))

        elif opcode == 'SQRT':
            a = self.stack.pop()
            self.stack.append(math.sqrt(a))

        elif opcode == 'NEG':
            a = self.stack.pop()
            self.stack.append(-a)

        elif opcode == 'EQ':
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.append(1 if a == b else 0)

        elif opcode == 'NEQ':
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.append(1 if a != b else 0)

        elif opcode == 'GT':
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.append(1 if a > b else 0)

        elif opcode == 'LT':
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.append(1 if a < b else 0)

        elif opcode == 'GE':
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.append(1 if a >= b else 0)

        elif opcode == 'LE':
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.append(1 if a <= b else 0)

        elif opcode == 'JMP':
            new_label = args[0].strip('"')
            self.exec_ptr = self.labels[new_label]

        elif opcode == 'CJMP':
            new_label = args[0].strip('"')
            jump_condition = self.stack.pop()
            if jump_condition == 1:
                self.exec_ptr = self.labels[new_label]

        elif opcode == 'LABEL':
            pass

        elif opcode == 'CALL':
            func = self.stack.pop()

            self.stack_call.append((self.code_entry, self.exec_ptr,
                                    self.vars.copy()))
            self.code_entry = self.code[func]
            self.exec_ptr = -1
            self.vars = {}

        elif opcode == 'RET':
            self.code_entry, self.exec_ptr, self.vars = self.stack_call.pop()

        return self.stack, self.vars

    def dump_stack(self, f_name):
        with open(f_name, 'wb') as file:
            pickle.dump(self.stack, file)

    def load_stack(self, f_name):
        with open(f_name, 'rb') as file:
            self.stack = pickle.load(file)

    def dump_memory(self, f_name):
        with open(f_name, 'wb') as file:
            pickle.dump(self.vars, file)

    def load_memory(self, f_name):
        with open(f_name, 'rb') as file:
            self.vars = pickle.load(file)
