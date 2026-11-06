# syntax_analyzer.py
# syntax analyzer for the lolcode interpreter
# reads the tokens from the lexer ang checks them against grammar
# every grammar rule has its own parse method which is recursive descent
# the result is a parse tree, or the first syntax error with its line number

import sys

from keywords import (ARITHMETIC_OPERATORS, BINARY_BOOLEAN_OPERATORS, BLOCK_KEYWORDS,
                      COMMENT_CLASSES, COMPARISON_OPERATORS, FUNCTION,
                      INFINITE_BOOLEAN_OPERATORS, LITERAL_KINDS, LOOP, NAME_DESCRIPTIONS,
                      NOT_NESTABLE, TYPE, VARIABLE)
from lexer import tokenize
from parse_tree import Node, print_tree


class ParseError(Exception):
    def __init__(self, line, message):
        super().__init__(f"line {line}: {message}")
        self.line = line


# the main class that does the syntax analysis
class Parser:
    def __init__(self, tokens):
        self.tokens = [token for token in tokens if token.classification not in COMMENT_CLASSES]
        self.position = 0
        # used to check where FOUND YR and GTFO are allowed
        self.function_depth = 0
        self.gtfo_depth = 0
        # the keyword that starts a statement and the method that parses it
        self.statement_parsers = {
            "VISIBLE": self.parse_print,
            "GIMMEH": self.parse_input,
            "O RLY?": self.parse_ifelse,
            "WTF?": self.parse_switch,
            "IM IN YR": self.parse_loop,
            "HOW IZ I": self.parse_funcdef,
            "FOUND YR": self.parse_return,
            "GTFO": self.parse_gtfo,
        }

    # reading tokens

    def peek(self, offset=0):
        index = self.position + offset
        if index < len(self.tokens):
            return self.tokens[index]
        return None

    def peek_lexeme(self, offset=0):
        token = self.peek(offset)
        return token.lexeme if token else None

    def previous_line(self):
        if self.position > 0:
            return self.tokens[self.position - 1].line
        return 1

    def on_current_line(self):
        # true if the next token is on the same line as the last token read
        token = self.peek()
        return token is not None and self.position > 0 and token.line == self.previous_line()

    def fail(self, message):
        token = self.peek()
        line = token.line if token else self.previous_line()
        raise ParseError(line, message)

    def found(self):
        token = self.peek()
        return "end of file" if token is None else f"'{token.lexeme}'"

    def require_same_line(self, what):
        # the line ended before the token that was still needed
        if self.peek() is not None and not self.on_current_line():
            raise ParseError(self.previous_line(), f"expected {what} before end of line")

    def take(self, what, matches, same_line=True):
        # read one token that matches, or stop with a syntax error
        if same_line:
            self.require_same_line(what)
        token = self.peek()
        if token is None or not matches(token):
            self.fail(f"expected {what}, found {self.found()}")
        self.position += 1
        return token

    def keyword(self, lexeme, same_line=True):
        token = self.take(lexeme, lambda token: token.lexeme == lexeme, same_line)
        return Node(lexeme, token=token)

    def identifier(self, classification, kind, same_line=True):
        token = self.take(NAME_DESCRIPTIONS[kind],
                          lambda token: token.classification == classification, same_line)
        return Node(kind, token=token)

    def end_line(self):
        # every statement must end at the end of its line
        if self.on_current_line():
            self.fail(f"expected end of line, found {self.found()}")

    # program structure

    # <program> ::= <outside> HAI <linebreak> <declsection> <statements> KTHXBYE <linebreak> <outside>
    def parse_program(self):
        node = Node("program")
        node.children.extend(self.parse_outside())
        node.children.append(self.keyword("HAI", same_line=False))
        self.end_line()
        if self.peek_lexeme() == "WAZZUP":
            node.children.append(self.parse_declsection())
        node.children.append(self.parse_statements(("KTHXBYE",)))
        node.children.append(self.keyword("KTHXBYE", same_line=False))
        self.end_line()
        node.children.extend(self.parse_outside())
        if self.peek() is not None:
            self.fail(f"only function definitions may come after KTHXBYE, found {self.found()}")
        return node

    # <outside> ::= <funcdef> <linebreak> <outside> | ε
    def parse_outside(self):
        functions = []
        while self.peek_lexeme() == "HOW IZ I":
            functions.append(self.parse_funcdef())
            self.end_line()
        return functions

    # <declsection> ::= WAZZUP <linebreak> <declarations> BUHBYE <linebreak>
    def parse_declsection(self):
        node = Node("declsection", [self.keyword("WAZZUP", same_line=False)])
        self.end_line()
        while self.peek() is not None and self.peek_lexeme() != "BUHBYE":
            if self.peek_lexeme() != "I HAS A":
                self.fail(f"expected I HAS A or BUHBYE, found {self.found()}")
            node.children.append(self.parse_vardecl())
            self.end_line()
        node.children.append(self.keyword("BUHBYE", same_line=False))
        self.end_line()
        return node

    # <vardecl> ::= I HAS A varident | I HAS A varident ITZ <operand>
    def parse_vardecl(self):
        node = Node("vardecl", [self.keyword("I HAS A", same_line=False),
                                self.identifier(VARIABLE, "varident")])
        if self.on_current_line() and self.peek_lexeme() == "ITZ":
            node.children.append(self.keyword("ITZ"))
            node.children.append(self.parse_operand())
        return node

    # <statements> ::= <statement> <linebreak> <statements> | ε
    # the statements stop at one of the keywords that closes the block
    def parse_statements(self, closing_keywords):
        node = Node("statements")
        while self.peek() is not None and self.peek_lexeme() not in closing_keywords:
            if self.peek_lexeme() == "WAZZUP":
                self.fail("WAZZUP must come right after HAI")
            if self.peek_lexeme() in BLOCK_KEYWORDS:
                self.fail(f"expected {' or '.join(closing_keywords)}, found {self.found()}")
            node.children.append(self.parse_statement())
            self.end_line()
        return node

    # <statement> ::= <print> | <input> | <assign> | <typecast> | <ifelse> | <switch>
    #               | <loop> | <funcdef> | <return> | <operand> | GTFO
    def parse_statement(self):
        lexeme = self.peek_lexeme()
        if lexeme in self.statement_parsers:
            return self.statement_parsers[lexeme]()
        if lexeme == "I HAS A":
            self.fail("variables must be declared between WAZZUP and BUHBYE")

        # a variable followed by R or IS NOW A on the same line
        token = self.peek()
        following = self.peek(1)
        if token.classification == VARIABLE and following is not None and following.line == token.line:
            if following.lexeme == "R":
                return self.parse_assign()
            if following.lexeme == "IS NOW A":
                return self.parse_typecast()

        # anything else must be an expression, its value goes to IT
        return Node("expression", [self.parse_operand(first_on_line=True)])

    # simple statements

    # <print> ::= VISIBLE <printargs> | VISIBLE <printargs> !
    # <printargs> ::= <operand> + <printargs> | <operand> <printargs> | <operand>
    def parse_print(self):
        node = Node("print", [self.keyword("VISIBLE", same_line=False), self.parse_operand()])
        while self.on_current_line() and self.peek_lexeme() != "!":
            if self.peek_lexeme() == "+":
                self.position += 1
            node.children.append(self.parse_operand())
        if self.on_current_line():
            node.children.append(self.keyword("!"))
        return node

    # <input> ::= GIMMEH varident
    def parse_input(self):
        return Node("input", [self.keyword("GIMMEH", same_line=False),
                              self.identifier(VARIABLE, "varident")])

    # <assign> ::= varident R <operand>
    def parse_assign(self):
        return Node("assign", [self.identifier(VARIABLE, "varident", same_line=False),
                               self.keyword("R"), self.parse_operand()])

    # <typecast> ::= varident IS NOW A type
    def parse_typecast(self):
        return Node("typecast", [self.identifier(VARIABLE, "varident", same_line=False),
                                 self.keyword("IS NOW A"), self.identifier(TYPE, "type")])

    # <return> ::= FOUND YR <operand>
    def parse_return(self):
        if self.function_depth == 0:
            self.fail("FOUND YR is only allowed inside a function")
        return Node("return", [self.keyword("FOUND YR", same_line=False), self.parse_operand()])

    def parse_gtfo(self):
        if self.gtfo_depth == 0:
            self.fail("GTFO is only allowed inside a loop, a switch or a function")
        return self.keyword("GTFO", same_line=False)

    # operands and expressions

    # <operand> ::= varident | <expr> | <literal>
    # <inneroperand> ::= varident | <innerexpr> | <literal>
    # nested is true for an operand inside another operation
    # first_on_line is true when the operand is a whole statement by itself
    def parse_operand(self, nested=False, first_on_line=False):
        if not first_on_line:
            self.require_same_line("an operand")
        token = self.peek()
        if token is None:
            self.fail("expected an operand, found end of file")

        lexeme = token.lexeme
        if nested and lexeme in NOT_NESTABLE:
            self.fail(f"{lexeme} cannot be nested inside another operation")

        if lexeme in ARITHMETIC_OPERATORS:
            return self.parse_binary("arith")
        if lexeme in BINARY_BOOLEAN_OPERATORS:
            return self.parse_binary("bool")
        if lexeme in COMPARISON_OPERATORS:
            return self.parse_binary("comp")
        if lexeme == "NOT":
            return Node("bool", [self.take_operator(), self.parse_operand(nested=True)])
        if lexeme in INFINITE_BOOLEAN_OPERATORS:
            return self.parse_infinite_bool()
        if lexeme == "SMOOSH":
            return Node("concat", [self.take_operator()] + self.parse_operandlist())
        if lexeme == "MAEK":
            return self.parse_cast()
        if lexeme == "I IZ":
            return self.parse_call()
        if lexeme == '"' or token.classification in LITERAL_KINDS:
            return self.parse_literal(same_line=not first_on_line)
        if token.classification == VARIABLE:
            self.position += 1
            return Node("varident", token=token)
        expected = "a statement" if first_on_line else "an operand"
        self.fail(f"expected {expected}, found {self.found()}")

    def take_operator(self):
        # the operator was already checked by parse_operand
        token = self.peek()
        self.position += 1
        return Node(token.lexeme, token=token)

    # <arith>, <bool> and <comp> with two operands: OPERATOR <inneroperand> AN <inneroperand>
    def parse_binary(self, kind):
        operator = self.take_operator()
        first = self.parse_operand(nested=True)
        self.keyword("AN")
        second = self.parse_operand(nested=True)
        return Node(kind, [operator, first, second])

    # <infbool> ::= ANY OF <operandlist> MKAY | ALL OF <operandlist> MKAY
    def parse_infinite_bool(self):
        node = Node("infbool", [self.take_operator()] + self.parse_operandlist())
        node.children.append(self.keyword("MKAY"))
        return node

    # <operandlist> ::= <inneroperand> AN <operandlist> | <inneroperand>
    def parse_operandlist(self):
        operands = [self.parse_operand(nested=True)]
        while self.on_current_line() and self.peek_lexeme() == "AN":
            # AN YR on the same line belongs to a function call around this list
            following = self.peek(1)
            if following is not None and following.lexeme == "YR" and following.line == self.peek().line:
                break
            self.position += 1
            operands.append(self.parse_operand(nested=True))
        return operands

    # <cast> ::= MAEK <inneroperand> A type | MAEK <inneroperand> type
    def parse_cast(self):
        node = Node("cast", [self.take_operator(), self.parse_operand(nested=True)])
        if self.on_current_line() and self.peek_lexeme() == "A":
            self.position += 1
        node.children.append(self.identifier(TYPE, "type"))
        return node

    # <call> ::= I IZ funcident <args> MKAY
    # <args> ::= YR <operand> <moreargs> | ε
    # <moreargs> ::= AN YR <operand> <moreargs> | ε
    def parse_call(self):
        node = Node("call", [self.take_operator(), self.identifier(FUNCTION, "funcident")])
        if self.on_current_line() and self.peek_lexeme() == "YR":
            self.position += 1
            node.children.append(self.parse_operand())
            while self.on_current_line() and self.peek_lexeme() == "AN":
                self.position += 1
                self.keyword("YR")
                node.children.append(self.parse_operand())
        node.children.append(self.keyword("MKAY"))
        return node

    # <literal> ::= numbr | numbar | yarn | troof
    def parse_literal(self, same_line=True):
        if self.peek_lexeme() == '"':
            # the lexer gives a yarn as three tokens: " text "
            self.keyword('"', same_line)
            text = self.take("yarn", lambda token: token.classification == "Literal (YARN)")
            self.keyword('"')
            return Node("yarn", token=text)
        literal = self.take("a literal", lambda token: token.classification in LITERAL_KINDS,
                            same_line)
        return Node(LITERAL_KINDS[literal.classification], token=literal)

    # flow control

    # <ifelse> ::= O RLY? <linebreak> YA RLY <linebreak> <statements> <mebbelist> <nowai> OIC
    def parse_ifelse(self):
        branch_ends = ("MEBBE", "NO WAI", "OIC")
        node = Node("ifelse", [self.keyword("O RLY?", same_line=False)])
        self.end_line()
        node.children.append(self.keyword("YA RLY", same_line=False))
        self.end_line()
        node.children.append(self.parse_statements(branch_ends))

        # <mebbelist> ::= MEBBE <operand> <linebreak> <statements> <mebbelist> | ε
        while self.peek_lexeme() == "MEBBE":
            mebbe = Node("mebbe", [self.keyword("MEBBE", same_line=False), self.parse_operand()])
            self.end_line()
            mebbe.children.append(self.parse_statements(branch_ends))
            node.children.append(mebbe)

        # <nowai> ::= NO WAI <linebreak> <statements> | ε
        if self.peek_lexeme() == "NO WAI":
            nowai = Node("nowai", [self.keyword("NO WAI", same_line=False)])
            self.end_line()
            nowai.children.append(self.parse_statements(("OIC",)))
            node.children.append(nowai)

        node.children.append(self.keyword("OIC", same_line=False))
        return node

    # <switch> ::= WTF? <linebreak> <cases> <default> OIC
    def parse_switch(self):
        case_ends = ("OMG", "OMGWTF", "OIC")
        node = Node("switch", [self.keyword("WTF?", same_line=False)])
        self.end_line()
        self.gtfo_depth += 1

        # <cases> ::= <case> <cases> | <case>
        # <case> ::= OMG <literal> <linebreak> <statements>
        if self.peek_lexeme() != "OMG":
            self.fail(f"expected OMG, found {self.found()}")
        while self.peek_lexeme() == "OMG":
            case = Node("case", [self.keyword("OMG", same_line=False), self.parse_literal()])
            self.end_line()
            case.children.append(self.parse_statements(case_ends))
            node.children.append(case)

        # <default> ::= OMGWTF <linebreak> <statements> | ε
        if self.peek_lexeme() == "OMGWTF":
            default = Node("default", [self.keyword("OMGWTF", same_line=False)])
            self.end_line()
            default.children.append(self.parse_statements(("OIC",)))
            node.children.append(default)

        self.gtfo_depth -= 1
        node.children.append(self.keyword("OIC", same_line=False))
        return node

    # <loop> ::= IM IN YR loopident <loopctl> <linebreak> <statements> IM OUTTA YR loopident
    # <loopctl> ::= <loopop> YR varident <loopcond>
    def parse_loop(self):
        node = Node("loop", [self.keyword("IM IN YR", same_line=False)])
        label = self.identifier(LOOP, "loopident")
        node.children.append(label)

        operation = self.take("UPPIN or NERFIN", lambda token: token.lexeme in {"UPPIN", "NERFIN"})
        node.children.append(Node(operation.lexeme, token=operation))
        self.keyword("YR")
        node.children.append(self.identifier(VARIABLE, "varident"))

        # <loopcond> ::= TIL <operand> | WILE <operand> | ε
        if self.on_current_line() and self.peek_lexeme() in {"TIL", "WILE"}:
            node.children.append(self.take_operator())
            node.children.append(self.parse_operand())
        self.end_line()

        self.gtfo_depth += 1
        node.children.append(self.parse_statements(("IM OUTTA YR",)))
        self.gtfo_depth -= 1

        node.children.append(self.keyword("IM OUTTA YR", same_line=False))
        end_label = self.identifier(LOOP, "loopident")
        if end_label.token.lexeme != label.token.lexeme:
            raise ParseError(end_label.token.line,
                             f"loop {label.token.lexeme} is closed with {end_label.token.lexeme}")
        node.children.append(end_label)
        return node

    # <funcdef> ::= HOW IZ I funcident <params> <linebreak> <statements> IF U SAY SO
    # <params> ::= YR varident <moreparams> | ε
    # <moreparams> ::= AN YR varident <moreparams> | ε
    def parse_funcdef(self):
        node = Node("funcdef", [self.keyword("HOW IZ I", same_line=False),
                                self.identifier(FUNCTION, "funcident")])
        if self.on_current_line() and self.peek_lexeme() == "YR":
            self.position += 1
            node.children.append(self.identifier(VARIABLE, "param"))
            while self.on_current_line() and self.peek_lexeme() == "AN":
                self.position += 1
                self.keyword("YR")
                node.children.append(self.identifier(VARIABLE, "param"))
        self.end_line()

        self.function_depth += 1
        self.gtfo_depth += 1
        node.children.append(self.parse_statements(("IF U SAY SO",)))
        self.function_depth -= 1
        self.gtfo_depth -= 1

        node.children.append(self.keyword("IF U SAY SO", same_line=False))
        return node


# the main function for other files to use
def parse(tokens):
    # returns the parse tree and a list of errors
    # the parser stops at the first syntax error so the list has at most one error
    try:
        return Parser(tokens).parse_program(), []
    except ParseError as error:
        return None, [str(error)]


# the main function for testing from the terminal
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python syntax_analyzer.py <file.lol>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as source_file:
        tokens, errors = tokenize(source_file.read())

    if not errors:
        tree, errors = parse(tokens)

    for error in errors:
        print("error:", error)
    if errors:
        sys.exit(1)

    print_tree(tree)
