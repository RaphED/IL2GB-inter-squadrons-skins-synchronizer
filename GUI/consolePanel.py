import tkinter as tk

class ConsolePanel:

    def __init__(self, root: tk):

        self.root = root

        self.text_widget = tk.Text(self.root, wrap="word", height=15, width=50)
        self.text_widget.pack(expand=True, fill="both")
        

    def addLine(self, text):
        self.text_widget.config(state=tk.NORMAL)  # Disable editing
        self.text_widget.insert(tk.END, text + "\n")  # Insert text
        self.text_widget.yview(tk.END)  # Auto-scroll to the end
        self.text_widget.config(state=tk.DISABLED)  # Disable editing again