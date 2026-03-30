import tkinter as tk
from source.app.databases.database import Create_Tables
from source.app.ui.LoginUI import LoginUI


def main():
    print("APP START")

    # Create DB tables
    Create_Tables()
    print("DB OK")

    # Create main window
    root = tk.Tk()
    root.title("Paragon Apartment Management System")
    root.geometry("700x500")
    root.configure(bg="#0f172a")

    # Prevent accidental full exit handling
    def on_app_close():
        print("App closed")
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_app_close)

    # Load login UI
    LoginUI(root)
    print("LOGIN UI LOADED")

    root.mainloop()
    print("APP CLOSED")


if __name__ == "__main__":
    main()