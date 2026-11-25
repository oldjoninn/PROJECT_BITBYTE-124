# test_failures.py
# failure modes and pain points of the whole pipeline: lexer -> parser -> interpreter
# page numbers are PDF pages of specs/lolcode_specifications.pdf (printed footer is one less)
#
# FixedBugs holds one regression test per bug fixed in last_minute_changes.md
#     python -m unittest tests.test_failures -v

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lexer import tokenize
from runtime_values import SemanticError
from semantic_analyzer import Interpreter
from syntax_analyzer import parse


def run(source, inputs=()):
    # returns (stage, result): ("lex"|"parse", errors), ("ok", output) or ("semantic", error)
    tokens, errors = tokenize(source)
    if errors:
        return "lex", errors
    tree, errors = parse(tokens)
    if errors:
        return "parse", errors
    output, answers = [], iter(inputs)
    interpreter = Interpreter({"output": output.append, "input": lambda prompt: next(answers)})
    try:
        interpreter.execute(tree)
    except SemanticError as error:
        return "semantic", error
    return "ok", "".join(output)


DECL = "HAI\nWAZZUP\nI HAS A x\nI HAS A y\nBUHBYE\n"  # statements start on line 6


def program(*lines):
    return DECL + "\n".join(lines) + "\nKTHXBYE"


RECURSIVE_COUNT = ("HOW IZ I f YR n\nBOTH SAEM n AN 0\nO RLY?\nYA RLY\nFOUND YR 0\nOIC\n"
                   "FOUND YR SUM OF 1 AN I IZ f YR DIFF OF n AN 1 MKAY\nIF U SAY SO\n"
                   "HAI\nVISIBLE I IZ f YR {} MKAY\nKTHXBYE")


class Helpers(unittest.TestCase):
    def assertOutput(self, source, expected, inputs=()):
        stage, result = run(source, inputs)
        self.assertEqual((stage, result), ("ok", expected))

    def assertFailsAt(self, source, stage, line, fragment=""):
        actual_stage, result = run(source)
        self.assertEqual(actual_stage, stage, result)
        message = str(result[0] if isinstance(result, list) else result)
        self.assertIn(f"line {line}", message)
        self.assertIn(fragment.lower(), message.lower())


class FixedBugs(Helpers):
    # each test failed before its fix in last_minute_changes.md

    def test_numbar_to_yarn_keeps_exact_two_decimals(self):
        # p.6: truncate to two decimals. math.trunc(0.29 * 100) is 28 because of float error
        self.assertOutput(program("VISIBLE 0.29", "VISIBLE 0.57", "VISIBLE MAEK 1.1 A YARN"),
                          "0.29\n0.57\n1.10\n")
        # the spec's own example on p.4: 4 - 3.14 is 0.8599999... in floats, printed as 0.85
        self.assertOutput(program("VISIBLE DIFF OF 4 AN 3.14"), "0.86\n")

    def test_mod_agrees_with_quoshunt_for_negatives(self):
        # QUOSHUNT truncates toward zero (-7/3 = -2) but MOD uses python floor mod (2)
        # so QUOSHUNT*3 + MOD = -4, not -7
        self.assertOutput(program("VISIBLE MOD OF -7 AN 3", "VISIBLE MOD OF 7 AN -3"), "-1\n1\n")

    def test_quoshunt_of_big_numbrs_is_exact(self):
        # int(a / b) goes through a float and loses digits past 2**53
        self.assertOutput(program("VISIBLE QUOSHUNT OF 10000000000000000001 AN 1"),
                          "10000000000000000001\n")

    def test_big_numeric_yarn_to_numbr_is_exact(self):
        # int(float(text)) loses digits; "12345678901234567890" became ...7168
        self.assertOutput(program('VISIBLE MAEK "12345678901234567890" A NUMBR'),
                          "12345678901234567890\n")

    def test_duplicate_parameter_names_are_an_error(self):
        # Scope.declare returns False on the second "a" and the argument is silently dropped
        source = ("HOW IZ I f YR a AN YR a\nFOUND YR a\nIF U SAY SO\n"
                  "HAI\nVISIBLE I IZ f YR 1 AN YR 2 MKAY\nKTHXBYE")
        self.assertEqual(run(source)[0], "semantic")

    def test_parameter_named_it_gets_the_argument(self):
        # p.8: parameters become variables with the argument as initial value
        # the function scope pre-declares IT, so declare("IT", 7) silently fails and IT stays NOOB
        source = "HOW IZ I f YR IT\nFOUND YR IT\nIF U SAY SO\nHAI\nVISIBLE I IZ f YR 7 MKAY\nKTHXBYE"
        self.assertOutput(source, "7\n")

    def test_recursion_200_deep_works(self):
        # each LOLCode call costs ~8 python frames, so depth ~120 already hits RecursionError
        self.assertOutput(RECURSIVE_COUNT.format(200), "200\n")

    def test_runaway_recursion_is_a_semantic_error(self):
        # RecursionError is not a SemanticError: the GUI only catches SemanticError,
        # so the console shows nothing and the traceback goes to the terminal
        source = "HOW IZ I f\nFOUND YR I IZ f MKAY\nIF U SAY SO\nHAI\nI IZ f MKAY\nKTHXBYE"
        try:
            stage, _ = run(source)
        except RecursionError:
            self.fail("RecursionError escaped the interpreter")
        self.assertEqual(stage, "semantic")

    def test_deeply_nested_expression_does_not_crash(self):
        try:
            stage, _ = run("HAI\nVISIBLE " + "NOT " * 600 + "WIN\nKTHXBYE")
        except RecursionError:
            self.fail("RecursionError escaped")
        self.assertIn(stage, ("ok", "semantic"))

    def test_interpreter_can_run_a_program_twice(self):
        # execute() resets the function table but not the global scope
        tree, _ = parse(tokenize("HAI\nWAZZUP\nI HAS A x\nBUHBYE\nKTHXBYE")[0])
        interpreter = Interpreter({"output": lambda text: None})
        interpreter.execute(tree)
        interpreter.execute(tree)


