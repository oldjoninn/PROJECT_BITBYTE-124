# parse_tree.py
# parse tree built by the syntax analyzer

import sys
from dataclasses import dataclass, field

from lexer import Token


@dataclass
class Node:
    kind: str
    children: list = field(default_factory=list)
    token: Token = None


def format_tree(node, depth=0):
    # plain ascii with two spaces per level so it prints on any terminal
    if node.token is None:
        label = f"<{node.kind}>"
    elif node.kind == "yarn":
        label = f'yarn: "{node.token.lexeme}"'
    elif node.kind == node.token.lexeme:
        label = node.kind
    else:
        label = f"{node.kind}: {node.token.lexeme}"

    lines = ["  " * depth + label]
    for child in node.children:
        lines.append(format_tree(child, depth + 1))
    return "\n".join(lines)


def print_tree(node):
    # if it cant print a special character, it will default into a backslash-escaped representation
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    print(format_tree(node).encode(encoding, "backslashreplace").decode(encoding))
