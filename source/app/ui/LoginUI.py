import tkinter as tk
from tkinter import messagebox
from math import sin
from source.app.controllers.Auth import AuthController
from source.app.ui.MaintenanceUI import MaintenanceUI
from source.app.ui.FinanceUI import FinanceUI
from source.app.ui.TenantUI import TenantUI


class LoginUI(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg="#030b1a")
        self.parent = parent
        self.pack(fill="both", expand=True)

        self.wave_offset = 0
        self.alpha = 0  # fade-in

        self.build_ui()
        self.fade_in()
        self.animate_waves()

    # ---------------- UI ----------------
    def build_ui(self):

        self.canvas = tk.Canvas(self, bg="#030b1a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # 🌊 GLASS CARD
        self.container = tk.Frame(self.canvas, bg="#0f172a")
        self.container.place(relx=0.5, rely=0.5, anchor="center", width=440, height=480)

        self.inner = tk.Frame(self.container, bg="#0f172a")
        self.inner.place(relx=0.5, rely=0.5, anchor="center", width=400, height=440)

        # ✨ TITLE
        tk.Label(self.inner, text="PARAGON",
                 font=("Segoe UI", 26, "bold"),
                 fg="white", bg="#0f172a").pack(pady=(30, 5))

        tk.Label(self.inner, text="Smart Property System",
                 font=("Segoe UI", 10),
                 fg="#94a3b8", bg="#0f172a").pack(pady=(0, 25))

        # INPUTS
        self.username_entry = self.create_input("Username")
        self.password_entry = self.create_input("Password", show="*")

        # 👁️ SHOW PASSWORD BUTTON
        self.show_password = False
        toggle = tk.Button(self.inner, text="👁 Show Password",
                           font=("Segoe UI", 9),
                           bg="#0f172a", fg="#38bdf8",
                           relief="flat",
                           command=self.toggle_password)
        toggle.pack(pady=5)

        # 🔘 LOGIN BUTTON
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

        # Hover glow
        self.login_btn.bind("<Enter>", lambda e: self.login_btn.config(bg="#38bdf8"))
        self.login_btn.bind("<Leave>", lambda e: self.login_btn.config(bg="#0ea5e9"))

        # Footer
        tk.Label(self.inner,
                 text="Secure Access • Paragon System",
                 font=("Segoe UI", 8),
                 fg="#475569",
                 bg="#0f172a").pack(side="bottom", pady=15)

        self.password_entry.bind("<Return>", lambda e: self.login())

    # ---------------- INPUT ----------------
    def create_input(self, placeholder, show=None):

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
        entry.pack(fill="x", ipady=10)

        entry.insert(0, placeholder)
        entry.config(fg="#64748b")

        def on_focus_in(e):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(fg="white")
                if show:
                    entry.config(show=show)

        def on_focus_out(e):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(fg="#64748b")
                if show:
                    entry.config(show="")

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

        # underline glow
        line = tk.Frame(frame, height=2, bg="#334155")
        line.pack(fill="x")

        entry.bind("<FocusIn>", lambda e: line.config(bg="#38bdf8"))
        entry.bind("<FocusOut>", lambda e: line.config(bg="#334155"))

        return entry

    # ---------------- PASSWORD TOGGLE ----------------
    def toggle_password(self):
        self.show_password = not self.show_password
        if self.show_password:
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    # ---------------- FADE IN ----------------
    def fade_in(self):
        if self.alpha < 1:
            self.alpha += 0.05
            self.parent.attributes("-alpha", self.alpha)
            self.after(30, self.fade_in)

    # ---------------- WAVES ----------------
    def animate_waves(self):
        self.canvas.delete("wave")

        width = self.winfo_width() or 900
        height = self.winfo_height() or 700

        intensity = 1.0
        if width > 1200:
            intensity = 0.4  # 🔥 dim when fullscreen

        for layer, color, speed, amp in [
            (400, "#0f1c3f", 0.01, 10),
            (450, "#132a5a", 0.015, 12),
            (500, "#1b3a6f", 0.02, 15)
        ]:
            points = []
            for x in range(0, width, 30):
                y = layer + sin((x + self.wave_offset) * speed) * (amp * intensity)
                points.append((x, y))

            self.draw_wave(points, color)

        self.wave_offset += 2
        self.after(80, self.animate_waves)

    def draw_wave(self, points, color):
        coords = []

        for x, y in points:
            coords.extend([x, y])

        coords.extend([self.winfo_width(), self.winfo_height()])
        coords.extend([0, self.winfo_height()])

        self.canvas.create_polygon(
            coords,
            fill=color,
            smooth=True,
            stipple="gray50",
            outline="",
            tags="wave"
        )

    # ---------------- LOGIN ----------------
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if username == "Username":
            username = ""
        if password == "Password":
            password = ""

        try:
            user = AuthController.Login(username, password)
            role = user["role"]

            self.parent.withdraw()

            if role == "FRONT_DESK":
                TenantUI(self.parent, user)

            elif role == "MAINTENANCE":
                MaintenanceUI(self.parent, user)

            elif role == "FINANCE":
                FinanceUI(self.parent, user)

            else:
                messagebox.showinfo("Info", "No UI assigned")
                self.parent.deiconify()

        except Exception as error:
            messagebox.showerror("Login Failed", str(error))