class LexerFailures(Helpers):
    def test_bad_lexemes_each_reported(self):
        stage, errors = run("HAI\nI HAS A v ITZ 1.2.3\nI HAS A bad$name\nKTHXBYE")
        self.assertEqual(stage, "lex")
        self.assertEqual(len(errors), 2)
        self.assertTrue(errors[0].startswith("line 2"))
        self.assertTrue(errors[1].startswith("line 3"))

    def test_bad_number_shapes(self):
        for literal in ("1.", ".5", "1e5", "--5", "5abc", "_x"):
            with self.subTest(literal):
                self.assertEqual(run(f"HAI\nVISIBLE {literal}\nKTHXBYE")[0], "lex")
        # p.3 forbids a leading +; the lexer reads it as the VISIBLE separator, so the parser rejects it
        self.assertEqual(run("HAI\nVISIBLE +5\nKTHXBYE")[0], "parse")

    def test_unclosed_string(self):
        self.assertFailsAt(program('VISIBLE "never closed'), "lex", 6, "closing quote")

    def test_obtw_after_code(self):
        self.assertFailsAt("HAI\nVISIBLE 1 OBTW\nTLDR\nKTHXBYE", "lex", 2, "obtw")

    def test_unclosed_obtw(self):
        self.assertFailsAt("HAI\nOBTW\nKTHXBYE", "lex", 2, "tldr")

    def test_code_after_tldr(self):
        self.assertFailsAt("HAI\nOBTW\nx\nTLDR VISIBLE 1\nKTHXBYE", "lex", 4, "tldr")

    def test_stray_tldr(self):
        self.assertFailsAt("HAI\nTLDR\nKTHXBYE", "lex", 2, "tldr")

    def test_keywords_are_case_sensitive(self):
        self.assertEqual(run("hai\nkthxbye")[0], "parse")

    def test_keyword_prefix_is_an_identifier(self):
        # R must not match the start of "result", ITZ must not match "ITZY"
        source = "HAI\nWAZZUP\nI HAS A result ITZ 1\nI HAS A ITZY ITZ 2\nBUHBYE\nVISIBLE result ITZY\nKTHXBYE"
        self.assertOutput(source, "12\n")

    def test_comment_keywords_inside_strings_are_text(self):
        self.assertOutput(program('VISIBLE "BTW OBTW TLDR"'), "BTW OBTW TLDR\n")

    def test_windows_line_endings_and_tabs(self):
        self.assertOutput("HAI\r\n\tVISIBLE\t1\r\nKTHXBYE\r\n", "1\n")

    def test_unicode_yarn(self):
        self.assertOutput(program('VISIBLE "héllo 🐱"'), "héllo 🐱\n")

    def test_yarn_escapes_are_not_supported(self):
        # pain point: escapes are optional (p.3) but :" ends the string early
        self.assertEqual(run(program('VISIBLE "say :"hi:""'))[0], "lex")


