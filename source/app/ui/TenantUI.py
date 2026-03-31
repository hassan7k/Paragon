"""
Placeholder — Tenant / Front-Desk UI (Michael's module)
Will be replaced by Miku's TenantUI when modules are integrated.
"""
import tkinter as tk


class TenantUI(tk.Frame):
    def __init__(self, parent, user_data):
        super().__init__(parent, bg="#0f172a")
        self.pack(fill="both", expand=True)
        parent.title("PAMS — Front Desk")
        parent.geometry("1100x700")
        tk.Label(self, text="Front Desk Module (Miku)", bg="#0f172a", fg="white",
                 font=("Segoe UI", 18, "bold")).pack(expand=True)
