import tkinter as tk
from tkinter import messagebox
from source.app.controllers.Auth import AuthController
from source.app.ui.MaintenanceUI import MaintenanceUI


class LoginUI(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg="#eef2f7")
        self.parent = parent
        self.pack(fill="both", expand=True)

        self.build_ui()

    def build_ui(self):
        container = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        container.place(relx=0.5, rely=0.5, anchor="center", width=420, height=340)

        title = tk.Label(
            container,
            text="Paragon Login",
            font=("Arial", 20, "bold"),
            bg="#ffffff",
            fg="#1f2937"
        )
        title.pack(pady=(25, 10))

        subtitle = tk.Label(
            container,
            text="Sign in to continue",
            font=("Arial", 11),
            bg="#ffffff",
            fg="#4b5563"
        )
        subtitle.pack(pady=(0, 20))

        username_label = tk.Label(
            container,
            text="Username",
            font=("Arial", 10, "bold"),
            bg="#ffffff",
            fg="#1f2937"
        )
        username_label.pack(anchor="w", padx=40)

        self.username_entry = tk.Entry(
            container,
            font=("Arial", 11),
            bg="#f8fafc",
            fg="#111827",
            relief="solid",
            bd=1,
            insertbackground="black"
        )
        self.username_entry.pack(fill="x", padx=40, pady=(5, 15))

        password_label = tk.Label(
            container,
            text="Password",
            font=("Arial", 10, "bold"),
            bg="#ffffff",
            fg="#1f2937"
        )
        password_label.pack(anchor="w", padx=40)

        self.password_entry = tk.Entry(
            container,
            font=("Arial", 11),
            bg="#f8fafc",
            fg="#111827",
            relief="solid",
            bd=1,
            insertbackground="black",
            show="*"
        )
        self.password_entry.pack(fill="x", padx=40, pady=(5, 20))

        login_button = tk.Button(
            container,
            text="Login",
            font=("Arial", 11, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            height=2,
            cursor="hand2",
            command=self.login
        )
        login_button.pack(fill="x", padx=40)

        self.password_entry.bind("<Return>", lambda event: self.login())

    def clear_fields(self):
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        try:
            user = AuthController.Login(username, password)
            role = user["role"]

            if role == "MAINTENANCE":
                messagebox.showinfo("Login Success", f"Welcome {user['username']} ({role})")

                # Hide login window
                self.parent.withdraw()

                # Clear fields for next login
                self.clear_fields()

                # Open maintenance dashboard
                MaintenanceUI(self.parent, user)

            else:
                messagebox.showinfo(
                    "Login Success",
                    f"Logged in as {user['username']} ({role}).\nOnly Maintenance UI is connected right now."
                )

        except Exception as error:
            messagebox.showerror("Login Failed", str(error))
