import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext

from lexer import tokenize


class LolInterpreterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LOLCode Interpreter")
        self.root.geometry("1100x700")
        self.build_top_bar()
        self.build_main_panels()
        self.build_execute_button()
        self.build_console()

    # (1) file explorer
    def build_top_bar(self):
        bar = tk.Frame(self.root)
        bar.pack(fill="x", padx=5, pady=5)
        self.file_label = tk.Label(bar, text="(None)", anchor="w")
        self.file_label.pack(side="left", fill="x", expand=True)
        tk.Button(bar, text="Open File", command=self.open_file).pack(side="right")

    def build_main_panels(self):
        panels = tk.PanedWindow(self.root, orient="horizontal")
        panels.pack(fill="both", expand=True, padx=5)

        # (2) text editor
        self.editor = scrolledtext.ScrolledText(panels, width=40, undo=True)
        panels.add(self.editor)

        # (3) list of tokens
        self.token_table = self.make_table(panels, ("Lexeme", "Classification"))
        # (4) symbol table
        self.symbol_table = self.make_table(panels, ("Identifier", "Value"))

    def make_table(self, parent, columns):
        frame = tk.Frame(parent)
        table = ttk.Treeview(frame, columns=columns, show="headings")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        for column in columns:
            table.heading(column, text=column)
            table.column(column, width=150)
        table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        parent.add(frame)
        return table

    # (5) execute button
    def build_execute_button(self):
        tk.Button(self.root, text="EXECUTE", command=self.execute).pack(fill="x", padx=5, pady=5)

    # (6) console
    def build_console(self):
        self.console = scrolledtext.ScrolledText(self.root, height=10, state="disabled")
        self.console.pack(fill="x", padx=5, pady=(0, 5))

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("LOLCode files", "*.lol")])
        if not path:
            return
        with open(path, "r") as source_file:
            content = source_file.read()
        self.editor.delete("1.0", tk.END)
        self.editor.insert(tk.END, content)
        self.file_label.config(text=path)

    def write_console(self, text):
        self.console.config(state="normal")
        self.console.insert(tk.END, text + "\n")
        self.console.config(state="disabled")

    def clear_table(self, table):
        for row in table.get_children():
            table.delete(row)

    def execute(self):
        # refresh everything every time the button is pressed
        self.clear_table(self.token_table)
        self.clear_table(self.symbol_table)
        self.console.config(state="normal")
        self.console.delete("1.0", tk.END)
        self.console.config(state="disabled")

        source = self.editor.get("1.0", tk.END)
        tokens, errors = tokenize(source)

        for token in tokens:
            self.token_table.insert("", tk.END, values=(token.lexeme, token.classification))

        for error in errors:
            self.write_console("error: " + error)

        # syntax and semantic analysis are not done yet so the symbol table stays empty
        if not errors:
            self.write_console(f"lexical analysis done - {len(tokens)} tokens found")
