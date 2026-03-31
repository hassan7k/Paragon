import tkinter as tk
from tkinter import messagebox
from math import sin
from source.app.controllers.Auth import AuthController


class LoginUI(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg="#030b1a")
        self.parent = parent
        self.pack(fill="both", expand=True)

        self.wave_offset = 0
        self.alpha = 0

        self.build_ui()
        self.fade_in()
        self.animate_waves()

    # ──────────────── UI ────────────────
    def build_ui(self):

        self.canvas = tk.Canvas(self, bg="#030b1a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Glass card
        self.container = tk.Frame(self.canvas, bg="#0f172a")
        self.container.place(relx=0.5, rely=0.5, anchor="center", width=440, height=480)

        self.inner = tk.Frame(self.container, bg="#0f172a")
        self.inner.place(relx=0.5, rely=0.5, anchor="center", width=400, height=440)

        # Title
        tk.Label(self.inner, text="PARAGON",
                 font=("Segoe UI", 26, "bold"),
                 fg="white", bg="#0f172a").pack(pady=(30, 5))

        tk.Label(self.inner, text="Smart Property System",
                 font=("Segoe UI", 10),
                 fg="#94a3b8", bg="#0f172a").pack(pady=(0, 25))

        # Inputs
        self.username_entry = self._create_input("Username")
        self.password_entry = self._create_input("Password", show="*")

        # Show password toggle
        self.show_password = False
        toggle = tk.Button(self.inner, text="Show Password",
                           font=("Segoe UI", 9),
                           bg="#0f172a", fg="#38bdf8",
                           relief="flat",
                           command=self.toggle_password)
        toggle.pack(pady=5)

        # Login button
        self.login_btn = tk.Button(
            self.inner,
            text="SIGN IN",
            font=("Segoe UI", 11, "bold"),
            bg="#0ea5e9",
            fg="#020617",
            activebackground="#38bdf8",
            activeforeground="#020617",
            relief="flat",
            height=2,
            cursor="hand2",
            command=self.login
        )
        self.login_btn.pack(fill="x", padx=60, pady=25)

        # Hover effects
        self.login_btn.bind("<Enter>", lambda e: self.login_btn.config(bg="#38bdf8"))
        self.login_btn.bind("<Leave>", lambda e: self.login_btn.config(bg="#0ea5e9"))

        # Footer
        tk.Label(self.inner,
                 text="Secure Access - Paragon System",
                 font=("Segoe UI", 8),
                 fg="#475569",
                 bg="#0f172a").pack(side="bottom", pady=15)

        self.password_entry.bind("<Return>", lambda e: self.login())

    # ──────────────── INPUT HELPER ────────────────
    def _create_input(self, placeholder, show=None):
        frame = tk.Frame(self.inner, bg="#0f172a")
        frame.pack(fill="x", padx=60, pady=10)

        entry = tk.Entry(
            frame,
            bg="#020617",
            fg="white",
            insertbackground="white",
            relief="flat",
            font=("Segoe UI", 11),
            show=show
        )
        entry.insert(0, placeholder)
        entry.config(fg="#64748b")
        entry.pack(fill="x", ipady=10, padx=2, pady=2)

        def on_focus_in(e):
            if entry.get() == placeholder:
                entry.delete(0, "end")
                entry.config(fg="white")
                if show:
                    entry.config(show=show)

        def on_focus_out(e):
            if not entry.get():
                entry.config(show="")
                entry.insert(0, placeholder)
                entry.config(fg="#64748b")

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

        return entry

    # ──────────────── PASSWORD TOGGLE ────────────────
    def toggle_password(self):
        self.show_password = not self.show_password
        self.password_entry.config(show="" if self.show_password else "*")

    # ──────────────── LOGIN ────────────────
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if username in ("Username", "") or password in ("Password", ""):
            messagebox.showerror("Error", "Please enter username and password.")
            return

        try:
            user_data = AuthController.Login(username, password)
            role = user_data["role"]
            location_id = user_data["location_id"]
            messagebox.showinfo("Welcome", f"Logged in as {role}")

            # Clear login UI
            self.destroy()

            # Route to the correct dashboard
            if role in ("ADMIN", "MANAGER"):
                from source.app.ui.AdminUI import AdminUI
                AdminUI(self.parent, user_data)
            elif role == "FRONT_DESK":
                try:
                    from source.app.ui.TenantUI import TenantUI
                    TenantUI(self.parent, user_data)
                except ImportError:
                    messagebox.showinfo("Info", f"Front Desk module not yet integrated.")
            elif role == "FINANCE":
                try:
                    from source.app.ui.FinanceUI import FinanceUI
                    FinanceUI(self.parent, user_data)
                except ImportError:
                    messagebox.showinfo("Info", f"Finance module not yet integrated.")
            elif role == "MAINTENANCE":
                try:
                    from source.app.ui.MaintenanceUI import MaintenanceUI
                    MaintenanceUI(self.parent, user_data)
                except ImportError:
                    messagebox.showinfo("Info", f"Maintenance module not yet integrated.")
            else:
                messagebox.showerror("Error", f"Unknown role: {role}")

        except ValueError as e:
            messagebox.showerror("Login Failed", str(e))

    # ──────────────── ANIMATIONS ────────────────
    def fade_in(self):
        if self.alpha < 1.0:
            self.alpha += 0.05
            self.after(30, self.fade_in)

    def animate_waves(self):
        self.canvas.delete("wave")
        w = self.canvas.winfo_width() or 700
        h = self.canvas.winfo_height() or 500

        for i in range(0, w, 4):
            y = h - 40 + sin((i + self.wave_offset) * 0.02) * 15
            self.canvas.create_oval(i, y, i + 3, y + 3,
                                    fill="#0ea5e9", outline="", tags="wave")

        self.wave_offset += 2
        self.after(50, self.animate_waves)
