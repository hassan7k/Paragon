import tkinter as tk
from tkinter import ttk, messagebox
from source.app.controllers.Apartments import ApartmentController


class ApartmentUI(tk.Toplevel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.title("Apartment Management")
        self.geometry("950x650")
        self.configure(bg="#0f172a")

        self.build_ui()
        self.load_apartments()

    def build_ui(self):
        tk.Label(
            self,
            text="Apartment Management",
            font=("Arial", 18, "bold"),
            fg="white",
            bg="#0f172a"
        ).pack(pady=15)

        form = tk.Frame(self, bg="#0f172a")
        form.pack(fill="x", padx=20, pady=10)

        self.location_id = self.field(form, "Location ID")
        self.apartment_number = self.field(form, "Apartment Number")
        self.apartment_type = self.field(form, "Type")
        self.rooms = self.field(form, "Rooms")
        self.monthly_rent = self.field(form, "Monthly Rent")
        self.status = self.field(form, "Status (AVAILABLE/OCCUPIED/MAINTENANCE)")
        self.status.insert(0, "AVAILABLE")

        tk.Button(
            self,
            text="Add Apartment",
            bg="#22c55e",
            fg="black",
            command=self.add_apartment
        ).pack(pady=10)

        table_frame = tk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("ApartmentID", "LocationID", "Number", "Type", "Rooms", "Rent", "Status")

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=120)

        self.tree.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")

    def field(self, parent, label):
        frame = tk.Frame(parent, bg="#0f172a")
        frame.pack(fill="x", pady=5)

        tk.Label(frame, text=label, width=32, anchor="w", fg="white", bg="#0f172a").pack(side="left")

        entry = tk.Entry(frame, bg="#020617", fg="white", insertbackground="white")
        entry.pack(side="left", fill="x", expand=True)

        return entry

    def load_apartments(self):
        self.tree.delete(*self.tree.get_children())

        rows = ApartmentController.GetAllApartments()

        for row in rows:
            self.tree.insert("", "end", values=row)

    def add_apartment(self):
        try:
            ApartmentController.CreateApartment(
                int(self.location_id.get()),
                self.apartment_number.get(),
                self.apartment_type.get(),
                int(self.rooms.get()),
                float(self.monthly_rent.get()),
                self.status.get().strip().upper()
            )

            messagebox.showinfo("Success", "Apartment added successfully")
            self.load_apartments()
            self.clear_form()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear_form(self):
        self.location_id.delete(0, tk.END)
        self.apartment_number.delete(0, tk.END)
        self.apartment_type.delete(0, tk.END)
        self.rooms.delete(0, tk.END)
        self.monthly_rent.delete(0, tk.END)
        self.status.delete(0, tk.END)
        self.status.insert(0, "AVAILABLE")