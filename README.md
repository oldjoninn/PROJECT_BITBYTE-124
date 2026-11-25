# bitbyte lolcode interpreter

a lolcode interpreter written in python 3 for the cmsc 124 final project
it reads a lolcode program then checks it in three stages and runs it
lexical analysis then syntax analysis then semantic analysis and execution
each stage only runs when the stage before it found no errors

---

## contents

1 requirements
2 installation
3 running the interpreter
4 using the gui
5 terminal tools
6 writing a lolcode program
7 language reference
8 typing and casting rules
9 error messages
10 sample programs
11 project structure
12 how it works
13 known limitations

---

## 1 requirements

python 3.8 or newer
tkinter which comes with the standard python install on windows and macos
on some linux distributions tkinter is a separate package

    sudo apt install python3-tk

no other packages are needed

## 2 installation

    git clone https://github.com/oldjoninn/PROJECT_BITBYTE-124.git
    cd PROJECT_BITBYTE-124

## 3 running the interpreter

    python main.py

on some systems the command is `python3` instead of `python`

## 4 using the gui

the window is in dark mode and has these parts

| part | where | what it does |
|---|---|---|
| open file | top right | opens a `.lol` file and loads it into the editor |
| file label | top left | shows the path of the open file or `(None)` |
| text editor | left | where the code is written or edited with line numbers on the side |
| token table | middle | lists every lexeme and its classification |
| symbol table tab | right | lists every visible variable and its value including `IT` |
| parse tree tab | right | shows the parse tree as a collapsible tree |
| execute | below the panels | runs the code that is in the editor |
| console | bottom | shows program output and every error in red |

### step by step

1 click open file and pick a `.lol` file or type code straight into the editor
2 click execute
3 the token table fills in and the console says how many tokens were found
4 if there are no lexical errors the parse tree tab opens and shows the tree
5 if there are no syntax errors the program runs and its output appears in the console
6 when the program reaches `GIMMEH` a dialog asks for a value
the symbol table is refreshed before the dialog so the current values can be checked
closing the dialog without typing gives an empty yarn
7 when the program ends or stops on an error the symbol table shows the final values

every click of execute clears all panels and runs the editor contents again
edits in the editor are not saved back to the file

## 5 terminal tools

### lexical analyzer

    python lexer.py tests/sample1.lol

prints a table of line number lexeme and classification then any lexical errors

### syntax analyzer

    python syntax_analyzer.py tests/sample2.lol

prints the parse tree or the first syntax error with its line number
it exits with code 1 when there is an error

### running a program without the gui

there is no terminal runner file but the interpreter can be called from python

    python -c "from lexer import tokenize; from syntax_analyzer import parse; from semantic_analyzer import Interpreter; t, e = tokenize(open('tests/09_loops.lol').read()); tree, e = parse(t); Interpreter().execute(tree)"

`VISIBLE` prints to the terminal and `GIMMEH` reads from the keyboard

## 6 writing a lolcode program

every program has this shape

    BTW functions may go here
    HAI
        WAZZUP
            I HAS A name ITZ "world"
        BUHBYE

        VISIBLE "hello " + name
    KTHXBYE
    BTW functions may also go here

rules to remember

- keywords are case sensitive and must be written in capital letters
- every statement is on its own line
- all variables are declared between `WAZZUP` and `BUHBYE` right after `HAI`
- the `WAZZUP` block may be left out if there are no variables
- only function definitions may come before `HAI` or after `KTHXBYE`
- a function can be called before the line where it is defined

## 7 language reference

### comments

| syntax | meaning |
|---|---|
| `BTW text` | the rest of the line is ignored |
| `OBTW` then lines then `TLDR` | a multi line comment |

`OBTW` and `TLDR` must each be alone on their line
only a `BTW` comment may follow `TLDR`

### literals and types

| type | examples | meaning |
|---|---|---|
| `NUMBR` | `17` `-4` | whole number |
| `NUMBAR` | `3.14` `-0.5` | decimal number |
| `YARN` | `"hello"` | text in double quotes |
| `TROOF` | `WIN` `FAIL` | true and false |
| `NOOB` | | no value which is what a variable holds before it is given one and it cannot be written as a literal |