class ParserFailures(Helpers):
    def test_empty_and_comment_only_files(self):
        self.assertFailsAt("", "parse", 1, "HAI")
        self.assertFailsAt("BTW nothing\n", "parse", 1, "HAI")

    def test_hai_with_version_is_rejected(self):
        # pain point: p.2 says the version is not needed; common LOLCode files have HAI 1.2
        self.assertFailsAt("HAI 1.2\nKTHXBYE", "parse", 1, "end of line")

    def test_infinite_bool_needs_mkay_even_at_end_of_line(self):
        self.assertFailsAt("HAI\nVISIBLE ANY OF WIN AN FAIL\nKTHXBYE", "parse", 2, "MKAY")

    def test_mebbe_after_no_wai(self):
        source = program("WIN", "O RLY?", "YA RLY", "VISIBLE 1", "NO WAI", "VISIBLE 2",
                         "MEBBE WIN", "VISIBLE 3", "OIC")
        self.assertFailsAt(source, "parse", 12, "OIC")

    def test_omg_after_omgwtf(self):
        source = program("1", "WTF?", "OMG 2", "VISIBLE 0", "OMGWTF", "VISIBLE 1", "OMG 1",
                         "VISIBLE 2", "OIC")
        self.assertFailsAt(source, "parse", 12, "OIC")

    def test_missing_oic(self):
        self.assertEqual(run(program("WIN", "O RLY?", "YA RLY", "VISIBLE 1"))[0], "parse")

    def test_visible_with_nothing(self):
        self.assertFailsAt(program("VISIBLE"), "parse", 6, "operand")

    def test_bang_not_last(self):
        self.assertFailsAt(program('VISIBLE "a"! "b"'), "parse", 6, "end of line")

    def test_typecast_to_non_type(self):
        self.assertFailsAt(program("x IS NOW A y"), "parse", 6, "type")

    def test_loop_missing_condition_operand(self):
        self.assertFailsAt(program("IM IN YR l UPPIN YR x TIL", "IM OUTTA YR l"), "parse", 6, "operand")

    def test_found_yr_in_loop_outside_function(self):
        self.assertFailsAt(program("IM IN YR l UPPIN YR x", "FOUND YR 1", "IM OUTTA YR l"),
                           "parse", 7, "FOUND YR")


