# evaluates LOLCode expressions: variables, literals, arithmetic, boolean, comparison, SMOOSH and MAEK.

from runtime_values import Value
from type_casting import TypeCaster


# the second layer of the interpreter
# visit, get_node_lexeme and current_scope come from Interpreter in semantic_analyzer.py
class ExpressionEvaluator(TypeCaster):
    def visit_varident(self, node):
        name = self.get_node_lexeme(node)
        value = self.current_scope.get(name)
        if value is None:
            self._error(f"Undeclared variable '{name}'", node)
        return value.copy()

    def visit_numbr(self, node):
        return Value("NUMBR", int(self.get_node_lexeme(node)))

    def visit_numbar(self, node):
        return Value("NUMBAR", float(self.get_node_lexeme(node)))

    def visit_troof(self, node):
        return Value("TROOF", self.get_node_lexeme(node) == "WIN")

    def visit_yarn(self, node):
        return Value("YARN", str(self.get_node_lexeme(node)))

    def visit_arith(self, node):
        if len(node.children) < 3:
            self._error("Malformed arithmetic expression", node)
        operator = self.get_node_lexeme(node.children[0])
        left = self._numeric(self.visit(node.children[1]), node.children[1])
        right = self._numeric(self.visit(node.children[2]), node.children[2])
        result_type = "NUMBR"
        if left.type == "NUMBAR" or right.type == "NUMBAR":
            result_type = "NUMBAR"
        result = self._compute_arith(operator, left.val, right.val, result_type, node)
        return Value(result_type, result)

    def _compute_arith(self, operator, a, b, result_type, node):
        if operator == "SUM OF":
            return a + b
        if operator == "DIFF OF":
            return a - b
        if operator == "PRODUKT OF":
            return a * b
        if operator == "QUOSHUNT OF":
            if b == 0:
                self._error("Division by zero", node)
            # two NUMBRs divide to a NUMBR, rounded toward zero
            if result_type == "NUMBAR":
                return a / b
            return int(a / b)
        if operator == "MOD OF":
            if b == 0:
                self._error("Modulo by zero", node)
            return a % b
        if operator == "BIGGR OF":
            return max(a, b)
        if operator == "SMALLR OF":
            return min(a, b)
        self._error(f"Unknown arithmetic operator '{operator}'", node)

    def visit_bool(self, node):
        if not node.children:
            self._error("Malformed boolean expression", node)
        operator = self.get_node_lexeme(node.children[0])
        if operator == "NOT":
            if len(node.children) < 2:
                self._error("NOT requires one operand", node)
            operand = self._implicit_troof(self.visit(node.children[1]), node.children[1])
            return Value("TROOF", not operand.val)

        if len(node.children) < 3:
            self._error(f"{operator} requires two operands", node)
        left = self._implicit_troof(self.visit(node.children[1]), node.children[1]).val
        right = self._implicit_troof(self.visit(node.children[2]), node.children[2]).val
        if operator == "BOTH OF":
            result = left and right
        elif operator == "EITHER OF":
            result = left or right
        elif operator == "WON OF":
            result = left != right
        else:
            self._error(f"Unknown boolean operator '{operator}'", node)
        return Value("TROOF", result)

    def visit_infbool(self, node):
        if not node.children:
            self._error("Malformed infinite boolean expression", node)
        operator = self.get_node_lexeme(node.children[0])
        operands = []
        for child in node.children[1:]:
            if child.kind != "MKAY":
                operands.append(child)
        if not operands:
            self._error(f"{operator} requires at least one operand", node)

        # both stop at the first operand that decides the answer
        if operator == "ALL OF":
            for operand in operands:
                if not self._implicit_troof(self.visit(operand), operand).val:
                    return Value("TROOF", False)
            return Value("TROOF", True)
        if operator == "ANY OF":
            for operand in operands:
                if self._implicit_troof(self.visit(operand), operand).val:
                    return Value("TROOF", True)
            return Value("TROOF", False)
        self._error(f"Unknown infinite boolean operator '{operator}'", node)

    def _same_case_value(self, left, right):
        # the types must match too, nothing is cast; also used by the switch statement
        return left.type == right.type and left.val == right.val

    def _compare_equal(self, left, right):
        # two numbers compare by value: integer math for two NUMBRs, floating-point math if one is a NUMBAR
        # any other pair is not cast, so it must have the same type and value
        left_is_number = left.type == "NUMBR" or left.type == "NUMBAR"
        right_is_number = right.type == "NUMBR" or right.type == "NUMBAR"
        if left_is_number and right_is_number:
            if left.type == "NUMBAR" or right.type == "NUMBAR":
                return float(left.val) == float(right.val)
            return left.val == right.val
        return self._same_case_value(left, right)

    def visit_comp(self, node):
        if len(node.children) < 3:
            self._error("Malformed comparison expression", node)
        operator = self.get_node_lexeme(node.children[0])
        left = self.visit(node.children[1])
        right = self.visit(node.children[2])
        if operator == "BOTH SAEM":
            result = self._compare_equal(left, right)
        elif operator == "DIFFRINT":
            result = not self._compare_equal(left, right)
        else:
            self._error(f"Unknown comparison operator '{operator}'", node)
        return Value("TROOF", result)

    def visit_concat(self, node):
        pieces = []
        for child in node.children[1:]:
            if child.kind == "MKAY":
                continue
            pieces.append(self._implicit_yarn(self.visit(child), child).val)
        return Value("YARN", "".join(pieces))

    def visit_cast(self, node):
        if len(node.children) < 3:
            self._error("Malformed MAEK expression", node)
        value = self.visit(node.children[1])
        target_type = self.get_node_lexeme(node.children[-1])
        return self.cast_to(value, target_type, explicit=True, node=node)
