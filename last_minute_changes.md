# Last Minute Changes

## 2026-11-25: bug fixes from the code review, and extra credit features

The work is on the branch `last-minute-fixes`, made from `main` at `158b096`. Nothing is committed.

Every change quotes the spec sentence it relies on. When no sentence covers a change, the entry says so and calls it our own choice. Page references give the PDF page:
- In `lolcode_specifications.pdf`, the printed footer is one lower than the PDF page.
- In `project_specifications.pdf`, every footer says "Page 5", so only the PDF page is given.

Each bug fix has a regression test in `tests/test_failures.py`, in the class `FixedBugs`. Each test failed before its fix. The extra credit features are tested in `tests/test_bonus.py`.

Changes 1 to 7 are bug fixes. Changes 8 to 11 are extra credit and leniency features. Arrays were left out, as you chose.

### Bug fixes

### 1. NUMBAR values print the right two decimals

**Code before**
```python
# type_casting.py, _cast_to_yarn
truncated = math.trunc(float(value.val) * 100) / 100
```
**Code after**
```python
# round(..., 6) removes float noise first: 0.29 * 100 is 28.999999999999996
truncated = math.trunc(round(float(value.val) * 100, 6)) / 100
```
- **What changed:** `VISIBLE 0.29` printed `0.28`, and `VISIBLE 0.57` printed `0.56`. Both now print their real value.
- **How it was applied:** the product is rounded to 6 decimal places before truncating. That removes the tiny float error and still cuts the decimals instead of rounding them.
- **Spec:** `lolcode_specifications.pdf`, PDF page 6 (printed Page 5), Typecasting, NUMBAR row:
  > "Casting NUMBARs to YARN will truncate the decimal portion up to two decimal places."

  0.29 truncated to two decimals is 0.29. The old code broke this rule because of float error, not because of the rule. The spec's own example on PDF page 4 (printed Page 3), `DIFF OF 4 AN 3.14 BTW result is NUMBAR`, printed `0.85` and now prints `0.86`.
- **Reason:** fixing wrong output.
- **Improvement:** every NUMBAR that VISIBLE, SMOOSH or MAEK turns into a YARN shows its real digits.
- **What it does to the code:** a value within a millionth of the next hundredth, like `1.9999999`, now prints `2.00`. Values that close to the next hundredth are rare. The symbol table is not affected, because it uses `Value.__repr__`.
- **Test:** `test_numbar_to_yarn_keeps_exact_two_decimals`. Before the fix it failed with `'0.28\n0.56\n1.10\n' != '0.29\n0.57\n1.10\n'`.

### 2. MOD OF with negative numbers agrees with QUOSHUNT OF

**Code before**
```python
# expressions.py, _compute_arith
if operator == "MOD OF":
    ...
    return a % b
```
**Code after**
```python
if operator == "MOD OF":
    ...
    # same sign rule as QUOSHUNT, so QUOSHUNT * b + MOD gives back a
    if result_type == "NUMBAR":
        return math.fmod(a, b)
    return a - b * truncating_divide(a, b)
```
- **What changed:** `MOD OF -7 AN 3` gave `2` and now gives `-1`. `MOD OF 7 AN -3` gave `-2` and now gives `1`.
- **How it was applied:** NUMBRs use the new `truncating_divide` from change 3. NUMBARs use `math.fmod`, which follows the same sign rule.
- **Spec:** `lolcode_specifications.pdf`, PDF page 4 (printed Page 3), Arithmetic/Mathematical Operations, has only this line for MOD:
  > "MOD OF <x> AN <y> BTW % (modulo)"

  It does not say what sign a negative remainder has. **The sign rule is our own choice.** QUOSHUNT already rounded toward zero (`-7 / 3` is `-2`), and Python's `%` rounds down. The two did not fit together, because `-2 × 3 + 2` is `-4`, not `-7`. Now `QUOSHUNT × y + MOD` always gives back `x`.
- **Reason:** QUOSHUNT and MOD disagreed with each other.
- **Improvement:** a negative remainder now has the same sign as `x`, as in C.
- **What it does to the code:** results only change when an operand is negative. The spec example `MOD OF 3 AN "3.14"` still gives `3.00`.
- **Test:** `test_mod_agrees_with_quoshunt_for_negatives`. Before the fix it failed with `'2\n-2\n' != '-1\n1\n'`.

