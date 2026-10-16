import re
import sys

# lexical analyzer for the lolcode interpreter
# work in progress - only the first set of lexemes is covered so far
# todo - operations, flow control, loops, functions, obtw and tldr

# keyword lexemes and their classification
KEYWORDS = {
    "HAI": "Code Delimiter",
    "KTHXBYE": "Code Delimiter",
    "WAZZUP": "Variable Declaration Delimiter",
    "BUHBYE": "Variable Declaration Delimiter",
    "I HAS A": "Variable Declaration",
    "ITZ": "Variable Assignment",
    "VISIBLE": "Output Keyword",
    "GIMMEH": "Input Keyword",
    "BTW": "Single Line Comment Delimiter",
}

# longest keywords are tried first so multi word keywords win over single words
SORTED_KEYWORDS = sorted(KEYWORDS, key=len, reverse=True)

# patterns from project requirement 1
NUMBR = re.compile(r"-?[0-9]+")
NUMBAR = re.compile(r"-?[0-9]+\.[0-9]+")
TROOF = re.compile(r"WIN|FAIL")
IDENTIFIER = re.compile(r"[a-zA-Z][a-zA-Z0-9_]*")


class Token:
    def __init__(self, lexeme, classification, line):
        self.lexeme = lexeme
        self.classification = classification
        self.line = line

    def __repr__(self):
        return f"Token({self.lexeme!r}, {self.classification!r}, line {self.line})"


def classify_word(word):
    # order matters since numbar must be checked before numbr
    if NUMBAR.fullmatch(word):
        return "Literal (NUMBAR)"
    if NUMBR.fullmatch(word):
        return "Literal (NUMBR)"
    if TROOF.fullmatch(word):
        return "Literal (TROOF)"
    if IDENTIFIER.fullmatch(word):
        return "Variable Identifier"
    return None


def match_keyword(line, pos):
    # a keyword only counts if it is followed by whitespace or the end of the line
    for keyword in SORTED_KEYWORDS:
        if line.startswith(keyword, pos):
            end = pos + len(keyword)
            if end == len(line) or line[end].isspace():
                return keyword
    return None


def tokenize_line(line, line_number):
    tokens = []
    errors = []
    pos = 0
    length = len(line)

    while pos < length:
        char = line[pos]

        # skip whitespace
        if char.isspace():
            pos += 1
            continue

        # yarn literal is scanned first so spaces and btw inside it are kept
        if char == '"':
            closing = line.find('"', pos + 1)
            if closing == -1:
                errors.append(f"line {line_number}: unterminated string literal")
                break
            tokens.append(Token('"', "String Delimiter", line_number))
            tokens.append(Token(line[pos + 1:closing], "Literal (YARN)", line_number))
            tokens.append(Token('"', "String Delimiter", line_number))
            pos = closing + 1
            continue

        # keywords
        keyword = match_keyword(line, pos)
        if keyword:
            tokens.append(Token(keyword, KEYWORDS[keyword], line_number))
            pos += len(keyword)
            # rest of the line after btw is a comment so it is ignored
            if keyword == "BTW":
                break
            continue

        # literals and identifiers
        end = pos
        while end < length and not line[end].isspace():
            end += 1
        word = line[pos:end]
        classification = classify_word(word)
        if classification:
            tokens.append(Token(word, classification, line_number))
        else:
            errors.append(f"line {line_number}: unknown lexeme '{word}'")
        pos = end

    return tokens, errors


def tokenize(source):
    all_tokens = []
    all_errors = []
    for number, line in enumerate(source.splitlines(), start=1):
        tokens, errors = tokenize_line(line, number)
        all_tokens.extend(tokens)
        all_errors.extend(errors)
    return all_tokens, all_errors


if __name__ == "__main__":
    # quick test from the terminal - python lexer.py tests/sample1.lol
    if len(sys.argv) != 2:
        print("usage: python lexer.py <file.lol>")
        sys.exit(1)

    with open(sys.argv[1], "r") as source_file:
        tokens, errors = tokenize(source_file.read())

    print(f"{'LEXEME':<20}{'CLASSIFICATION'}")
    for token in tokens:
        print(f"{token.lexeme:<20}{token.classification}")
    for error in errors:
        print("error:", error)
