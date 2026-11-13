# converts LOLCode values from one type to another, both explicitly (MAEK, IS NOW A) and implicitly.

import math

from runtime_values import SemanticError, Value


# the five LOLCode types a value can be cast to
VALID_TYPES = ("NOOB", "NUMBR", "NUMBAR", "YARN", "TROOF")


def is_numeric_yarn(text):
    # true for text like 12, -12, 1.5 or -1.5 (digits, an optional minus sign, at most one dot)
    if text.startswith("-"):
        text = text[1:]
    parts = text.split(".")
    if len(parts) > 2:
        return False
    for part in parts:
        if part == "":
            return False
        for character in part:
            if character not in "0123456789":
                return False
    return True


# the first layer of the interpreter: error reporting and type casting
class TypeCaster:
    # errors

    def _line(self, node):
        line = self._find_line(node)
        if line is None:
            return 1
        return line

    def _find_line(self, node):
        # the line of the first token in the node or below it; a node like MAEK or SUM OF has no token of its own
        token = getattr(node, "token", None)
        if token:
            return getattr(token, "line", 1)
        for child in getattr(node, "children", []):
            line = self._find_line(child)
            if line is not None:
                return line
        return None

    def _error(self, message, node=None):
        line = 1
        if node is not None:
            line = self._line(node)
        raise SemanticError(message, line)

    # type conversion

    def cast_to(self, value, target_type, explicit=False, node=None):
        # explicit is true for MAEK and IS NOW A, which may turn NOOB into any type
        if not isinstance(value, Value):
            value = Value("NOOB", None)
        if target_type not in VALID_TYPES:
            self._error(f"Invalid target type '{target_type}'", node)

        if value.type == "NOOB":
            return self._cast_noob(target_type, explicit, node)
        if target_type == value.type:
            return value.copy()

        result = None
        if target_type == "TROOF":
            result = self._cast_to_troof(value)
        elif target_type == "NUMBR":
            result = self._cast_to_numbr(value, node)
        elif target_type == "NUMBAR":
            result = self._cast_to_numbar(value, node)
        elif target_type == "YARN":
            result = self._cast_to_yarn(value)

        if result is None:
            self._error(f"Cannot cast {value.type} to {target_type}", node)
        return result

    def _cast_noob(self, target_type, explicit, node):
        if target_type == "TROOF":
            return Value("TROOF", False)
        if not explicit:
            self._error(f"Cannot implicitly cast NOOB to {target_type}", node)
        # an explicit cast of NOOB gives the empty or zero value of the type
        defaults = {
            "NOOB": Value("NOOB", None),
            "NUMBR": Value("NUMBR", 0),
            "NUMBAR": Value("NUMBAR", 0.0),
            "YARN": Value("YARN", ""),
        }
        return defaults[target_type]

    def _cast_to_troof(self, value):
        if value.type == "NUMBR" or value.type == "NUMBAR":
            return Value("TROOF", value.val != 0)
        if value.type == "YARN":
            return Value("TROOF", len(str(value.val)) > 0)
        return None

    def _cast_to_numbr(self, value, node):
        if value.type == "TROOF":
            if value.val:
                return Value("NUMBR", 1)
            return Value("NUMBR", 0)
        if value.type == "NUMBAR":
            # int() drops the decimals, so it rounds toward zero
            return Value("NUMBR", int(value.val))
        if value.type == "YARN":
            return self._yarn_to_number(value.val, "NUMBR", node)
        return None

    def _cast_to_numbar(self, value, node):
        if value.type == "TROOF":
            if value.val:
                return Value("NUMBAR", 1.0)
            return Value("NUMBAR", 0.0)
        if value.type == "NUMBR":
            return Value("NUMBAR", float(value.val))
        if value.type == "YARN":
            return self._yarn_to_number(value.val, "NUMBAR", node)
        return None

    def _yarn_to_number(self, raw, target_type, node):
        text = str(raw)
        if not is_numeric_yarn(text):
            self._error(f"Cannot cast YARN '{text}' to {target_type}", node)
        try:
            if target_type == "NUMBR":
                return Value("NUMBR", int(float(text)))
            return Value("NUMBAR", float(text))
        except (ValueError, OverflowError):
            self._error(f"Cannot cast YARN '{text}' to {target_type}", node)

    def _cast_to_yarn(self, value):
        if value.type == "TROOF":
            if value.val:
                return Value("YARN", "WIN")
            return Value("YARN", "FAIL")
        if value.type == "NUMBR":
            return Value("YARN", str(value.val))
        if value.type == "NUMBAR":
            # the spec cuts a NUMBAR to two decimals instead of rounding it
            truncated = math.trunc(float(value.val) * 100) / 100
            return Value("YARN", f"{truncated:.2f}")
        return None

    def _implicit_troof(self, value, node=None):
        return self.cast_to(value, "TROOF", explicit=False, node=node)

    def _implicit_yarn(self, value, node=None):
        return self.cast_to(value, "YARN", explicit=False, node=node)

    def _numeric(self, value, node=None):
        # turns an operand into a NUMBR or NUMBAR for arithmetic and loops
        if value.type == "NUMBR" or value.type == "NUMBAR":
            return value.copy()
        if value.type == "YARN":
            text = str(value.val)
            if not is_numeric_yarn(text):
                self._error(f"Cannot implicitly cast YARN '{text}' to a number", node)
            if "." in text:
                return self.cast_to(value, "NUMBAR", node=node)
            return self.cast_to(value, "NUMBR", node=node)
        if value.type == "TROOF":
            return self.cast_to(value, "NUMBR", node=node)
        self._error("Cannot implicitly cast NOOB to a number", node)