### 3. Big NUMBRs keep every digit

**Code before**
```python
# expressions.py, _compute_arith, QUOSHUNT OF
return int(a / b)

# type_casting.py, _yarn_to_number
return Value("NUMBR", int(float(text)))
```
**Code after**
```python
# expressions.py, new module-level function
def truncating_divide(a, b):
    # exact integer division rounded toward zero, with no float in between
    quotient = abs(a) // abs(b)
    if (a >= 0) == (b >= 0):
        return quotient
    return -quotient
...
return truncating_divide(a, b)

# type_casting.py
# Decimal keeps every digit; int() still drops the decimal part
return Value("NUMBR", int(Decimal(text)))
```
- **What changed:**
  - `QUOSHUNT OF 10000000000000000001 AN 1` gave `10000000000000000000` and now gives the exact number.
  - `MAEK "12345678901234567890" A NUMBR` gave `12345678901234567168` and now gives the exact number.
- **How it was applied:** both places converted the number to a Python float, which only keeps about 16 digits. Integer division (`//`) and `Decimal` never go through a float.
- **Spec:**
  - `lolcode_specifications.pdf`, PDF page 3 (printed Page 2), Data Types, NUMBR row: "These are sequences of digits without a decimal point (.) and are not enclosed by double quotes." No size limit is given, and the lexer already accepts NUMBRs of any length.
  - PDF page 6 (printed Page 5), NUMBAR row: "Casting NUMBARs to NUMBR will truncate the decimal portion of the NUMBAR." `int(Decimal("-3.7"))` is still `-3`, so the truncation is kept.
  - The spec does not mention precision itself. Losing digits was our bug.
- **Reason:** fixing wrong results.
- **Improvement:** NUMBR math and YARN-to-NUMBR casts are exact at any size.
- **What it does to the code:** none for normal-sized numbers. Python's `int(Decimal(...))` truncates toward zero, as `int(float(...))` did.
- **Tests:** `test_quoshunt_of_big_numbrs_is_exact` and `test_big_numeric_yarn_to_numbr_is_exact`. Before the fix they failed with `...000` and `...7168`.

### 4. A function cannot repeat a parameter name

**Code before**
```python
# semantic_analyzer.py, _register_function
if name in self.functions:
    self._error(f"Function '{name}' is already defined", name_node)
# store the whole node so a call can read its params and body
self.functions[name] = node
```
**Code after**
```python
if name in self.functions:
    self._error(f"Function '{name}' is already defined", name_node)
# every parameter needs its own name so each argument has a variable to go into
seen = set()
for child in node.children:
    if child.kind == "param":
        parameter = self.get_node_lexeme(child)
        if parameter in seen:
            self._error(f"Parameter '{parameter}' appears twice in function '{name}'", child)
        seen.add(parameter)
# store the whole node so a call can read its params and body
self.functions[name] = node
```
- **What changed:** `HOW IZ I f YR a AN YR a` was accepted, and the second argument was silently dropped. It is now a semantic error on the definition's line.
- **How it was applied:** the check runs when functions are registered, before the program starts.
- **Spec:** `lolcode_specifications.pdf`, PDF page 8 (printed Page 7), Functions, Definition:
  > "The parameters in the function become a variable of that function, with the passed argument as the initial value."

  With two parameters named `a`, the second argument never becomes the initial value of any variable.
- **Reason:** a silent wrong result is worse than an error.
- **Improvement:** the mistake is reported where it was made.
- **What it does to the code:** functions with distinct parameter names are not affected.
- **Test:** `test_duplicate_parameter_names_are_an_error`. Before the fix it failed with `'ok' != 'semantic'`.

### 5. A parameter named IT receives its argument

