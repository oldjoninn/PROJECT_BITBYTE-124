import tkinter as tk

from gui import LolInterpreterGUI


def main():
    root = tk.Tk()
    LolInterpreterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
