# lexer.py
# lexical analyzer for the lolcode interpreter
# it reads the source code and turns it into a list of tokens
# every token has a lexeme a classification and a line number
# anything that is not a valid lexeme is reported in the error list
#
# how to use it from other files
#     tokens, errors = tokenize(source_code)
#
# how to test it from the terminal
#     python lexer.py tests/sample1.lol

import re
import sys
from dataclasses import dataclass


# every keyword from project requirement 1 and the lexemes added in requirement 2
# each keyword is paired with its classification shown in the token list
KEYWORDS = {
    # program structure
    "HAI": "Code Delimiter",
    "KTHXBYE": "Code Delimiter",
    "WAZZUP": "Variable Declaration Delimiter",
    "BUHBYE": "Variable Declaration Delimiter",

    # comments
    "BTW": "Single Line Comment Delimiter",
    "OBTW": "Multi Line Comment Delimiter",
    "TLDR": "Multi Line Comment Delimiter",

    # variables and assignment
    "I HAS A": "Variable Declaration",
    "ITZ": "Variable Initialization",
    "R": "Assignment Keyword",

    # arithmetic operations
    "SUM OF": "Arithmetic Operator",
    "DIFF OF": "Arithmetic Operator",
    "PRODUKT OF": "Arithmetic Operator",
    "QUOSHUNT OF": "Arithmetic Operator",
    "MOD OF": "Arithmetic Operator",
    "BIGGR OF": "Arithmetic Operator",
    "SMALLR OF": "Arithmetic Operator",

    # boolean operations
    "BOTH OF": "Boolean Operator",
    "EITHER OF": "Boolean Operator",
    "WON OF": "Boolean Operator",
    "NOT": "Boolean Operator",
    "ANY OF": "Boolean Operator",
    "ALL OF": "Boolean Operator",

    # comparison operations
    "BOTH SAEM": "Comparison Operator",
    "DIFFRINT": "Comparison Operator",

    # string concatenation
    "SMOOSH": "Concatenation Operator",

    # typecasting
    "MAEK": "Typecast Operator",
    "A": "Typecast Keyword",
    "IS NOW A": "Typecast Operator",

    # input and output
    "VISIBLE": "Output Keyword",
    "GIMMEH": "Input Keyword",
    "!": "Newline Suppressor",
    "+": "Output Separator",

    # if else statements
    "O RLY?": "If Else Delimiter",
    "YA RLY": "If Clause Delimiter",
    "MEBBE": "Else If Clause Delimiter",
    "NO WAI": "Else Clause Delimiter",
    "OIC": "Flow Control Delimiter",

    # switch case statements
    "WTF?": "Switch Delimiter",
    "OMG": "Case Keyword",
    "OMGWTF": "Default Case Keyword",
    "GTFO": "Break Keyword",

    # loops
    "IM IN YR": "Loop Delimiter",
    "IM OUTTA YR": "Loop Delimiter",
    "UPPIN": "Loop Operation",
    "NERFIN": "Loop Operation",
    "TIL": "Loop Condition",
    "WILE": "Loop Condition",

    # functions
    "HOW IZ I": "Function Delimiter",
    "IF U SAY SO": "Function Delimiter",
    "FOUND YR": "Return Keyword",
    "I IZ": "Function Call Keyword",
    "MKAY": "Argument List Delimiter",

    # shared by loops and functions
    "YR": "Parameter Marker",
    "AN": "Operand Separator",
}

# longest keywords are tried first so a multi word keyword wins over a shorter one
SORTED_KEYWORDS = sorted(KEYWORDS, key=len, reverse=True)

# keywords made of symbols may touch the lexeme before or after them
SYMBOL_KEYWORDS = {"!", "+"}

# a word stops at whitespace or at one of these characters
WORD_ENDERS = '"!+'

# literal patterns from project requirement 1
NUMBR_PATTERN = re.compile(r"-?[0-9]+")
NUMBAR_PATTERN = re.compile(r"-?[0-9]+\.[0-9]+")
IDENTIFIER_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9_]*")
TROOF_VALUES = {"WIN", "FAIL"}
TYPE_NAMES = {"NOOB", "NUMBR", "NUMBAR", "YARN", "TROOF"}

# the keyword before an identifier tells what kind of identifier it is
IDENTIFIER_KINDS = {
    "HOW IZ I": "Function Identifier",
    "I IZ": "Function Identifier",
    "IM IN YR": "Loop Identifier",
    "IM OUTTA YR": "Loop Identifier",
}
# the default kind is a variable identifier
DEFAULT_IDENTIFIER_KIND = "Variable Identifier"


@dataclass
class Token:
    lexeme: str
    classification: str
    line: int


# small helper functions

def is_word_end(character):
    return character.isspace() or character in WORD_ENDERS


def keyword_ends_cleanly(line, end):
    # a keyword must be followed by whitespace or the end of the line
    # this stops the keyword R from matching the start of a name like result
    return end == len(line) or line[end].isspace()


def find_keyword(line, position):
    # return the keyword that starts at this position or none
    for keyword in SORTED_KEYWORDS:
        if not line.startswith(keyword, position):
            continue
        if keyword in SYMBOL_KEYWORDS:
            return keyword
        if keyword_ends_cleanly(line, position + len(keyword)):
            return keyword
    return None