### variables

| syntax | meaning |
|---|---|
| `I HAS A x` | declares `x` as `NOOB` |
| `I HAS A x ITZ 5` | declares `x` with a starting value |
| `x R 10` | assigns a new value to `x` |

variable names start with a letter and may have letters digits and underscores
a variable cannot be declared twice
`I HAS A x ITZ x` is an error because the value is evaluated before `x` exists

### output and input

| syntax | meaning |
|---|---|
| `VISIBLE a` | prints `a` then a newline |
| `VISIBLE a + b + c` | prints the values joined together |
| `VISIBLE a b c` | the `+` is optional |
| `VISIBLE a!` | prints without a newline |
| `GIMMEH x` | reads one line of input into `x` as a `YARN` |

### arithmetic

all of these take two operands joined by `AN`

| syntax | result |
|---|---|
| `SUM OF a AN b` | a plus b |
| `DIFF OF a AN b` | a minus b |
| `PRODUKT OF a AN b` | a times b |
| `QUOSHUNT OF a AN b` | a divided by b |
| `MOD OF a AN b` | remainder of a divided by b |
| `BIGGR OF a AN b` | the larger value |
| `SMALLR OF a AN b` | the smaller value |

operations can be nested for example `SUM OF PRODUKT OF 2 AN 3 AN 4` gives 10
two `NUMBR` values give a `NUMBR` and if either value is a `NUMBAR` the result is a `NUMBAR`
`QUOSHUNT OF` two `NUMBR` values rounds toward zero
dividing or taking the modulo by zero is an error

### boolean

| syntax | result |
|---|---|
| `BOTH OF a AN b` | and |
| `EITHER OF a AN b` | or |
| `WON OF a AN b` | exclusive or |
| `NOT a` | not |
| `ALL OF a AN b AN c MKAY` | and of any number of operands |
| `ANY OF a AN b AN c MKAY` | or of any number of operands |

`ALL OF` and `ANY OF` stop at the first operand that decides the answer
`ALL OF` `ANY OF` and `SMOOSH` cannot be nested inside another operation

### comparison

| syntax | result |
|---|---|
| `BOTH SAEM a AN b` | `WIN` when a equals b |
| `DIFFRINT a AN b` | `WIN` when a does not equal b |

a `NUMBR` and a `NUMBAR` compare by value so `BOTH SAEM 2 AN 2.0` is `WIN`
any other pair must have the same type and value so `BOTH SAEM "2" AN 2` is `FAIL`
greater than and less than are written with `BIGGR OF` and `SMALLR OF`

    BTW x >= y
    BOTH SAEM BIGGR OF x AN y AN x

### string concatenation

    SMOOSH a AN b AN c

every operand is turned into a `YARN` and joined together

### typecasting

| syntax | meaning |
|---|---|
| `MAEK x A NUMBR` | gives the value of `x` as a `NUMBR` without changing `x` |
| `MAEK x NUMBR` | the `A` is optional |
| `x IS NOW A NUMBR` | changes `x` itself to a `NUMBR` |

### the it variable

`IT` holds the value of the last expression that was written as a statement by itself
it also holds the return value of the last function call
`O RLY?` and `WTF?` look at `IT`

    BOTH SAEM x AN 1
    BTW IT is now WIN or FAIL

### if else

    BOTH SAEM choice AN 1
    O RLY?
        YA RLY
            VISIBLE "one"
        MEBBE BOTH SAEM choice AN 2
            VISIBLE "two"
        NO WAI
            VISIBLE "something else"
    OIC

`YA RLY` runs when `IT` is `WIN`
each `MEBBE` has its own condition and the first true one runs
`NO WAI` runs when nothing else did
`MEBBE` and `NO WAI` are optional

### switch

    choice
    WTF?
        OMG 1
            VISIBLE "one"
            GTFO
        OMG 2
            VISIBLE "two"
            GTFO
        OMGWTF
            VISIBLE "other"
    OIC

