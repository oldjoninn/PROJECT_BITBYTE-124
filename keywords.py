# keywords.py
# groups of keywords and token classifications used by the syntax analyzer


# comments are ignored by the parser, the lexer already checked where they are
COMMENT_CLASSES = {"Single Line Comment Delimiter", "Multi Line Comment Delimiter"}

ARITHMETIC_OPERATORS = {"SUM OF", "DIFF OF", "PRODUKT OF", "QUOSHUNT OF",
                        "MOD OF", "BIGGR OF", "SMALLR OF"}
BINARY_BOOLEAN_OPERATORS = {"BOTH OF", "EITHER OF", "WON OF"}
INFINITE_BOOLEAN_OPERATORS = {"ANY OF", "ALL OF"}
COMPARISON_OPERATORS = {"BOTH SAEM", "DIFFRINT"}

# these may not be nested inside another operation (spec p.3 and p.4)
NOT_NESTABLE = INFINITE_BOOLEAN_OPERATORS | {"SMOOSH"}

# literal classifications and the name used for them in the parse tree
LITERAL_KINDS = {
    "Literal (NUMBR)": "numbr",
    "Literal (NUMBAR)": "numbar",
    "Literal (TROOF)": "troof",
}

VARIABLE = "Variable Identifier"
FUNCTION = "Function Identifier"
LOOP = "Loop Identifier"
TYPE = "Literal (TYPE)"

# how each kind of name is described in error messages
NAME_DESCRIPTIONS = {
    "varident": "a variable",
    "param": "a parameter name",
    "funcident": "a function name",
    "loopident": "a loop name",
    "type": "a type",
}

# keywords that open or close a block, so they can never start a statement
BLOCK_KEYWORDS = {"HAI", "KTHXBYE", "WAZZUP", "BUHBYE", "YA RLY", "MEBBE", "NO WAI", "OIC",
                  "OMG", "OMGWTF", "IM OUTTA YR", "IF U SAY SO"}
