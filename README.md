# lolcode interpreter for cmsc 124 final project

language: python 3
tkinter comes with the standard python install so nothing else is needed

## run the interpreter

    python main.py

## test the lexical analyzer from the terminal

    python lexer.py tests/sample2.lol

## test the syntax analyzer from the terminal

    python syntax_analyzer.py tests/sample2.lol

it prints the parse tree, or the first syntax error with its line number

## run the unit tests

    python -m unittest discover tests

## files

    lexer.py            lexical analyzer
    syntax_analyzer.py  syntax analyzer (recursive descent parser)
    keywords.py         keyword groups the syntax analyzer uses
    parse_tree.py       parse tree node and tree printing
    semantic_analyzer.py  runs the program: statements, flow control, functions, symbol table
    expressions.py      evaluates expressions
    type_casting.py     typecasting rules
    runtime_values.py   values, scopes and the semantic error
    gui.py              graphical user interface
    main.py             starts the gui
    specs/grammar.md    the grammar the syntax analyzer follows
    tests/              sample programs and unit tests

## status

lexical analyzer is done
syntax analyzer is done (milestone 2)
semantic analyzer is done (milestone 3): the gui shows the program output, asks for GIMMEH input in a dialog, and fills the symbol table