**Code before**
```python
# semantic_analyzer.py, _make_function_scope
function_scope = Scope(parent=None)
# the function has its own it
function_scope.declare("IT", Value("NOOB", None))
for index in range(len(parameter_nodes)):
    ...
    function_scope.declare(parameter_name, argument_value)
return function_scope
```
**Code after**
```python
function_scope = Scope(parent=None)
for index in range(len(parameter_nodes)):
    ...
    function_scope.declare(parameter_name, argument_value)
# the function has its own it, declared last so a parameter named IT keeps its argument
function_scope.declare("IT", Value("NOOB", None))
return function_scope
```
- **What changed:** `HOW IZ I f YR IT` then `FOUND YR IT` returned NOOB, which then failed with "Cannot implicitly cast NOOB to YARN". It now returns the argument.
- **How it was applied:** the line that declares IT moved below the parameter loop. `Scope.declare` does nothing when the name already exists, so IT stays as the parameter.
- **Spec:** the same sentence as change 4, PDF page 8 (printed Page 7):
  > "The parameters in the function become a variable of that function, with the passed argument as the initial value."
- **Reason:** the parameter was silently ignored.
- **Improvement:** every parameter name works the same way.
- **What it does to the code:** functions without a parameter named IT behave exactly as before.
- **Test:** `test_parameter_named_it_gets_the_argument`. Before the fix it failed with a semantic error instead of `'7\n'`.

### 6. Deep recursion works, and runaway recursion is a normal error

**Code before**
```python
# semantic_analyzer.py, execute
for child in root_node.children:
    if child.kind == "declsection" or child.kind == "statements":
        self.visit(child)
return Value("NOOB", None)

# syntax_analyzer.py, parse
try:
    return Parser(tokens).parse_program(), []
except ParseError as error:
    return None, [str(error)]
```
**Code after**
```python
# each LOLCode call uses about 8 python frames, so the default limit of 1000 is too low
sys.setrecursionlimit(max(sys.getrecursionlimit(), 4000))
# only declarations and statements are run
try:
    for child in root_node.children:
        if child.kind == "declsection" or child.kind == "statements":
            self.visit(child)
except RecursionError:
    self._error("Too many nested function calls or expressions")
return Value("NOOB", None)

# syntax_analyzer.py, parse
parser = Parser(tokens)
try:
    return parser.parse_program(), []
except ParseError as error:
    return None, [str(error)]
except RecursionError:
    return None, [f"line {parser.previous_line()}: expression is nested too deeply"]
```
- **What changed:**
  - A recursive function more than about 120 calls deep crashed with Python's `RecursionError`. The GUI only catches `SemanticError`, so the console showed nothing and the traceback went to the terminal.
  - Recursion 200 deep now works. Runaway recursion shows "Too many nested function calls or expressions" in red in the console.
  - An expression nested thousands of levels deep, like 3000 `NOT`s, is now a syntax error instead of a crash.
- **How it was applied:**
  - The Python recursion limit is raised to 4000, which allows about 400 levels of LOLCode recursion.
  - `RecursionError` is turned into the same error types the GUI already shows.
  - The parser keeps a reference to itself so the error can name the line it reached.
- **Spec:** **not in the spec. This is our own choice.** The LOLCode spec does not mention recursion depth. The closest rule is `project_specifications.pdf`, PDF page 4, GUI item 6:
  > "Console – Input/Output of the program should be reflected in the console."

  Before this change, the error never reached the console.
- **Reason:** a crash with an empty console looks like the interpreter is broken.
- **Improvement:** recursive programs like factorial or countdown work to a useful depth, and every failure is shown in the console.
- **What it does to the code:**
  - The runtime error always says line 1, because no node is at hand where it is caught.
  - The limit of 4000 was tested on Python 3.15 on macOS only. The project spec, PDF page 5, asks that the code "can be run in the Windows OS". Windows gives Python a smaller C stack. A much higher limit could crash there, so the limit was kept at 4000.
- **Tests:** `test_recursion_200_deep_works`, `test_runaway_recursion_is_a_semantic_error` and `test_deeply_nested_expression_does_not_crash`. Before the fix all three raised `RecursionError: maximum recursion depth exceeded`.
- **GUI check:** the real `LolInterpreterGUI` ran a 200-deep call and printed `200`. A 2000-deep call printed the red error, and the symbol table still filled in.

### 7. The same Interpreter can run a program twice

