# lolcode interpreter for cmsc 124 final project

language: python 3
tkinter comes with the standard python install so nothing else is needed

## run the interpreter

    python main.py

open a .lol file with the open file button then press execute
the lexemes show in the middle panel and errors show in the console
if there are no lexical errors the syntax analyzer runs next and the parse tree is printed in the terminal

## test from the terminal

lexical analyzer

    python lexer.py tests/sample2.lol

syntax analyzer

    python syntax_analyzer.py tests/10_functions.lol

## files

    main.py              starts the gui
    gui.py               graphical user interface in dark mode
    lexer.py             lexical analyzer
    keywords.py          keyword groups used by the syntax analyzer
    syntax_analyzer.py   syntax analyzer (recursive descent, one method per grammar rule)
    parse_tree.py        parse tree node and tree printer
    tests/               sample programs

## how it works

1. the lexer turns the source into tokens with a lexeme, classification and line number
2. the syntax analyzer checks the tokens against the grammar and builds a parse tree
3. the first syntax error stops the parse and is reported with its line number

## tests

    01_variables.lol    04_smoosh_assign.lol   07_ifelse.lol     10_functions.lol
    02_gimmeh.lol       05_bool.lol            08_switch.lol     errors.lol
    03_arith.lol        06_comparison.lol      09_loops.lol      sample1.lol, sample2.lol

errors.lol has programs with lexical errors for testing the error messages

## status

- lexical analyzer: done
- syntax analyzer: done, prints the parse tree in the terminal
- semantic analyzer: not started yet, the symbol table stays empty until it is done

## group

- Ralph Crisostomo
- Jorge Paguirigan
- Geoseffe Rufo
- Raymond Sarino