class Lexer:
    def __init__(self, source):
        self.lines = source.splitlines()
        self.tokens = []
        self.errors = []
        self.in_multiline_comment = False
        self.multiline_comment_start = 0

    # main loop

    def tokenize(self):
        for line_number, line in enumerate(self.lines, start=1):
            if self.in_multiline_comment:
                self.scan_comment_line(line, line_number)
            else:
                self.scan_line(line, line_number)

        if self.in_multiline_comment:
            self.add_error(self.multiline_comment_start, "obtw has no matching tldr")

        return self.tokens, self.errors

    # recording results

    def add_token(self, lexeme, classification, line_number):
        self.tokens.append(Token(lexeme, classification, line_number))

    def add_error(self, line_number, message):
        self.errors.append(f"line {line_number}: {message}")

    def previous_token_on_line(self, line_number):
        # return the last token only if it is on the given line
        if self.tokens and self.tokens[-1].line == line_number:
            return self.tokens[-1]
        return None

    # scanning a normal line
    # each scan method returns the position where scanning continues
    # returning the length of the line means the rest of the line is skipped

    # scan a line of code
    def scan_line(self, line, line_number):
        position = 0
        while position < len(line):
            character = line[position]

            if character.isspace():
                position += 1
            elif character == '"':
                position = self.scan_string(line, position, line_number)
            else:
                position = self.scan_keyword_or_word(line, position, line_number)

    # scan a string literal
    def scan_string(self, line, position, line_number):
        closing_quote = line.find('"', position + 1)

        if closing_quote == -1:
            self.add_error(line_number, "string is missing its closing quote")
            return len(line)

        text = line[position + 1:closing_quote]
        self.add_token('"', "String Delimiter", line_number)
        self.add_token(text, "Literal (YARN)", line_number)
        self.add_token('"', "String Delimiter", line_number)
        return closing_quote + 1

    # scan a keyword or a word
    def scan_keyword_or_word(self, line, position, line_number):
        keyword = find_keyword(line, position)
        if keyword is None:
            return self.scan_word(line, position, line_number)
        return self.scan_keyword(keyword, line, position, line_number)

    # scan a keyword
    def scan_keyword(self, keyword, line, position, line_number):
        end = position + len(keyword)

        if keyword == "BTW":
            self.add_token(keyword, KEYWORDS[keyword], line_number)
            return len(line)

        if keyword == "OBTW":
            return self.start_multiline_comment(line, line_number)

        if keyword == "TLDR":
            self.add_error(line_number, "tldr has no matching obtw")
            return end

        self.add_token(keyword, KEYWORDS[keyword], line_number)
        return end

    # scan a word
    def scan_word(self, line, position, line_number):
        end = position
        while end < len(line) and not is_word_end(line[end]):
            end += 1

        word = line[position:end]
        classification = self.classify_word(word, line_number)

        if classification is None:
            self.add_error(line_number, f"unknown lexeme {word}")
        else:
            self.add_token(word, classification, line_number)

        return end

    # classify a word using regexes and the previous token on the same line
    def classify_word(self, word, line_number):
        # numbar is checked before numbr so a decimal is never split
        if NUMBAR_PATTERN.fullmatch(word):
            return "Literal (NUMBAR)"
        if NUMBR_PATTERN.fullmatch(word):
            return "Literal (NUMBR)"
        if word in TROOF_VALUES:
            return "Literal (TROOF)"
        if word in TYPE_NAMES:
            return "Literal (TYPE)"
        if IDENTIFIER_PATTERN.fullmatch(word):
            return self.identifier_kind(line_number)
        return None

    # determine the kind of identifier based on the previous token on the same line
    def identifier_kind(self, line_number):
        previous = self.previous_token_on_line(line_number)
        if previous is None:
            return DEFAULT_IDENTIFIER_KIND
        return IDENTIFIER_KINDS.get(previous.lexeme, DEFAULT_IDENTIFIER_KIND)

    # multi line comments

    # start a multi-line comment
    def start_multiline_comment(self, line, line_number):
        # obtw must be the first lexeme on its line
        if self.previous_token_on_line(line_number) is not None:
            self.add_error(line_number, "obtw must be alone on its line")
            return len(line)

        self.add_token("OBTW", KEYWORDS["OBTW"], line_number)
        self.in_multiline_comment = True
        self.multiline_comment_start = line_number
        return len(line)

    # scan a line inside a multi-line comment
    def scan_comment_line(self, line, line_number):
        # every line inside the comment is ignored until a line starts with tldr
        words = line.split()
        if not words or words[0] != "TLDR":
            return

        self.add_token("TLDR", KEYWORDS["TLDR"], line_number)
        self.in_multiline_comment = False

        # only a btw comment may follow tldr on the same line
        leftover = words[1:]
        if leftover and leftover[0] != "BTW":
            self.add_error(line_number, "tldr must be alone on its line")

# the main function for other files to use
def tokenize(source):
    # returns a list of tokens and a list of error messages
    return Lexer(source).tokenize()


# the main function for testing from the terminal
if __name__ == "__main__":
    # check that the user provided a file name
    if len(sys.argv) != 2:
        print("usage: python lexer.py <file.lol>")
        sys.exit(1)
    # read the source code from the file and tokenize it
    with open(sys.argv[1], "r") as source_file:
        tokens, errors = tokenize(source_file.read())

    # print the results in a table format
    print(f"{'LINE':<6}{'LEXEME':<20}CLASSIFICATION")
    for token in tokens:
        print(f"{token.line:<6}{token.lexeme:<20}{token.classification}")

    for error in errors:
        print("error:", error)