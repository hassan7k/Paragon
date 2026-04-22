import tkinter as tk
from tkinter import ttk, messagebox
from source.app.controllers.Complaints import ComplaintController
from source.app.controllers.Tenants import TenantController


class ComplaintUI(tk.Toplevel):

    def __init__(self, parent=None, user=None):
        super().__init__(parent)

        self.parent = parent
        self.user = user or {}
        self.role = self.user.get("role")

        if self.role not in ("FRONT_DESK", "ADMIN", "MANAGER"):
            self.destroy()
            raise PermissionError("Only FRONT_DESK, ADMIN, or MANAGER users can access complaints.")

        self.title("Complaint Management")
        self.geometry("1000x600")
        self.configure(bg="#0f172a")

        self.build_ui()
        self.load_complaints()

    # ---------------- UI ----------------
    def build_ui(self):

        tk.Label(self, text="Complaint Management",
                 font=("Arial", 20, "bold"),
                 fg="white", bg="#0f172a").pack(pady=10)

        # TABLE
        columns = ("Complaint ID", "Tenant ID", "Apartment ID", "Description", "Status", "Created At")

        self.tree = ttk.Treeview(self, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        # FORM
        form = tk.Frame(self, bg="#1e293b")
        form.pack(fill="x", padx=20, pady=10)

        self.ni_entry = self.field(form, "Tenant NI (lookup)")
        self.desc_entry = self.field(form, "Complaint Description")

        # BUTTONS
        btn_frame = tk.Frame(self, bg="#0f172a")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Add Complaint",
                  bg="#22c55e", fg="black",
                  command=self.add_complaint).pack(side="left", padx=5)

        tk.Button(btn_frame, text="Refresh",
                  bg="#3b82f6", fg="black",
                  command=self.load_complaints).pack(side="left", padx=5)

        if self.role in ("ADMIN", "MANAGER"):
            tk.Button(btn_frame, text="Close Complaint",
                      bg="#f59e0b", fg="black",
                      command=self.close_complaint).pack(side="left", padx=5)

        tk.Button(btn_frame, text="Close Window",
                  bg="#ef4444", fg="black",
                  command=self.close).pack(side="left", padx=5)

    # ---------------- FIELD ----------------
    def field(self, parent, label):
        frame = tk.Frame(parent, bg="#1e293b")
        frame.pack(fill="x", padx=10, pady=5)

        tk.Label(frame, text=label, width=18,
                 bg="#1e293b", fg="white").pack(side="left")

        entry = tk.Entry(frame, bg="#020617", fg="white")
        entry.pack(side="left", fill="x", expand=True)

        return entry

    # ---------------- LOAD DATA ----------------
    def load_complaints(self):
        try:
            self.tree.delete(*self.tree.get_children())

            data = ComplaintController.GetComplaints()

            for row in data:
                self.tree.insert("", "end", values=row)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---------------- ADD ----------------
    def add_complaint(self):
        try:
            ni = self.ni_entry.get().strip()
            desc = self.desc_entry.get().strip()

            if not ni:
                raise ValueError("NI number required")

            if not desc:
                raise ValueError("Description required")

            tenant = TenantController.GetTenantByNI(ni)
            if not tenant:
                raise ValueError("Tenant not found")

            tenant_id = tenant["tenant_id"] if isinstance(tenant, dict) else tenant[0]
            apartment_id = ComplaintController.GetTenantActiveApartmentId(tenant_id)

            ComplaintController.CreateComplaint(tenant_id, apartment_id, desc)

            messagebox.showinfo("Success", "Complaint added successfully")

            self.load_complaints()
            self.clear_fields()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---------------- CLOSE COMPLAINT ----------------
    def close_complaint(self):
        try:
            selected = self.tree.focus()
            if not selected:
                raise ValueError("Select a complaint first")

            data = self.tree.item(selected, "values")
            complaint_id = int(data[0])

            ComplaintController.CloseComplaint(complaint_id)
            messagebox.showinfo("Success", "Complaint closed")
            self.load_complaints()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---------------- CLEAR ----------------
    def clear_fields(self):
        self.ni_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)

    # ---------------- CLOSE ----------------
    def close(self):
        self.destroy()
        if self.parent:
            self.parent.deiconify()