class SemanticFailures(Helpers):
    def test_undeclared_variables(self):
        self.assertFailsAt(program("VISIBLE z"), "semantic", 6, "undeclared")
        self.assertFailsAt(program("z R 1"), "semantic", 6, "undeclared")
        self.assertFailsAt(program("GIMMEH z"), "semantic", 6, "undeclared")
        self.assertFailsAt(program("z IS NOW A NUMBR"), "semantic", 6, "undeclared")

    def test_initializer_cannot_use_itself(self):
        self.assertFailsAt("HAI\nWAZZUP\nI HAS A x ITZ x\nBUHBYE\nKTHXBYE", "semantic", 3, "undeclared")

    def test_redeclaration(self):
        self.assertFailsAt("HAI\nWAZZUP\nI HAS A x\nI HAS A x\nBUHBYE\nKTHXBYE", "semantic", 4, "already")

    def test_noob_only_implicitly_casts_to_troof(self):
        # p.5: implicit NOOB to anything but TROOF is an error
        self.assertFailsAt(program("VISIBLE x"), "semantic", 6, "NOOB")
        self.assertFailsAt(program('VISIBLE SMOOSH "a" AN x'), "semantic", 6, "NOOB")
        self.assertFailsAt(program("VISIBLE SUM OF x AN 1"), "semantic", 6, "NOOB")
        self.assertOutput(program("VISIBLE NOT x"), "WIN\n")

    def test_explicit_noob_casts_give_empty_values(self):
        self.assertOutput(program("VISIBLE MAEK x A NUMBR", "VISIBLE MAEK x A NUMBAR",
                                  "VISIBLE MAEK x A TROOF"), "0\n0.00\nFAIL\n")

    def test_non_numeric_yarns_in_math(self):
        for text in ("abc", "1.2.3", "", " 5", "1e3", "-", "+5"):
            with self.subTest(text):
                self.assertFailsAt(program(f'VISIBLE SUM OF "{text}" AN 1'), "semantic", 6, "cast")

    def test_gimmeh_input_with_spaces_is_not_a_number(self):
        # pain point: a stray space typed in the dialog breaks arithmetic later
        stage, _ = run(program("GIMMEH x", "VISIBLE SUM OF x AN 1"), inputs=[" 5"])
        self.assertEqual(stage, "semantic")

    def test_division_and_modulo_by_zero(self):
        self.assertFailsAt(program("VISIBLE QUOSHUNT OF 1 AN 0"), "semantic", 6, "zero")
        self.assertFailsAt(program("VISIBLE QUOSHUNT OF 1.0 AN 0.0"), "semantic", 6, "zero")
        self.assertFailsAt(program("VISIBLE MOD OF 1 AN 0"), "semantic", 6, "zero")
        self.assertFailsAt(program('VISIBLE MOD OF 1 AN "0"'), "semantic", 6, "zero")

    def test_error_line_inside_function_body(self):
        source = "HOW IZ I f\nVISIBLE z\nIF U SAY SO\nHAI\nI IZ f MKAY\nKTHXBYE"
        self.assertFailsAt(source, "semantic", 2, "undeclared")

    def test_functions_cannot_see_globals(self):
        # p.8: only arguments are accessible
        source = ("HOW IZ I f\nFOUND YR x\nIF U SAY SO\n"
                  "HAI\nWAZZUP\nI HAS A x ITZ 1\nBUHBYE\nVISIBLE I IZ f MKAY\nKTHXBYE")
        self.assertFailsAt(source, "semantic", 2, "undeclared")

    def test_wrong_argument_counts(self):
        head = "HOW IZ I f YR a\nFOUND YR a\nIF U SAY SO\nHAI\n"
        self.assertFailsAt(head + "I IZ f MKAY\nKTHXBYE", "semantic", 5, "expects 1")
        self.assertFailsAt(head + "I IZ f YR 1 AN YR 2 MKAY\nKTHXBYE", "semantic", 5, "expects 1")

    def test_undefined_and_duplicate_functions(self):
        self.assertFailsAt("HAI\nI IZ nope MKAY\nKTHXBYE", "semantic", 2, "undefined")
        source = "HOW IZ I f\nGTFO\nIF U SAY SO\nHOW IZ I f\nGTFO\nIF U SAY SO\nHAI\nKTHXBYE"
        self.assertFailsAt(source, "semantic", 4, "already")

    def test_loop_counter_rules(self):
        # p.7: the loop variable must be declared and castable to a number
        self.assertFailsAt("HAI\nIM IN YR l UPPIN YR i TIL WIN\nIM OUTTA YR l\nKTHXBYE",
                           "semantic", 2, "undeclared")
        self.assertFailsAt(program('x R "abc"', "IM IN YR l UPPIN YR x TIL WIN", "IM OUTTA YR l"),
                           "semantic", 7, "cast")


