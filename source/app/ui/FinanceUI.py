import tkinter as tk

class FinanceUI:
    def __init__(self, parent, user):
        window = tk.Toplevel(parent)
        window.title("Finance UI")
        window.geometry("600x400")

        tk.Label(window, text="Finance UI (Placeholder)").pack(pady=50)