the value after `OMG` must be a literal
a case matches only when the type and the value are both the same as `IT`
so a `YARN` from `GIMMEH` must be cast before it can match `OMG 1`
after a case matches every case below it also runs until `GTFO`
`OMGWTF` is optional and runs only when no case matched

### loops

    IM IN YR count UPPIN YR i TIL BOTH SAEM i AN 10
        VISIBLE i
    IM OUTTA YR count

| part | meaning |
|---|---|
| `count` | the loop name which must be the same at the start and the end |
| `UPPIN` or `NERFIN` | adds 1 or subtracts 1 from the counter after each round |
| `YR i` | the counter which must be a declared variable |
| `TIL condition` | stops when the condition is `WIN` |
| `WILE condition` | stops when the condition is `FAIL` |

the condition is checked before every round
without `TIL` or `WILE` the loop only stops with `GTFO`
the counter is turned into a number when the loop starts

### functions

    HOW IZ I add YR a AN YR b
        FOUND YR SUM OF a AN b
    IF U SAY SO

    HAI
        I IZ add YR 3 AN YR 4 MKAY
        VISIBLE IT
    KTHXBYE

| syntax | meaning |
|---|---|
| `HOW IZ I name YR p1 AN YR p2` | starts a function with its parameters |
| `IF U SAY SO` | ends the function |
| `FOUND YR value` | returns a value |
| `GTFO` | leaves the function and returns `NOOB` |
| `I IZ name YR arg1 AN YR arg2 MKAY` | calls the function |

the number of arguments must match the number of parameters
a function cannot see the variables of the main program only its parameters
every function has its own `IT`
two functions cannot have the same name

### gtfo

`GTFO` leaves the nearest loop switch or function
using it anywhere else is a syntax error

## 8 typing and casting rules

### explicit casts with maek and is now a

| from | to `TROOF` | to `NUMBR` | to `NUMBAR` | to `YARN` |
|---|---|---|---|---|
| `NOOB` | `FAIL` | `0` | `0.0` | `"NOOB"` |
| `TROOF` | same | `WIN` is 1 `FAIL` is 0 | 1.0 or 0.0 | `"WIN"` or `"FAIL"` |
| `NUMBR` | 0 is `FAIL` anything else `WIN` | same | adds `.0` | the digits |
| `NUMBAR` | 0.0 is `FAIL` anything else `WIN` | drops the decimals | same | cut to two decimals |
| `YARN` | empty is `FAIL` anything else `WIN` | only if it looks like a number | only if it looks like a number | same |

a `NUMBAR` turned into a `YARN` is cut and not rounded so `3.14159` becomes `"3.14"`
a `YARN` looks like a number when it has digits an optional minus sign at the front and at most one dot

### implicit casts

these happen on their own when an operation needs a certain type

- arithmetic and loop counters need numbers
a numeric `YARN` with a dot becomes a `NUMBAR` and one without a dot becomes a `NUMBR`
`TROOF` becomes 1 or 0
`NOOB` is an error
- boolean operations and `O RLY?` need a `TROOF`
`NOOB` becomes `FAIL`
- `VISIBLE` and `SMOOSH` need a `YARN`
`NOOB` is an error so a variable must be given a value before it is printed

## 9 error messages

errors are shown in the console in red with their line number
the interpreter stops at the first stage that has errors

### lexical errors

all lexical errors in the file are listed together

| message | cause |
|---|---|
| `unknown lexeme x` | a word that is not a keyword literal or valid name like `1.2.3` or `bad$name` |
| `string is missing its closing quote` | a `"` with no matching `"` on the same line |
| `obtw must be alone on its line` | code before `OBTW` |
| `tldr must be alone on its line` | code after `TLDR` that is not a `BTW` comment |
| `obtw has no matching tldr` | the file ends inside a comment |
| `tldr has no matching obtw` | a `TLDR` with no comment open |

### syntax errors

only the first syntax error is shown
some common ones are