class SpecBehavior(Helpers):
    # behavior that works today and must keep working

    def test_arithmetic_examples_from_spec(self):
        # p.4 examples
        self.assertOutput(program('VISIBLE PRODUKT OF "2" AN "7"', 'VISIBLE QUOSHUNT OF 5 AN "12"',
                                  'VISIBLE MOD OF 3 AN "3.14"',
                                  "VISIBLE SUM OF QUOSHUNT OF PRODUKT OF 3 AN 4 AN 2 AN 1"),
                          "14\n0\n3.00\n7\n")

    def test_troof_math(self):
        self.assertOutput(program("VISIBLE SUM OF WIN AN WIN", "VISIBLE SUM OF FAIL AN 1.5"),
                          "2\n1.50\n")

    def test_comparison_does_not_cast(self):
        # p.5: no automatic typecasting in comparisons, but NUMBR vs NUMBAR compare by value
        self.assertOutput(program('VISIBLE BOTH SAEM "1" AN 1', "VISIBLE BOTH SAEM WIN AN 1",
                                  "VISIBLE BOTH SAEM 1 AN 1.0", "VISIBLE BOTH SAEM x AN y"),
                          "FAIL\nFAIL\nWIN\nWIN\n")

    def test_troof_casts(self):
        self.assertOutput(program('VISIBLE MAEK "" A TROOF', 'VISIBLE MAEK " " A TROOF',
                                  "VISIBLE MAEK 0.0 A TROOF", 'VISIBLE MAEK "0" A TROOF'),
                          "FAIL\nWIN\nFAIL\nWIN\n")

    def test_numbar_truncates_toward_zero(self):
        self.assertOutput(program("VISIBLE MAEK -3.7 A NUMBR", 'VISIBLE MAEK "-3.7" A NUMBR',
                                  "VISIBLE -0.001"), "-3\n-3\n0.00\n")

    def test_gimmeh_is_always_yarn(self):
        source = program("GIMMEH x", "VISIBLE BOTH SAEM x AN 5", "VISIBLE SUM OF x AN 1")
        self.assertOutput(source, "FAIL\n6\n", inputs=["5"])

    def test_switch_is_strict_and_falls_through(self):
        cases = ["WTF?", "OMG 1", 'VISIBLE "one"', "OMG 2", 'VISIBLE "two"', "GTFO",
                 "OMGWTF", 'VISIBLE "def"', "OIC"]
        self.assertOutput(program("1", *cases), "one\ntwo\n")
        self.assertOutput(program("1.0", *cases), "def\n")  # decided: no NUMBR/NUMBAR match

    def test_gtfo_in_inner_switch_only_leaves_inner_switch(self):
        source = program("1", "WTF?", "OMG 1", "2", "WTF?", "OMG 2", 'VISIBLE "in"', "GTFO", "OIC",
                         'VISIBLE "after"', "OIC")
        self.assertOutput(source, "in\nafter\n")

    def test_gtfo_in_if_leaves_loop(self):
        source = program("x R 0", "IM IN YR l UPPIN YR x", "BOTH SAEM x AN 2", "O RLY?", "YA RLY",
                         "GTFO", "OIC", "IM OUTTA YR l", "VISIBLE x")
        self.assertOutput(source, "2\n")

    def test_gtfo_in_function_returns_noob_and_loop_continues(self):
        source = ("HOW IZ I f\nGTFO\nIF U SAY SO\nHAI\nWAZZUP\nI HAS A x ITZ 0\nBUHBYE\n"
                  "IM IN YR l UPPIN YR x TIL BOTH SAEM x AN 3\nI IZ f MKAY\nIM OUTTA YR l\n"
                  "VISIBLE x\nVISIBLE MAEK IT A TROOF\nKTHXBYE")
        self.assertOutput(source, "3\nFAIL\n")

    def test_found_yr_inside_loop_returns(self):
        source = ("HOW IZ I f\n0\nIM IN YR l UPPIN YR IT\nFOUND YR 5\nIM OUTTA YR l\nIF U SAY SO\n"
                  "HAI\nVISIBLE I IZ f MKAY\nKTHXBYE")
        self.assertOutput(source, "5\n")

    def test_til_and_wile_loops_from_spec(self):
        # p.7 example: both print 2 to 9
        expected = "".join(f"{n}\n" for n in range(2, 10)) * 2
        source = program("x R 2", "IM IN YR p UPPIN YR x TIL BOTH SAEM x AN 10", "VISIBLE x!",
                         "VISIBLE \"\"", "IM OUTTA YR p", "x R 2",
                         "IM IN YR p UPPIN YR x WILE DIFFRINT x AN 10", "VISIBLE x", "IM OUTTA YR p")
        self.assertOutput(source, expected)

    def test_call_result_goes_to_it(self):
        # p.8: return values are stored in IT, even when the call is inside VISIBLE
        source = ("HOW IZ I f\nFOUND YR 99\nIF U SAY SO\nHAI\nFAIL\nVISIBLE I IZ f MKAY\n"
                  'O RLY?\nYA RLY\nVISIBLE "yes"\nNO WAI\nVISIBLE "no"\nOIC\nKTHXBYE')
        self.assertOutput(source, "99\nyes\n")

    def test_arguments_are_passed_by_value(self):
        source = ("HOW IZ I f YR a\na R 100\nFOUND YR a\nIF U SAY SO\n"
                  "HAI\nWAZZUP\nI HAS A x ITZ 1\nBUHBYE\nI IZ f YR x MKAY\nVISIBLE x\nKTHXBYE")
        self.assertOutput(source, "1\n")

    def test_recursion_shallow(self):
        self.assertOutput(RECURSIVE_COUNT.format(50), "50\n")

    def test_errors_keep_earlier_output(self):
        stage, _ = run(program('VISIBLE "before"', "VISIBLE z"))
        self.assertEqual(stage, "semantic")


if __name__ == "__main__":
    unittest.main()
