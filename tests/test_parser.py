# test_parser.py
# unit tests for the syntax analyzer
#
# how to run them from the project folder
#     python -m unittest discover tests

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from lexer import tokenize
from parse_tree import format_tree
from syntax_analyzer import parse


def parse_source(source):
    tokens, lexer_errors = tokenize(source)
    # a plain assert would be skipped by python -O
    if lexer_errors:
        raise AssertionError(f"the snippet has lexical errors: {lexer_errors}")
    return parse(tokens)


def syntax_errors(source):
    return parse_source(source)[1]


def read_test_file(name):
    with open(os.path.join(ROOT, "tests", name), "r", encoding="utf-8") as source_file:
        return source_file.read()


DECLARATIONS = "HAI\nWAZZUP\nI HAS A x\nI HAS A y\nBUHBYE\n"

# programs that must parse
VALID = {
    "empty program": "HAI\nKTHXBYE",
    "comments before HAI and after KTHXBYE": "BTW hi\nHAI\nKTHXBYE\nBTW bye\n",
    "comment between HAI and WAZZUP": "HAI\nBTW hi\nWAZZUP\nI HAS A x\nBUHBYE\nKTHXBYE",
    "comment after keywords": "HAI BTW a\nWAZZUP BTW b\nBUHBYE BTW c\nKTHXBYE BTW d",
    "comment inside if": DECLARATIONS + "WIN\nO RLY?\nBTW a\nYA RLY\nVISIBLE 1\nOIC\nKTHXBYE",
    "multi line comment": DECLARATIONS + "OBTW\nanything\nTLDR\nVISIBLE x\nKTHXBYE",
    "blank lines": "\n\nHAI\n\n\nVISIBLE 1\n\nKTHXBYE\n\n",
    "visible with and without +": DECLARATIONS + 'VISIBLE "a" + x y\nKTHXBYE',
    "visible with !": DECLARATIONS + "VISIBLE x!\nKTHXBYE",
    "bare variable sets IT": DECLARATIONS + "x\nWTF?\nOMG 1\nGTFO\nOMGWTF\nVISIBLE 2\nOIC\nKTHXBYE",
    "all of with nested operations": DECLARATIONS
        + "VISIBLE ALL OF NOT x AN BOTH OF y AN x AN EITHER OF x AN y MKAY\nKTHXBYE",
    "both maek forms": DECLARATIONS + "x R MAEK x A NUMBAR\nx R MAEK x YARN\nKTHXBYE",
    "smoosh as a call argument": "HOW IZ I f YR a AN YR b\nFOUND YR a\nIF U SAY SO\n"
        + 'HAI\nI IZ f YR SMOOSH "a" AN "b" AN YR 2 MKAY\nKTHXBYE',
    "function with no parameters": "HOW IZ I f\nGTFO\nIF U SAY SO\nHAI\nI IZ f MKAY\nKTHXBYE",
    "nested loops": DECLARATIONS + "IM IN YR a UPPIN YR x TIL BOTH SAEM x AN 3\n"
        + "IM IN YR b NERFIN YR y WILE DIFFRINT y AN 0\nGTFO\nIM OUTTA YR b\nIM OUTTA YR a\nKTHXBYE",
    "mebbe and no wai": DECLARATIONS + "WIN\nO RLY?\nYA RLY\nVISIBLE 1\nMEBBE x\nVISIBLE 2\n"
        + "NO WAI\nVISIBLE 3\nOIC\nKTHXBYE",
}

# programs that must fail, with the line of the expected error
INVALID = {
    "two statements on one line": (DECLARATIONS + "x R 1 y R 2\nKTHXBYE", 6),
    "statement split over lines": (DECLARATIONS + "x R\n5\nKTHXBYE", 6),
    "missing AN": (DECLARATIONS + "VISIBLE SUM OF 1 2\nKTHXBYE", 6),
    "all of missing MKAY": (DECLARATIONS + "VISIBLE ALL OF WIN AN FAIL\nKTHXBYE", 6),
    "call missing MKAY": ("HOW IZ I f\nGTFO\nIF U SAY SO\nHAI\nI IZ f\nKTHXBYE", 5),
    "function missing IF U SAY SO": ("HOW IZ I f\nVISIBLE 1\nHAI\nKTHXBYE", 3),
    "loop missing IM OUTTA YR": (DECLARATIONS + "IM IN YR l UPPIN YR x\nVISIBLE x\nKTHXBYE", 8),
    "loop labels differ": (DECLARATIONS + "IM IN YR a UPPIN YR x\nVISIBLE x\nIM OUTTA YR b\nKTHXBYE", 8),
    "I HAS A outside WAZZUP": (DECLARATIONS + "VISIBLE 1\nI HAS A z\nKTHXBYE", 7),
    "statement before HAI": ("VISIBLE 1\nHAI\nKTHXBYE", 1),
    "statement after KTHXBYE": ("HAI\nKTHXBYE\nVISIBLE 1", 3),
    "two KTHXBYE": ("HAI\nKTHXBYE\nKTHXBYE", 3),
    "missing KTHXBYE": (DECLARATIONS + "VISIBLE 1", 6),
    "GIMMEH a literal": (DECLARATIONS + "GIMMEH 5\nKTHXBYE", 6),
    "O RLY? without YA RLY": (DECLARATIONS + "WIN\nO RLY?\nOIC\nKTHXBYE", 8),
    "WTF? with no OMG": (DECLARATIONS + "WTF?\nOIC\nKTHXBYE", 7),
    "OMG with an expression": (DECLARATIONS + "WTF?\nOMG SUM OF 1 AN 2\nVISIBLE 1\nOIC\nKTHXBYE", 7),
    "all of nested in all of": (DECLARATIONS + "VISIBLE ALL OF ALL OF x AN y MKAY AN x MKAY\nKTHXBYE", 6),
    "smoosh nested in sum of": (DECLARATIONS + 'VISIBLE SUM OF SMOOSH "1" AN "2" AN 3\nKTHXBYE', 6),
    "any of nested in not": (DECLARATIONS + "VISIBLE NOT ANY OF x AN y MKAY\nKTHXBYE", 6),
    "R with nothing after": (DECLARATIONS + "x R\nKTHXBYE", 6),
    "UPPIN missing YR": (DECLARATIONS + "IM IN YR l UPPIN x TIL WIN\nIM OUTTA YR l\nKTHXBYE", 6),
    "keyword used as a variable": ("HAI\nVISIBLE MKAY\nKTHXBYE", 2),
    "FOUND YR outside a function": ("HAI\nFOUND YR 1\nKTHXBYE", 2),
    "GTFO outside loop switch or function": ("HAI\nGTFO\nKTHXBYE", 2),
    "WAZZUP after a statement": ("HAI\nVISIBLE 1\nWAZZUP\nBUHBYE\nKTHXBYE", 3),
    "stray OIC": ("HAI\nOIC\nKTHXBYE", 2),
    "dangling +": (DECLARATIONS + "VISIBLE x +\nKTHXBYE", 6),
}


