import tkinter as tk
from source.app.databases.database import Create_Tables
from source.app.ui.LoginUI import LoginUI


if __name__ == "__main__":
    Create_Tables()

    root = tk.Tk()
    root.title("Paragon Apartment Management System")
    root.geometry("700x500")
    root.configure(bg="#eef2f7")

    LoginUI(root)

    root.mainloop()
