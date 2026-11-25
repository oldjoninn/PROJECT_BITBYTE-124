# test_bonus.py
# extra credit features from the project spec, PDF page 4, section C.3
#     python -m unittest tests.test_bonus -v

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_failures import Helpers, run, program


class SoftLineBreaks(Helpers):
    def test_comma_separates_statements(self):
        self.assertOutput("HAI, VISIBLE 1, VISIBLE 2, KTHXBYE", "1\n2\n")

    def test_comma_inside_yarn_is_text(self):
        self.assertOutput(program('VISIBLE "a, b"'), "a, b\n")

    def test_comma_glued_to_operand(self):
        self.assertOutput(program("x R 5, VISIBLE x,"), "5\n")

    def test_errors_keep_the_physical_line(self):
        self.assertFailsAt(program("VISIBLE 1, VISIBLE z"), "semantic", 6, "undeclared")

    def test_comma_ends_a_statement(self):
        self.assertFailsAt(program("x R, 5"), "parse", 6, "operand")


class LineContinuation(Helpers):
    def test_three_dots_join_lines(self):
        self.assertOutput(program("VISIBLE SUM OF 1 ...", "AN 2"), "3\n")

    def test_unicode_ellipsis(self):
        self.assertOutput(program("VISIBLE SUM OF 1 …", "AN 2"), "3\n")

    def test_dots_glued_to_operand(self):
        self.assertOutput(program("VISIBLE 1...", "2"), "12\n")

    def test_function_name_after_continuation(self):
        source = "HOW IZ I f\nFOUND YR 7\nIF U SAY SO\nHAI\nVISIBLE I IZ ...\nf MKAY\nKTHXBYE"
        self.assertOutput(source, "7\n")

    def test_dots_must_end_the_line(self):
        self.assertFailsAt(program("VISIBLE 1 ... 2"), "lex", 6, "last")

    def test_continuation_into_nothing(self):
        self.assertFailsAt("HAI\nVISIBLE 1 ...", "lex", 2, "continu")
        self.assertFailsAt(program("VISIBLE 1 ...", ""), "lex", 6, "continu")

    def test_numbars_still_lex(self):
        self.assertOutput(program("VISIBLE 1.5"), "1.50\n")


class YarnSpecialCharacters(Helpers):
    def test_newline_tab_bell_colon(self):
        self.assertOutput(program('VISIBLE "a:)b:>c:od::e"'), "a\nb\tc\ad:e\n")

    def test_hex_code_point(self):
        self.assertOutput(program('VISIBLE "cat :(1F431)"'), "cat \U0001F431\n")

    def test_colon_before_closing_quote_stays_text(self):
        # tests/05_bool.lol line 8 relies on this, so :" is not an escape
        self.assertOutput(program('VISIBLE "x:" + WIN'), "x:WIN\n")

    def test_unknown_or_bad_codes_stay_text(self):
        self.assertOutput(program('VISIBLE "Value 1: " + ":q" + ":(zz)" + ":("'),
                          "Value 1: :q:(zz):(\n")

    def test_escapes_work_in_smoosh_and_switch(self):
        source = program('SMOOSH "a" AN ":)"', 'WTF?', 'OMG "a:)"', 'VISIBLE "hit"', "OIC")
        self.assertOutput(source, "hit\n")

    def test_parse_tree_keeps_raw_text(self):
        from lexer import tokenize
        tokens, _ = tokenize('HAI\nVISIBLE "a:)"\nKTHXBYE')
        self.assertIn("a:)", [token.lexeme for token in tokens])


class OptionalSmooshMkay(Helpers):
    def test_smoosh_with_mkay(self):
        self.assertOutput('HAI\nVISIBLE SMOOSH "a" AN "b" MKAY\nKTHXBYE', "ab\n")

    def test_smoosh_mkay_then_more_print_operands(self):
        self.assertOutput('HAI\nVISIBLE SMOOSH "a" AN "b" MKAY + "c"\nKTHXBYE', "abc\n")

    def test_smoosh_as_last_call_argument_leaves_mkay_to_the_call(self):
        head = "HOW IZ I f YR s\nFOUND YR s\nIF U SAY SO\nHAI\n"
        self.assertOutput(head + 'VISIBLE I IZ f YR SMOOSH "a" AN "b" MKAY\nKTHXBYE', "ab\n")
        self.assertOutput(head + 'VISIBLE I IZ f YR SMOOSH "a" AN "b" MKAY MKAY\nKTHXBYE', "ab\n")


if __name__ == "__main__":
    unittest.main()