class ValidPrograms(unittest.TestCase):
    def test_valid_snippets(self):
        for name, source in VALID.items():
            with self.subTest(name):
                self.assertEqual(syntax_errors(source), [])

    def test_valid_test_files(self):
        names = ["01_variables.lol", "02_gimmeh.lol", "03_arith.lol", "04_smoosh_assign.lol",
                 "05_bool.lol", "06_comparison.lol", "07_ifelse.lol", "08_switch.lol",
                 "09_loops.lol", "sample1.lol", "sample2.lol"]
        for name in names:
            with self.subTest(name):
                self.assertEqual(syntax_errors(read_test_file(name)), [])


class TreeShape(unittest.TestCase):
    # the error tests above cannot tell if the tree itself is built right
    def test_statement_tree(self):
        source = ('HAI\nWAZZUP\nI HAS A x ITZ 2\nBUHBYE\n'
                  'VISIBLE SUM OF x AN PRODUKT OF 3 AN 4.5 + "hi"!\n'
                  'x R MAEK x A YARN\nKTHXBYE')
        expected = "\n".join([
            "<program>",
            "  HAI",
            "  <declsection>",
            "    WAZZUP",
            "    <vardecl>",
            "      I HAS A",
            "      varident: x",
            "      ITZ",
            "      numbr: 2",
            "    BUHBYE",
            "  <statements>",
            "    <print>",
            "      VISIBLE",
            "      <arith>",
            "        SUM OF",
            "        varident: x",
            "        <arith>",
            "          PRODUKT OF",
            "          numbr: 3",
            "          numbar: 4.5",
            '      yarn: "hi"',
            "      !",
            "    <assign>",
            "      varident: x",
            "      R",
            "      <cast>",
            "        MAEK",
            "        varident: x",
            "        type: YARN",
            "  KTHXBYE",
        ])
        tree, errors = parse_source(source)
        self.assertEqual(errors, [])
        self.assertEqual(format_tree(tree), expected)

    def test_block_tree(self):
        source = ("HOW IZ I f YR a\nFOUND YR a\nIF U SAY SO\nHAI\n"
                  "IM IN YR l UPPIN YR IT TIL ALL OF WIN AN IT MKAY\n"
                  "WTF?\nOMG 1\nGTFO\nOIC\nIM OUTTA YR l\nKTHXBYE")
        expected = "\n".join([
            "<program>",
            "  <funcdef>",
            "    HOW IZ I",
            "    funcident: f",
            "    param: a",
            "    <statements>",
            "      <return>",
            "        FOUND YR",
            "        varident: a",
            "    IF U SAY SO",
            "  HAI",
            "  <statements>",
            "    <loop>",
            "      IM IN YR",
            "      loopident: l",
            "      UPPIN",
            "      varident: IT",
            "      TIL",
            "      <infbool>",
            "        ALL OF",
            "        troof: WIN",
            "        varident: IT",
            "        MKAY",
            "      <statements>",
            "        <switch>",
            "          WTF?",
            "          <case>",
            "            OMG",
            "            numbr: 1",
            "            <statements>",
            "              GTFO",
            "          OIC",
            "      IM OUTTA YR",
            "      loopident: l",
            "  KTHXBYE",
        ])
        tree, errors = parse_source(source)
        self.assertEqual(errors, [])
        self.assertEqual(format_tree(tree), expected)


class InvalidPrograms(unittest.TestCase):
    def test_invalid_snippets(self):
        for name, (source, line) in INVALID.items():
            with self.subTest(name):
                errors = syntax_errors(source)
                self.assertEqual(len(errors), 1)
                self.assertTrue(errors[0].startswith(f"line {line}:"), errors[0])

    def test_dangling_an_before_yr_line(self):
        # AN at the end of a line is an error even if the next line starts with YR
        errors = syntax_errors(DECLARATIONS + "VISIBLE SMOOSH x AN\nYR\nKTHXBYE")
        self.assertEqual(errors, ["line 6: expected an operand before end of line"])

    def test_functions_file_needs_mkay(self):
        # the spec requires MKAY after a function call (p.7, Calling)
        errors = syntax_errors(read_test_file("10_functions.lol"))
        self.assertEqual(errors, ["line 24: expected MKAY before end of line"])


if __name__ == "__main__":
    unittest.main()
