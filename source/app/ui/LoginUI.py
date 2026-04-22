import tkinter as tk
from tkinter import messagebox
from source.app.controllers.Auth import AuthController
from source.app.ui.AdminUI import AdminUI
from source.app.ui.MaintenanceUI import MaintenanceUI
from source.app.ui.FinanceUI import FinanceUI
from source.app.ui.TenantUI import TenantUI
from source.app.databases.database import Get_Connection

BG = "#0f172a"
CARD = "#1e293b"
FG = "#e2e8f0"
MUTED = "#94a3b8"
ACCENT = "#2563eb"
ACCENT_HOVER = "#1d4ed8"
INPUT_BG = "#020617"
BORDER = "#334155"


class LoginUI(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.parent = parent
        self.pack(fill="both", expand=True)
        self.build_ui()

    def build_ui(self):
        container = tk.Frame(self, bg=CARD, bd=1, relief="solid", highlightbackground=BORDER, highlightthickness=1)
        container.place(relx=0.5, rely=0.5, anchor="center", width=460, height=380)

        tk.Label(
            container,
            text="Paragon Login",
            font=("Segoe UI", 22, "bold"),
            bg=CARD,
            fg=FG
        ).pack(pady=(28, 8))

        tk.Label(
            container,
            text="Sign in to access your assigned dashboard",
            font=("Segoe UI", 11),
            bg=CARD,
            fg=MUTED
        ).pack(pady=(0, 18))

        tk.Label(
            container,
            text="Username",
            font=("Segoe UI", 10, "bold"),
            bg=CARD,
            fg=FG
        ).pack(anchor="w", padx=40)

        self.username_entry = tk.Entry(
            container,
            font=("Segoe UI", 11),
            bg=INPUT_BG,
            fg="white",
            relief="flat",
            bd=0,
            insertbackground="white"
        )
        self.username_entry.pack(fill="x", padx=40, pady=(6, 16), ipady=8)

        tk.Label(
            container,
            text="Password",
            font=("Segoe UI", 10, "bold"),
            bg=CARD,
            fg=FG
        ).pack(anchor="w", padx=40)

        self.password_entry = tk.Entry(
            container,
            font=("Segoe UI", 11),
            bg=INPUT_BG,
            fg="white",
            relief="flat",
            bd=0,
            insertbackground="white",
            show="*"
        )
        self.password_entry.pack(fill="x", padx=40, pady=(6, 22), ipady=8)

        login_button = tk.Button(
            container,
            text="Login",
            font=("Segoe UI", 11, "bold"),
            bg=ACCENT,
            fg="white",
            activebackground=ACCENT_HOVER,
            activeforeground="white",
            relief="flat",
            height=2,
            cursor="hand2",
            command=self.login
        )
        login_button.pack(fill="x", padx=40)
        login_button.bind("<Enter>", lambda e: login_button.config(bg=ACCENT_HOVER))
        login_button.bind("<Leave>", lambda e: login_button.config(bg=ACCENT))
        
        tk.Label(
            container,
            font=("Segoe UI", 9),
            bg=CARD,
            fg=MUTED,
            justify="center"
        ).pack(pady=(18, 0))

        self.password_entry.bind("<Return>", lambda event: self.login())

    def clear_fields(self):
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)

    def _get_location_name(self, location_id):
        if location_id is None:
            return None
        try:
            conn = Get_Connection()
            cur = conn.cursor()
            cur.execute("SELECT city FROM Location WHERE location_id = ?", (location_id,))
            row = cur.fetchone()
            conn.close()
            return row[0] if row else None
        except Exception:
            return None

    def _scope_text(self, user):
        role = user.get("role")
        if role == "MANAGER":
            return "All Locations"
        city = self._get_location_name(user.get("location_id"))
        return city if city else "Assigned Location"

    def _open_dashboard(self, dashboard_class, user):
        self.parent.withdraw()
        self.clear_fields()
        dashboard_class(self.parent, user)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        try:
            user = AuthController.Login(username, password)
            role = user["role"]
            scope = self._scope_text(user)

            messagebox.showinfo(
                "Login Success",
                f"Welcome {user['username']}\nRole: {role}\nScope: {scope}"
            )

            if role == "MAINTENANCE":
                self._open_dashboard(MaintenanceUI, user)
            elif role == "FINANCE":
                self._open_dashboard(FinanceUI, user)
            elif role == "FRONT_DESK":
                self._open_dashboard(TenantUI, user)
            elif role in ("ADMIN", "MANAGER"):
                self._open_dashboard(AdminUI, user)
            else:
                messagebox.showinfo(
                    "Login Success",
                    f"Logged in as {user['username']} ({role}).\n"
                    "This role does not have a connected UI yet."
                )
                self.parent.deiconify()

        except Exception:
            messagebox.showerror("Login Failed", "Incorrect username or password.")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Paragon Login")
    root.geometry("700x500")
    root.configure(bg=BG)
    root.resizable(False, False)
    LoginUI(root)
    root.mainloop()
