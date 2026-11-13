# runs a lolcode parse tree by walking it node by node

from expressions import ExpressionEvaluator
from runtime_values import BreakSignal, ReturnSignal, Scope, Value


# prints text without adding a newline because visible already decides that
def print_without_newline(text):
    print(text, end="")


# the last layer of the interpreter that runs statements flow control and functions
class Interpreter(ExpressionEvaluator):
    # sets up the scopes function table and the input and output callbacks
    def __init__(self, io_callbacks=None):
        if not io_callbacks:
            io_callbacks = {}
        self.global_scope = Scope()
        self.current_scope = self.global_scope
        # maps a function name to its funcdef node
        self.functions = {}
        self.output_cb = io_callbacks.get("output", print_without_newline)
        self.input_cb = io_callbacks.get("input", input)
        # it is the implicit variable that holds the last bare expression
        self.global_scope.declare("IT", Value("NOOB", None))

    # returns every visible variable as text with nearer scopes hiding outer ones
    def get_symbol_table(self):
        result = {}
        scope = self.current_scope
        # walk from the current scope outward through the parents
        while scope is not None:
            for name, value in scope.vars.items():
                # keep the nearest one so inner variables hide outer ones
                if name not in result:
                    result[name] = str(value)
            scope = scope.parent
        return result

    # running the tree

    # runs a whole program after registering all functions first
    def execute(self, root_node):
        if root_node is None or root_node.kind != "program":
            self._error("Invalid or missing program parse tree")

        # register every function first so calls can come before definitions
        self.functions = {}
        self._collect_functions(root_node)

        # only declarations and statements are run
        for child in root_node.children:
            if child.kind == "declsection" or child.kind == "statements":
                self.visit(child)
        return Value("NOOB", None)

    # finds every function definition anywhere in the tree and registers it
    def _collect_functions(self, node):
        for child in node.children:
            if child.kind == "funcdef":
                self._register_function(child)
            # keep going deeper so nested functions are found too
            self._collect_functions(child)

    # does nothing because functions are registered before running
    def visit_funcdef(self, node):
        return Value("NOOB", None)

    # saves a function node in the function table and rejects duplicate names
    def _register_function(self, node):
        name_node = self._first_child(node, ("funcident",))
        if name_node is None:
            self._error("Malformed function definition", node)
        name = self.get_node_lexeme(name_node)
        # two functions cannot share a name
        if name in self.functions:
            self._error(f"Function '{name}' is already defined", name_node)
        # store the whole node so a call can read its params and body
        self.functions[name] = node

    # returns the first child of a node with one of the given kinds or none
    def _first_child(self, node, kinds):
        for child in node.children:
            if child.kind in kinds:
                return child
        return None

    # returns the text a node stands for
    def get_node_lexeme(self, node):
        if node is None:
            return ""
        # a leaf node has a token so return its text
        token = getattr(node, "token", None)
        if token is not None:
            return token.lexeme
        # no token so try the first child
        children = getattr(node, "children", None)
        if children:
            return self.get_node_lexeme(children[0])
        # last resort is the kind name
        return node.kind

    # runs the visit method for a node and turns python errors into semantic errors
    def visit(self, node):
        if node is None:
            return Value("NOOB", None)
        # find visit_kind for this node or use generic_visit
        method = getattr(self, "visit_" + node.kind, self.generic_visit)
        try:
            result = method(node)
        except (ArithmeticError, ValueError, TypeError, IndexError, KeyError) as error:
            # python errors become semantic errors that show the node location
            message = str(error)
            if not message:
                message = error.__class__.__name__
            self._error(message, node)
        # always hand back a value so callers never get anything else
        if isinstance(result, Value):
            return result
        return Value("NOOB", None)

    # fallback that visits every child of a node with no visit method
    def generic_visit(self, node):
        result = Value("NOOB", None)
        for child in getattr(node, "children", []):
            result = self.visit(child)
        return result

    # stores a value in the it variable of the current scope
    def _set_it(self, value):
        # assign fails when it is not in this scope yet so declare it
        if not self.current_scope.assign("IT", value):
            self.current_scope.declare("IT", value)

    # declarations and simple statements

    # runs the variable declarations in the wazzup block
    def visit_declsection(self, node):
        for child in node.children:
            if child.kind == "vardecl":
                self.visit_vardecl(child)
        return Value("NOOB", None)

    # declares a variable and evaluates its optional starting value first
    def visit_vardecl(self, node):
        name_node = self._first_child(node, ("varident",))
        if name_node is None:
            self._error("Malformed variable declaration", node)
        name = self.get_node_lexeme(name_node)
        # a name already in this scope cannot be declared again
        if self.current_scope.get(name) is not None:
            self._error(f"Variable '{name}' is already declared", name_node)

        # the initializer is the first child that is not the name or a keyword token
        initializer = None
        for child in node.children:
            if child is name_node or child.kind == "I HAS A" or child.kind == "ITZ":
                continue
            initializer = child
            break

        # the initializer runs before the declaration so i has a x itz x is an error
        value = Value("NOOB", None)
        if initializer is not None:
            value = self.visit(initializer)
        self.current_scope.declare(name, value)
        return value

    # runs a list of statements in order
    def visit_statements(self, node):
        result = Value("NOOB", None)
        for statement in node.children:
            result = self.visit(statement)
        return result

    # prints the evaluated expressions and adds a newline unless there is a bang
    def visit_print(self, node):
        parts = []
        suppress_newline = False
        for child in node.children:
            # skip the keyword token
            if child.kind == "VISIBLE":
                continue
            # a bang token means no newline
            if child.kind == "!":
                suppress_newline = True
                continue
            value = self.visit(child)
            # every value is converted to a yarn before joining
            parts.append(self._implicit_yarn(value, child).val)
        output = "".join(parts)
        # visible adds the newline itself unless there is a bang
        if not suppress_newline:
            output += "\n"
        # send the whole line out in one call
        self.output_cb(output)
        return Value("NOOB", None)

    # reads a line of input into a declared variable as a yarn
    def visit_input(self, node):
        if len(node.children) < 2:
            self._error("Malformed GIMMEH statement", node)
        # children are the gimmeh keyword then the variable
        var_node = node.children[1]
        name = self.get_node_lexeme(var_node)
        if self.current_scope.get(name) is None:
            self._error(f"Undeclared variable '{name}'", var_node)
        # ask the user for a line of text
        entered = self.input_cb(f"Enter value for {name}: ")
        if entered is None:
            entered = ""
        # input is always a yarn even if it looks like a number
        value = Value("YARN", str(entered))
        self.current_scope.assign(name, value)
        return value

    # evaluates an expression and stores it in a declared variable
    def visit_assign(self, node):
        if len(node.children) < 3:
            self._error("Malformed assignment statement", node)
        # children are the variable then r then the expression
        var_node = node.children[0]
        name = self.get_node_lexeme(var_node)
        if self.current_scope.get(name) is None:
            self._error(f"Undeclared variable '{name}'", var_node)
        # evaluate the expression before storing it
        value = self.visit(node.children[2])
        self.current_scope.assign(name, value)
        return value

    # converts a declared variable to another type in place
    def visit_typecast(self, node):
        if len(node.children) < 3:
            self._error("Malformed IS NOW A statement", node)
        # children are the variable then the keyword then the target type
        var_node = node.children[0]
        name = self.get_node_lexeme(var_node)
        current = self.current_scope.get(name)
        if current is None:
            self._error(f"Undeclared variable '{name}'", var_node)
        target = self.get_node_lexeme(node.children[2])
        # explicit mode because the programmer asked for this cast
        converted = self.cast_to(current, target, explicit=True, node=node)
        self.current_scope.assign(name, converted)
        return converted

    # evaluates a standalone expression and stores the result in it
    def visit_expression(self, node):
        value = self.visit(node.children[0])
        # the result becomes it so o rly or wtf can test it
        self._set_it(value)
        return value

    # stores the return value in it and raises a return signal
    def visit_return(self, node):
        value = Value("NOOB", None)
        # the value comes after the found yr keyword
        if len(node.children) >= 2:
            value = self.visit(node.children[1])
        self._set_it(value)
        # unwinds up to the function call that catches it
        raise ReturnSignal(value)

    # raises a break signal to leave the nearest loop switch or function
    def visit_GTFO(self, node):
        # caught by the nearest loop switch or function
        raise BreakSignal()

    # flow control

    # runs the ya rly or first true mebbe or no wai branch based on it
    def visit_ifelse(self, node):
        it_value = self.current_scope.get("IT")
        if it_value is None:
            it_value = Value("NOOB", None)

        # ya rly runs when it is truthy
        if self._implicit_troof(it_value, node).val:
            return self.visit(self._first_child(node, ("statements",)))

        # otherwise try each mebbe in order and run the first true one
        for child in node.children:
            if child.kind == "mebbe" and len(child.children) >= 3:
                branch_condition = self.visit(child.children[1])
                if self._implicit_troof(branch_condition, child).val:
                    return self.visit(child.children[2])

        # nothing matched so use no wai if there is one
        nowai = self._first_child(node, ("nowai",))
        if nowai is None:
            return Value("NOOB", None)
        return self.visit(self._first_child(nowai, ("statements",)))

    # runs omg cases with fall through until gtfo and falls back to the default
    def visit_switch(self, node):
        it_value = self.current_scope.get("IT")
        if it_value is None:
            it_value = Value("NOOB", None)

        # once a case matches every later case runs until gtfo
        matched = False
        for case in node.children:
            if case.kind != "case":
                continue
            if len(case.children) < 3:
                self._error("Malformed OMG case", case)
            # children are the omg keyword then the value then the statements
            case_value = self.visit(case.children[1])
            if not matched and self._same_case_value(it_value, case_value):
                matched = True
            if matched:
                try:
                    self.visit(case.children[2])
                except BreakSignal:
                    # gtfo ends the switch
                    break

        # the default only runs when nothing matched
        default = self._first_child(node, ("default",))
        if not matched and default is not None:
            try:
                self.visit(self._first_child(default, ("statements",)))
            except BreakSignal:
                pass
        return Value("NOOB", None)

    # repeats the body while stepping the counter until the condition or gtfo stops it
    def visit_loop(self, node):
        # pick out the parts of the loop
        operation = self._first_child(node, ("UPPIN", "NERFIN"))
        var_node = self._first_child(node, ("varident",))
        condition_marker = self._first_child(node, ("TIL", "WILE"))
        body = self._first_child(node, ("statements",))
        if operation is None or var_node is None or body is None:
            self._error("Malformed loop statement", node)

        var_name = self.get_node_lexeme(var_node)
        current_value = self.current_scope.get(var_name)
        if current_value is None:
            self._error(f"Undeclared loop variable '{var_name}'", var_node)
        # the counter must be a number before counting
        self.current_scope.assign(var_name, self._numeric(current_value, var_node))

        condition_expr = self._loop_condition(node, condition_marker)
        condition_name = None
        if condition_marker is not None:
            condition_name = self.get_node_lexeme(condition_marker)
        operation_name = self.get_node_lexeme(operation)

        # each round checks the condition then runs the body then steps the counter
        while True:
            if self._loop_should_stop(condition_name, condition_expr):
                break
            # gtfo in the body ends the loop
            try:
                self.visit(body)
            except BreakSignal:
                break
            # step the counter after each run of the body
            self._step_loop_variable(var_name, var_node, operation_name)
        return Value("NOOB", None)

    # returns the condition expression that comes right after til or wile
    def _loop_condition(self, node, condition_marker):
        if condition_marker is None:
            return None
        # the condition sits right after the marker
        marker_index = node.children.index(condition_marker)
        if marker_index + 1 >= len(node.children):
            self._error("Missing loop condition", condition_marker)
        return node.children[marker_index + 1]

    # tells whether the loop condition says to stop
    def _loop_should_stop(self, condition_name, condition_expr):
        # no condition means the loop only stops with gtfo
        if condition_expr is None:
            return False
        condition_value = self.visit(condition_expr)
        condition_truth = self._implicit_troof(condition_value, condition_expr).val
        # til stops when the condition is win
        if condition_name == "TIL" and condition_truth:
            return True
        # wile stops when the condition is fail
        if condition_name == "WILE" and not condition_truth:
            return True
        return False

    # adds or subtracts one from the loop counter
    def _step_loop_variable(self, var_name, var_node, operation_name):
        numeric_value = self._numeric(self.current_scope.get(var_name), var_node)
        # keep the same type so a numbar stays a numbar
        if numeric_value.type == "NUMBAR":
            delta = 1.0
        else:
            delta = 1
        # uppin counts up and nerfin counts down
        if operation_name == "UPPIN":
            updated = numeric_value.val + delta
        else:
            updated = numeric_value.val - delta
        self.current_scope.assign(var_name, Value(numeric_value.type, updated))

    # functions

    # checks a function call then runs the function and returns its value
    def visit_call(self, node):
        if len(node.children) < 2:
            self._error("Malformed function call", node)
        name_node = node.children[1]
        function_name = self.get_node_lexeme(name_node)
        # the function must have been registered
        if function_name not in self.functions:
            self._error(f"Undefined function '{function_name}'", name_node)
        function_node = self.functions[function_name]

        # gather the parameters from the definition and the arguments from the call
        parameter_nodes = []
        for child in function_node.children:
            if child.kind == "param":
                parameter_nodes.append(child)
        argument_nodes = []
        for child in node.children[2:]:
            if child.kind != "MKAY":
                argument_nodes.append(child)
        # the counts must match
        if len(argument_nodes) != len(parameter_nodes):
            self._error(
                f"Function '{function_name}' expects {len(parameter_nodes)} argument(s), "
                f"but received {len(argument_nodes)}",
                node,
            )

        # the call gets its own scope
        function_scope = self._make_function_scope(parameter_nodes, argument_nodes)
        body = self._first_child(function_node, ("statements",))
        if body is None:
            self._error(f"Function '{function_name}' has no body", function_node)

        # run the body and catch whatever it returns
        return_value = self._run_function_body(body, function_scope)
        # the result also becomes it in the caller
        self._set_it(return_value)
        return return_value

    # builds a separate scope with the evaluated arguments as parameters
    def _make_function_scope(self, parameter_nodes, argument_nodes):
        # no parent so the function cannot see outside variables
        function_scope = Scope(parent=None)
        # the function has its own it
        function_scope.declare("IT", Value("NOOB", None))
        for index in range(len(parameter_nodes)):
            # arguments run in the caller scope because current_scope has not changed yet
            argument_value = self.visit(argument_nodes[index])
            parameter_name = self.get_node_lexeme(parameter_nodes[index])
            function_scope.declare(parameter_name, argument_value)
        return function_scope

    # runs the body in the function scope and always restores the caller scope
    def _run_function_body(self, body, function_scope):
        # remember the caller scope so it can be restored
        previous_scope = self.current_scope
        self.current_scope = function_scope
        return_value = Value("NOOB", None)
        try:
            self.visit(body)
        except ReturnSignal as returned:
            # found yr gives the return value
            return_value = returned.value
        except BreakSignal:
            # gtfo in a function returns noob
            pass
        finally:
            # always restore the caller scope even after an error
            self.current_scope = previous_scope
        return return_value