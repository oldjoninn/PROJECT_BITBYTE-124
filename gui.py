# gui.py
# graphical user interface for the lolcode interpreter
#
# parts of the window
#     file explorer button on the top
#     text editor on the left
#     list of tokens in the middle
#     symbol table on the right
#     execute button below the panels
#     console at the bottom

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext

from lexer import tokenize


class LolInterpreterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LOLCode Interpreter")
        self.root.geometry("1100x700")

        self.build_file_explorer()
        self.build_panels()
        self.build_execute_button()
        self.build_console()

    # building the window

    def build_file_explorer(self):
        bar = tk.Frame(self.root)
        bar.pack(fill="x", padx=5, pady=5)

        self.file_label = tk.Label(bar, text="(None)", anchor="w")
        self.file_label.pack(side="left", fill="x", expand=True)

        tk.Button(bar, text="Open File", command=self.open_file).pack(side="right")

    def build_panels(self):
        panels = tk.PanedWindow(self.root, orient="horizontal")
        panels.pack(fill="both", expand=True, padx=5)

        self.editor = scrolledtext.ScrolledText(panels, width=40, undo=True)
        panels.add(self.editor)

        self.token_table = self.make_table(panels, ("Lexeme", "Classification"))
        self.symbol_table = self.make_table(panels, ("Identifier", "Value"))

    def make_table(self, panels, columns):
        frame = tk.Frame(panels)
        table = ttk.Treeview(frame, columns=columns, show="headings")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)

        for column in columns:
            table.heading(column, text=column)
            table.column(column, width=150)

        table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        panels.add(frame)
        return table

    def build_execute_button(self):
        tk.Button(self.root, text="EXECUTE", command=self.execute).pack(fill="x", padx=5, pady=5)

    def build_console(self):
        self.console = scrolledtext.ScrolledText(self.root, height=10, state="disabled")
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
        self.clear_table(self.token_table)
        self.clear_table(self.symbol_table)
        self.clear_console()

        source = self.editor.get("1.0", tk.END)
        tokens, errors = tokenize(source)

        for token in tokens:
            self.token_table.insert("", tk.END, values=(token.lexeme, token.classification))

        for error in errors:
            self.write_console("error: " + error)

        # the symbol table stays empty until the semantic analyzer is done
        if not errors:
            self.write_console(f"lexical analysis done with {len(tokens)} tokens")

    # small helpers

    def clear_table(self, table):
        for row in table.get_children():
            table.delete(row)

    def clear_console(self):
        self.console.config(state="normal")
        self.console.delete("1.0", tk.END)
        self.console.config(state="disabled")

    def write_console(self, text):
        self.console.config(state="normal")
        self.console.insert(tk.END, text + "\n")
        self.console.config(state="disabled")