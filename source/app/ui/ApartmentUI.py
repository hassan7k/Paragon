import tkinter as tk
from tkinter import ttk, messagebox
from source.app.controllers.Apartments import ApartmentController
from source.app.controllers.AdminController import AdminController


class ApartmentUI(tk.Toplevel):

    def __init__(self, parent=None, user=None):
        super().__init__(parent)

        self.user = user or {}
        role = self.user.get("role")
        if role not in ("ADMIN", "MANAGER"):
            self.destroy()
            raise PermissionError("Only ADMIN or MANAGER users can manage apartments.")

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

        self.location_options = []
        loc_frame = tk.Frame(form, bg="#0f172a")
        loc_frame.pack(fill="x", pady=5)
        tk.Label(loc_frame, text="Location", width=32, anchor="w", fg="white", bg="#0f172a").pack(side="left")

        if self.user.get("role") == "ADMIN":
            self.location_display = tk.Entry(loc_frame, bg="#020617", fg="white", insertbackground="white")
            self.location_display.pack(side="left", fill="x", expand=True)
            self.location_display.insert(0, f"{self.user.get('location_id')} - Your Assigned Location")
            self.location_display.config(state="disabled")
            self.location_combo = None
        else:
            self.location_combo = ttk.Combobox(loc_frame, state="readonly")
            self.location_combo.pack(side="left", fill="x", expand=True)
            self.load_location_options()

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

    def load_location_options(self):
        try:
            self.location_options = []
            rows = AdminController.GetAllLocations()
            values = []
            for row in rows:
                loc_id, city = int(row[0]), str(row[1])
                self.location_options.append((loc_id, city))
                values.append(f"{loc_id} - {city}")
            if self.location_combo is not None:
                self.location_combo["values"] = values
                if values:
                    self.location_combo.current(0)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _selected_location_id(self):
        if self.user.get("role") == "ADMIN":
            return int(self.user.get("location_id"))
        raw = self.location_combo.get().strip() if self.location_combo is not None else ""
        if not raw:
            return None
        return int(raw.split(" - ", 1)[0])

    def load_apartments(self):
        self.tree.delete(*self.tree.get_children())
        rows = ApartmentController.GetAllApartments()
        if self.user.get("role") == "ADMIN":
            rows = [row for row in rows if int(row[1]) == int(self.user.get("location_id"))]
        for row in rows:
            self.tree.insert("", "end", values=row)

    def add_apartment(self):
        try:
            ApartmentController.CreateApartment(
                int(self._selected_location_id()),
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
        if getattr(self, "location_combo", None) is not None and self.location_combo["values"]:
            self.location_combo.current(0)
        self.apartment_number.delete(0, tk.END)
        self.apartment_type.delete(0, tk.END)
        self.rooms.delete(0, tk.END)
        self.monthly_rent.delete(0, tk.END)
        self.status.delete(0, tk.END)
        self.status.insert(0, "AVAILABLE")