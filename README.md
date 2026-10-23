# lolcode interpreter for cmsc 124 final project

language: python 3
tkinter comes with the standard python install so nothing else is needed

## run the interpreter

    python main.py

## test the lexical analyzer from the terminal

    python lexer.py tests/sample2.lol

## run the automated tests

    python -m unittest discover tests

## files

    lexer.py        lexical analyzer
    gui.py          graphical user interface
    main.py         starts the gui
    tests/          sample programs and unit tests

## status

lexical analyzer is done
syntax analyzer and semantic analyzer are not started yet