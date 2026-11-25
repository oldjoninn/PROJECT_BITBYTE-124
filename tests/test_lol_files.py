# test_lol_files.py
# runs tests/11_*.lol to tests/21_*.lol, one file per fix and extra credit in last_minute_changes.md
#     python -m unittest tests.test_lol_files -v

import os
import sys
import unittest

TESTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(TESTS))

from lexer import tokenize
from runtime_values import SemanticError
from semantic_analyzer import Interpreter
from syntax_analyzer import parse

# file name: (expected output, expected error or None)
EXPECTED = {
    "11_numbar_two_decimals.lol": ("0.29\n0.57\n0.86\n3.99\n1.10\n0.00\n", None),
    "12_mod_negative.lol": ("-2\n-1\n1\n1\n-1.50\n-7\n", None),
    "13_big_numbr.lol": ("10000000000000000001\n12345678901234567890\n10000000000000000002\n-3\n", None),
    "14_repeated_parameter.lol": ("", "semantic error (line 4): Parameter 'a' appears twice in function 'pick'"),
    "15_parameter_named_it.lol": ("14\n", None),
    "16_deep_recursion.lol": ("200\n", "semantic error (line 1): Too many nested function calls or expressions"),
    "17_run_twice.lol": ("count is 1\n", None),
    "18_soft_line_breaks.lol": ("1\n2\n30\na, b, c\nyes\n", None),
    "19_line_continuation.lol": ("3\none two three\n9\n", None),
    "20_yarn_special_characters.lol": (
        "line one\nline two\nname\tvalue\na:b\ncat \U0001F431\nx:WIN\nValue 1: \ntop\nbottom\n", None),
    "21_smoosh_mkay.lol": ("ab\nab\nabc\nxy\nxy\n", None),
}


def run_file(name, interpreter=None):
    with open(os.path.join(TESTS, name), "r", encoding="utf-8") as source_file:
        tokens, errors = tokenize(source_file.read())
    if errors:
        raise AssertionError(f"{name} has lexical errors: {errors}")
    tree, errors = parse(tokens)
    if errors:
        raise AssertionError(f"{name} has syntax errors: {errors}")
    output = []
    interpreter = interpreter or Interpreter()
    interpreter.output_cb = output.append
    try:
        interpreter.execute(tree)
    except SemanticError as error:
        return "".join(output), str(error)
    return "".join(output), None


class NumberedLolFiles(unittest.TestCase):
    def test_each_file(self):
        for name, expected in EXPECTED.items():
            with self.subTest(name):
                self.assertEqual(run_file(name), expected)

    def test_run_twice_on_one_interpreter(self):
        interpreter = Interpreter()
        first = run_file("17_run_twice.lol", interpreter)
        self.assertEqual(run_file("17_run_twice.lol", interpreter), first)


if __name__ == "__main__":
    unittest.main()