| message | cause |
|---|---|
| `expected HAI` | the program does not start with `HAI` |
| `expected an operand before end of line` | the line ended too early like `SUM OF 1 AN` |
| `expected end of line` | extra tokens after a full statement |
| `variables must be declared between WAZZUP and BUHBYE` | `I HAS A` in the middle of the program |
| `WAZZUP must come right after HAI` | a second or late `WAZZUP` block |
| `FOUND YR is only allowed inside a function` | `FOUND YR` in the main program |
| `GTFO is only allowed inside a loop a switch or a function` | a stray `GTFO` |
| `X cannot be nested inside another operation` | `ANY OF` `ALL OF` or `SMOOSH` inside another operation |
| `loop a is closed with b` | the loop names at the start and end do not match |
| `only function definitions may come after KTHXBYE` | other code after the program ends |

### semantic errors

these appear while the program runs and the output printed before the error stays in the console

| message | cause |
|---|---|
| `Undeclared variable` | using a name that was never declared |
| `Variable is already declared` | declaring the same name twice |
| `Undefined function` | calling a function that does not exist |
| `Function is already defined` | two functions with the same name |
| `Function expects n argument(s)` | wrong number of arguments |
| `Division by zero` or `Modulo by zero` | dividing by zero |
| `Cannot implicitly cast NOOB to ...` | using a variable with no value in math or output |
| `Cannot cast YARN to NUMBR` | casting text that is not a number |

## 10 sample programs

all are in the `tests` folder and can be opened from the gui

| file | what it tests |
|---|---|
| `01_variables.lol` | declarations and starting values |
| `02_gimmeh.lol` | input |
| `03_arith.lol` | arithmetic operations |
| `04_smoosh_assign.lol` | concatenation assignment and casting |
| `05_bool.lol` | boolean operations |
| `06_comparison.lol` | comparisons and multi line comments |
| `07_ifelse.lol` | if else with a menu |
| `08_switch.lol` | switch case |
| `09_loops.lol` | counting up and down with loops |
| `10_functions.lol` | function definitions and calls |
| `sample1.lol` `sample2.lol` | general programs |
| `errors.lol` | lexical errors on purpose |

## 11 project structure

    main.py               starts the gui
    gui.py                graphical user interface
    lexer.py              lexical analyzer
    keywords.py           keyword groups the syntax analyzer uses
    syntax_analyzer.py    syntax analyzer which is a recursive descent parser
    parse_tree.py         parse tree node and tree printing
    type_casting.py       error reporting and typecasting rules
    expressions.py        evaluates expressions
    semantic_analyzer.py  runs statements flow control and functions and keeps the symbol table
    runtime_values.py     values scopes the semantic error and the return and break signals
    tests/                sample lolcode programs

## 12 how it works

### lexical analysis

the lexer reads the code line by line
multi word keywords are tried longest first so `IS NOW A` is found before `A`
a keyword must end at a space so `R` does not match the start of `result`
numbers yarns troofs and types are matched with regular expressions
a name after `HOW IZ I` or `I IZ` is a function name
a name after `IM IN YR` or `IM OUTTA YR` is a loop name
every other name is a variable
a yarn becomes three tokens which are the opening quote the text and the closing quote

### syntax analysis

the parser is recursive descent so every grammar rule has its own method
the grammar rule is written as a comment above each method
it also checks the end of every line and where `FOUND YR` and `GTFO` are allowed
the result is a tree of nodes shown in the parse tree tab

### semantic analysis and execution

the interpreter walks the parse tree and calls `visit_<kind>` for each node
it is split into three layers that build on each other

    TypeCaster  →  ExpressionEvaluator  →  Interpreter

all functions are registered before the program runs so they can be called before they are defined
variables live in scopes and a function call gets a new scope with no link to the main program
`FOUND YR` and `GTFO` work by raising signals that the nearest function loop or switch catches
python errors like dividing by zero are turned into semantic errors with a line number

## 13 known limitations

- only the first syntax error is reported
- `GIMMEH` from the terminal runner stops with a python error if there is no input left
- there are no automated unit tests and testing is done with the sample programs
- the editor has no save button so changes must be copied back to the file by hand