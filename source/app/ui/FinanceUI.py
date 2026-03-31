"""
Placeholder — Finance UI (Neha's module)
Will be replaced by Neha's FinanceUI when modules are integrated.
"""
import tkinter as tk


class FinanceUI(tk.Frame):
    def __init__(self, parent, user_data):
        super().__init__(parent, bg="#0f172a")
        self.pack(fill="both", expand=True)
        parent.title("PAMS — Finance")
        parent.geometry("1450x860")
        tk.Label(self, text="Finance Module (Neha)", bg="#0f172a", fg="white",
                 font=("Segoe UI", 18, "bold")).pack(expand=True)