**Code before**
```python
# semantic_analyzer.py, __init__
self.global_scope = Scope()
self.current_scope = self.global_scope
...
self.global_scope.declare("IT", Value("NOOB", None))
```
**Code after**
```python
# __init__ ends with
self._reset_scopes()

# starts with only IT so the same interpreter can run a program again
def _reset_scopes(self):
    self.global_scope = Scope()
    self.current_scope = self.global_scope
    # it is the implicit variable that holds the last bare expression
    self.global_scope.declare("IT", Value("NOOB", None))

# execute, after self.functions = {}
self._reset_scopes()
```
- **What changed:** running a program a second time on the same `Interpreter` failed with "Variable 'x' is already declared", because the variables from the first run were still there.
- **How it was applied:** the three scope lines moved into `_reset_scopes`, which both `__init__` and `execute` call.
- **Spec:** **not in the spec. This is our own choice.**
- **Reason:** `execute` already reset the function table, but not the variables. Now it resets both.
- **Improvement:** each run starts clean, as the function table already did.
- **What it does to the code:** nothing visible. The GUI creates a new `Interpreter` on every EXECUTE.
- **Test:** `test_interpreter_can_run_a_program_twice`. Before the fix it raised "Variable 'x' is already declared".

### Extra credit and leniency

The extra credit list is in `project_specifications.pdf`, PDF page 4, section C.3:
> "Implementing features beyond the minimum project requirements may earn bonus points. The number of points awarded will depend on the complexity and quality of the implementation. Possible bonus features include the following:"

Loop-nesting, MEBBE, else-if clauses, suppressing the newline with `!`, nesting of different flow control statements, if-else nesting and switch-nesting already worked before this change. Each one was checked by running a small program. Arrays were left out, as you chose.

### 8. Soft-line breaks with a comma

**Code before**
```python
# lexer.py
SYMBOL_KEYWORDS = {"!", "+"}
WORD_ENDERS = '"!+'

@dataclass
class Token:
    lexeme: str
    classification: str
    line: int

# syntax_analyzer.py
def on_current_line(self):
    # true if the next token is on the same line as the last token read
    token = self.peek()
    return token is not None and self.position > 0 and token.line == self.previous_line()
```
**Code after**
```python
# lexer.py
",": "Soft Line Break",                    # new entry in KEYWORDS
SYMBOL_KEYWORDS = {"!", "+", ",", "...", "…"}
WORD_ENDERS = '"!+,…'

@dataclass
class Token:
    lexeme: str
    classification: str
    line: int
    # the statement the token belongs to; a comma starts a new one and ... continues one
    statement: int

# lexer.py, scan_keyword
if keyword == ",":
    self.add_token(keyword, KEYWORDS[keyword], line_number)
    self.statement += 1
    return end

# keywords.py
IGNORED_CLASSES = {"Single Line Comment Delimiter", "Multi Line Comment Delimiter",
                   "Soft Line Break", "Line Continuation"}

# syntax_analyzer.py
def on_current_line(self):
    # true if the next token is in the same statement as the last token read
    # a statement is one line, unless a comma splits it or ... joins the next line
    token = self.peek()
    return (token is not None and self.position > 0
            and token.statement == self.tokens[self.position - 1].statement)
```
- **What changed:** a comma now ends a statement, as a new line does. `HAI, VISIBLE 1, VISIBLE 2, KTHXBYE` runs and prints `1` and `2`. A comma inside a YARN is still text.
- **How it was applied:**
  - Every token now carries two numbers. `line` is the physical line, used in error messages. `statement` is the logical line, used by the parser to find where a statement ends.
  - The lexer starts a new statement at every new line and after every comma.
  - The three parser checks that compared `.line` now compare `.statement`: `on_current_line`, `parse_statement` and `parse_operandlist`.
  - The comma still appears in the token list as "Soft Line Break". The parser ignores it, as it ignores comments, through `IGNORED_CLASSES`. That set replaces `COMMENT_CLASSES`.
  - `keyword_ends_cleanly` also accepts a comma after a keyword, so `HAI,` works.
- **Spec:** `project_specifications.pdf`, PDF page 4, Extra Credit table:
  > "Soft-line/command breaks (,)"
- **Reason:** extra credit.
- **Improvement:** short statements can share a line, and errors still give the physical line. In `VISIBLE 1, VISIBLE z` on line 6, the error says line 6.
- **What it does to the code:** without commas or `...`, every statement number matches its line, so old programs parse the same. All 13 sample `.lol` files give byte-for-byte the same tokens, parse trees and output as `main`.
- **Tests:** class `SoftLineBreaks` in `tests/test_bonus.py`.

