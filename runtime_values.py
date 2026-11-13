# the values, variable scopes, errors and control-flow signals the LOLCode interpreter works with.


# an error caused by invalid LOLCode behavior while the program runs
class SemanticError(Exception):
    def __init__(self, message, line=1):
        if not line:
            line = 1
        self.message = message
        self.line = line
        super().__init__(f"semantic error (line {self.line}): {message}")


# a LOLCode value: its type name and the python value it holds
class Value:
    def __init__(self, type_name="NOOB", val=None):
        self.type = type_name
        self.val = val

    def copy(self):
        return Value(self.type, self.val)

    def __repr__(self):
        if self.type == "NOOB":
            return "NOOB"
        if self.type == "TROOF":
            if self.val:
                return "WIN"
            return "FAIL"
        if self.type == "YARN":
            return str(self.val)
        if self.type == "NUMBAR":
            return f"{float(self.val):.2f}"
        return str(self.val)


# the variables of one scope; a function scope has no parent, so it cannot see the globals
class Scope:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def declare(self, name, value=None):
        if name in self.vars:
            return False
        if isinstance(value, Value):
            self.vars[name] = value.copy()
        else:
            self.vars[name] = Value("NOOB", None)
        return True

    def assign(self, name, value):
        if name in self.vars:
            self.vars[name] = value.copy()
            return True
        if self.parent is not None:
            return self.parent.assign(name, value)
        return False

    def get(self, name):
        if name in self.vars:
            return self.vars[name]
        if self.parent is not None:
            return self.parent.get(name)
        return None


# raised by FOUND YR to leave a function with a value
class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


# raised by GTFO to leave a loop, a switch or a function
class BreakSignal(Exception):
    pass
