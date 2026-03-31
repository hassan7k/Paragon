"""
Placeholder — Maintenance UI (Rena's module)
Will be replaced by Rena's MaintenanceUI when modules are integrated.
"""
import tkinter as tk


class MaintenanceUI(tk.Frame):
    def __init__(self, parent, user_data):
        super().__init__(parent, bg="#0f172a")
        self.pack(fill="both", expand=True)
        parent.title("PAMS — Maintenance")
        parent.geometry("1450x860")
        tk.Label(self, text="Maintenance Module (Rena)", bg="#0f172a", fg="white",
                 font=("Segoe UI", 18, "bold")).pack(expand=True)