### 9. Line continuation with three dots

**Code before:** no `...` keyword. `VISIBLE SUM OF 1 ...` gave "unknown lexeme ...".

**Code after**
```python
# lexer.py, new KEYWORDS entries
"...": "Line Continuation",
"…": "Line Continuation",
LINE_CONTINUATIONS = {"...", "…"}

# lexer.py, tokenize: a new statement starts on each line unless the last line ended with ...
if self.continued_from is None:
    self.statement += 1
elif not line.strip():
    self.add_error(self.continued_from, "line continuation is followed by an empty line")
self.continued_from = None
...
if self.continued_from is not None:
    self.add_error(self.continued_from, "line continuation is followed by the end of the file")

# lexer.py, scan_keyword
if keyword in LINE_CONTINUATIONS:
    self.add_token(keyword, KEYWORDS[keyword], line_number)
    if line[end:].strip():
        self.add_error(line_number, f"{keyword} must be the last thing on its line")
    else:
        self.continued_from = line_number
    return len(line)

# lexer.py, the identifier kind now looks back through a ...
def previous_token_in_statement(self):
    # like previous_token_on_line, but a ... carries the statement onto the next line
    for token in reversed(self.tokens):
        if token.statement != self.statement:
            return None
        if token.lexeme not in LINE_CONTINUATIONS:
            return token
    return None
```
- **What changed:** a line that ends with `...` or the single character `…` continues onto the next line. `VISIBLE SUM OF 1 ...` followed by `AN 2` prints `3`.
- **How it was applied:**
  - The next line keeps the same statement number, so the parser reads both lines as one statement. The parser needed no other change.
  - `is_word_end` also stops a word at `...`, so `VISIBLE 1...` works without a space.
  - Identifier kinds now look at the previous token in the statement, not on the physical line. So in `I IZ ...` followed by `f MKAY`, `f` is still a Function Identifier.
- **Errors:**
  - `...` followed by more code on its line is a lexical error.
  - `...` followed by an empty line, or by the end of the file, is a lexical error.
- **Spec:** `project_specifications.pdf`, PDF page 4, Extra Credit table:
  > "Line continuation (...)"
- **Reason:** extra credit.
- **Improvement:** long expressions can be split over several lines.
- **What it does to the code:** NUMBARs such as `1.5` still lex as before, because only three dots in a row count.
- **Tests:** class `LineContinuation` in `tests/test_bonus.py`.

### 10. Special characters in a YARN

