# gui.py
# graphical user interface for the lolcode interpreter in dark mode
#
# parts of the window
#     file explorer button on the top
#     text editor on the left
#     list of tokens in the middle
#     symbol table and parse tree in tabs on the right
#     execute button below the panels
#     console at the bottom

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext

from lexer import tokenize
from parse_tree import node_label
from syntax_analyzer import parse


# dark mode colors
BACKGROUND = "#1e1e1e"
PANEL = "#252526"
TEXT = "#d4d4d4"
BUTTON = "#3c3c3c"
SELECTION = "#264f78"
ERROR = "#f48771"


class LolInterpreterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LOLCode Interpreter")
        self.root.geometry("1100x700")
        self.root.configure(bg=BACKGROUND)

        self.apply_dark_theme()
        self.build_file_explorer()
        self.build_panels()
        self.build_execute_button()
        self.build_console()

    # building the window

    def apply_dark_theme(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Treeview", background=PANEL, fieldbackground=PANEL,
                        foreground=TEXT, borderwidth=0)
        style.map("Treeview", background=[("selected", SELECTION)])
        style.configure("Treeview.Heading", background=BUTTON, foreground=TEXT,
                        borderwidth=0)

        style.configure("Vertical.TScrollbar", background=BUTTON,
                        troughcolor=BACKGROUND, bordercolor=BACKGROUND)

        style.configure("TButton", background=BUTTON, foreground=TEXT,
                        borderwidth=0, padding=6)
        style.map("TButton", background=[("active", SELECTION)])

    def build_file_explorer(self):
        bar = tk.Frame(self.root, bg=BACKGROUND)
        bar.pack(fill="x", padx=5, pady=5)

        self.file_label = tk.Label(bar, text="(None)", anchor="w",
                                   bg=BACKGROUND, fg=TEXT)
        self.file_label.pack(side="left", fill="x", expand=True)

        ttk.Button(bar, text="Open File", command=self.open_file).pack(side="right")

    def build_panels(self):
        panels = tk.PanedWindow(self.root, orient="horizontal", bg=BACKGROUND)
        panels.pack(fill="both", expand=True, padx=5)

        # insertbackground is the color of the typing cursor
        self.editor = scrolledtext.ScrolledText(panels, width=40, undo=True,
                                                bg=PANEL, fg=TEXT,
                                                insertbackground=TEXT)
        panels.add(self.editor)

        self.token_table = self.make_table(panels, ("Lexeme", "Classification"))
        panels.add(self.token_table.master)

        # the right side has one tab for the symbol table and one for the parse tree
        self.right_tabs = ttk.Notebook(panels)
        self.symbol_table = self.make_table(self.right_tabs, ("Identifier", "Value"))
        self.right_tabs.add(self.symbol_table.master, text="Symbol Table")

        # show="tree" gives the collapsible tree look instead of column headings
        self.parse_tree_view = self.make_table(self.right_tabs, (), show="tree")
        self.parse_tree_view.column("#0", width=300)
        self.right_tabs.add(self.parse_tree_view.master, text="Parse Tree")
        panels.add(self.right_tabs)

    def make_table(self, parent, columns, show="headings"):
        frame = tk.Frame(parent, bg=BACKGROUND)
        table = ttk.Treeview(frame, columns=columns, show=show)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)

        for column in columns:
            table.heading(column, text=column)
            table.column(column, width=150)

        table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return table

    def build_execute_button(self):
        ttk.Button(self.root, text="EXECUTE", command=self.execute).pack(fill="x", padx=5, pady=5)

    def build_console(self):
        self.console = scrolledtext.ScrolledText(self.root, height=10, state="disabled",
                                                 bg=PANEL, fg=TEXT)
        self.console.tag_config("error", foreground=ERROR)
        self.console.pack(fill="x", padx=5, pady=(0, 5))

    # button actions

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("LOLCode files", "*.lol")])
        if not path:
            return

        with open(path, "r") as source_file:
            content = source_file.read()

        self.editor.delete("1.0", tk.END)
        self.editor.insert(tk.END, content)
        self.file_label.config(text=path)

    def execute(self):
        # everything is refreshed every time the button is pressed
        # the symbol table stays empty until the semantic analyzer is done
        self.clear_table(self.token_table)
        self.clear_table(self.symbol_table)
        self.clear_table(self.parse_tree_view)
        self.clear_console()

        source = self.editor.get("1.0", tk.END)
        tokens, errors = tokenize(source)

        for token in tokens:
            self.token_table.insert("", tk.END, values=(token.lexeme, token.classification))

        for error in errors:
            self.write_console("error: " + error, "error")
        if errors:
            return
        self.write_console(f"lexical analysis done with {len(tokens)} tokens")

        # the parser only runs when there are no lexical errors
        tree, errors = parse(tokens)
        for error in errors:
            self.write_console("syntax error: " + error, "error")
        if errors:
            return
        self.write_console("syntax analysis done")
        self.show_tree(tree)
        self.right_tabs.select(self.parse_tree_view.master)

    # small helpers

    def show_tree(self, node, parent=""):
        # each node becomes a row under its parent and every row starts expanded
        row = self.parse_tree_view.insert(parent, tk.END, text=node_label(node), open=True)
        for child in node.children:
            self.show_tree(child, row)

    def clear_table(self, table):
        for row in table.get_children():
            table.delete(row)

    def clear_console(self):
        self.console.config(state="normal")
        self.console.delete("1.0", tk.END)
        self.console.config(state="disabled")

    def write_console(self, text, tag=None):
        self.console.config(state="normal")
        self.console.insert(tk.END, text + "\n", tag)
        self.console.config(state="disabled")