**Code before**
```python
# expressions.py
def visit_yarn(self, node):
    return Value("YARN", str(self.get_node_lexeme(node)))
```
**Code after**
```python
# extra credit: special characters in a YARN, written with a colon
YARN_SPECIAL_CHARACTERS = {")": "\n", ">": "\t", "o": "\a", ":": ":"}
HEX_DIGITS = "0123456789abcdefABCDEF"


def decode_yarn(raw):
    # :) newline, :> tab, :o bell, :: colon, :(hex) unicode code point
    # any other colon stays as typed; :" is left out because "x:" + WIN must still close the yarn
    ...

def visit_yarn(self, node):
    return Value("YARN", decode_yarn(self.get_node_lexeme(node)))
```
- **What changed:** inside a YARN, `:)` is a new line, `:>` is a tab, `:o` is a bell, `::` is one colon, and `:(1F431)` is the character with that hexadecimal code (🐱).
- **How it was applied:** the codes are decoded when the YARN is evaluated, not in the lexer. The token list and the parse tree still show the YARN exactly as typed.
- **What was left out, and why:**
  - **`:"` (an escaped quote) is not supported.** `tests/05_bool.lol` line 8 is `VISIBLE "x:" + WIN + " y:" + WIN`. If `:"` were an escape, `"x:"` would not close there and the file would fail to lex. That file and the other provided tests must keep working, so a colon before a quote stays plain text.
  - **Any other colon also stays as typed.** `"Value 1: "` in `06_comparison.lol` and a bad code like `:(zz)` print as written instead of raising an error.
  - `:{var}` (inserting a variable's value) is not supported.
- **Spec:**
  - `project_specifications.pdf`, PDF page 4, Extra Credit table: "Special characters in a YARN (:>, :), etc)" and "Special characters in strings".
  - `lolcode_specifications.pdf`, PDF page 3 (printed Page 2), Data Types, YARN row: "Special characters inside YARNs (e.g. :), :>, etc.) are not required."
  - The spec names only `:)` and `:>`. The meanings of `:o`, `::` and `:(hex)` come from the original LOLCode 1.2 specification, which `project_specifications.pdf` PDF page 2 links to. That page was not re-read for this change.
- **Reason:** extra credit, without breaking the provided test files.
- **Improvement:** output can contain new lines and tabs inside one VISIBLE. This also works in SMOOSH and OMG cases.
- **What it does to the code:** a YARN that happens to contain `:)`, such as a smiley, now prints a new line there. None of the 13 sample files contain one, and their output is unchanged.
- **Tests:** class `YarnSpecialCharacters` in `tests/test_bonus.py`.

### 11. SMOOSH may end with an optional MKAY

**Code before**
```python
# syntax_analyzer.py, parse_operand
if lexeme == "SMOOSH":
    return Node("concat", [self.take_operator()] + self.parse_operandlist())
```
**Code after**
```python
if lexeme == "SMOOSH":
    return self.parse_concat()

# <concat> ::= SMOOSH <operandlist> | SMOOSH <operandlist> MKAY
def parse_concat(self):
    node = Node("concat", [self.take_operator()] + self.parse_operandlist())
    if self.on_current_line() and self.peek_lexeme() == "MKAY" and self.smoosh_owns_mkay():
        node.children.append(self.keyword("MKAY"))
    return node

def smoosh_owns_mkay(self):
    # outside a call the MKAY can only close the SMOOSH
    # inside a call it closes the SMOOSH only if the call still has its own MKAY or AN YR after it
    if self.call_depth == 0:
        return True
    following = self.peek(1)
    return (following is not None and following.statement == self.peek().statement
            and following.lexeme in {"MKAY", "AN"})

# parse_call counts how deep the calls are
self.call_depth += 1
... the arguments ...
self.call_depth -= 1
```
- **What changed:** `VISIBLE SMOOSH "a" AN "b" MKAY` was a syntax error and now prints `ab`. SMOOSH without MKAY works as before.
- **How it was applied:**
  - Inside a function call, one MKAY may be needed to close the call. In `I IZ f YR SMOOSH "a" AN "b" MKAY`, the MKAY belongs to the call.
  - In `I IZ f YR SMOOSH "a" AN "b" MKAY MKAY`, the first MKAY closes the SMOOSH and the second closes the call.
  - `call_depth` tells `parse_concat` whether it is inside a call.
  - `visit_concat` already skipped an MKAY child, so the interpreter needed no change.
  - `specs/grammar.md` now has `<concat> ::= SMOOSH <operandlist> | SMOOSH <operandlist> MKAY`.
- **Spec:** `lolcode_specifications.pdf`, PDF page 5 (printed Page 4), String Concatenation:
  > "SMOOSH does not require the MKAY keyword."

  "Does not require" means MKAY is optional, not forbidden.
- **Reason:** you chose this leniency change from the review.
- **Improvement:** programs written with the optional MKAY now run.
- **What it does to the code:** the old test `test_smoosh_with_trailing_mkay_is_rejected` was removed, because it checked the old behavior. HAI with a version number is still rejected, as you chose.
- **Tests:** class `OptionalSmooshMkay` in `tests/test_bonus.py`.

### Verification of changes 1 to 11

- `python3 -m unittest discover tests` runs 91 tests, and all pass:
  - 7 from `tests/test_parser.py`.
  - 63 from `tests/test_failures.py`.
  - 21 from `tests/test_bonus.py`.
- All 13 `tests/*.lol` files were run on `main` and on this branch, and the outputs were compared. The tokens, parse trees and program output are byte-for-byte identical. As before:
  - `01_variables.lol` still stops at line 19.
  - `10_functions.lol` still needs its MKAY on line 24.
  - `errors.lol` still shows its lexical errors.
- The real `LolInterpreterGUI` ran one program that used a comma, `...`, `:)`, `0.29`, SMOOSH with MKAY and a 200-deep recursive call. The console printed `a`, then `b0.29 200`. A 2000-deep call then printed the red recursion error, and the symbol table filled in. The window was not checked by eye.
- Not done: nothing is committed, and the code was not run on Windows.
