import tkinter as tk
from tkinter import messagebox
from source.app.controllers.Tenants import TenantController


class TenantUI:

    def __init__(self, parent, user):
        self.parent = parent
        self.user = user

        self.window = tk.Toplevel(parent)
        self.window.title("Tenant Dashboard")
        self.window.geometry("1100x700")
        self.window.configure(bg="#0f172a")

        # Handle close properly
        self.window.protocol("WM_DELETE_WINDOW", self.logout)

        self.build_ui()

    # ---------------- UI ----------------
    def build_ui(self):

        # Header
        header = tk.Frame(self.window, bg="#020617", height=60)
        header.pack(fill="x")

        tk.Label(header,
                 text="🏢 Paragon Tenant Management",
                 font=("Segoe UI", 16, "bold"),
                 fg="white", bg="#020617").pack(side="left", padx=20)

        tk.Button(header,
                  text="Logout",
                  bg="#dc2626", fg="black",
                  relief="flat",
                  command=self.logout).pack(side="right", padx=20, pady=10)

        # Main layout
        main = tk.Frame(self.window, bg="#0f172a")
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # LEFT PANEL (FORM)
        left = tk.Frame(main, bg="#1e293b", bd=0)
        left.pack(side="left", fill="y", padx=(0, 15))

        tk.Label(left, text="Tenant Details",
                 font=("Segoe UI", 14, "bold"),
                 fg="white", bg="#1e293b").pack(pady=10)

        self.ni = self.create_field(left, "NI Number")
        self.first = self.create_field(left, "First Name")
        self.last = self.create_field(left, "Last Name")
        self.phone = self.create_field(left, "Phone")
        self.email = self.create_field(left, "Email")
        self.occupation = self.create_field(left, "Occupation")
        self.reference = self.create_field(left, "Reference")

        # Buttons
        btn_frame = tk.Frame(left, bg="#1e293b")
        btn_frame.pack(pady=15)

        self.create_button(btn_frame, "Add", self.add_tenant, "#22c55e").grid(row=0, column=0, padx=5)
        self.create_button(btn_frame, "Update", self.update_tenant, "#eab308").grid(row=0, column=1, padx=5)
        self.create_button(btn_frame, "Search", self.search_tenant, "#3b82f6").grid(row=0, column=2, padx=5)
        self.create_button(btn_frame, "Delete", self.delete_tenant, "#ef4444").grid(row=0, column=3, padx=5)

        # RIGHT PANEL (OPERATIONS)
        right = tk.Frame(main, bg="#1e293b")
        right.pack(side="right", fill="both", expand=True)

        tk.Label(right, text="Operations",
                 font=("Segoe UI", 14, "bold"),
                 fg="white", bg="#1e293b").pack(pady=10)

        # Lease / Payment buttons
        action_frame = tk.Frame(right, bg="#1e293b")
        action_frame.pack(pady=10)

        self.create_button(action_frame, "View Lease", self.view_lease, "#6366f1").grid(row=0, column=0, padx=5)
        self.create_button(action_frame, "Payments", self.view_payments, "#06b6d4").grid(row=0, column=1, padx=5)
        self.create_button(action_frame, "Early Exit", self.request_early_leave, "#f97316").grid(row=0, column=2, padx=5)

        # Complaint section
        complaint_box = tk.Frame(right, bg="#0f172a")
        complaint_box.pack(fill="x", padx=20, pady=10)

        tk.Label(complaint_box, text="Complaint",
                 fg="white", bg="#0f172a").pack(anchor="w")

        self.complaint_text = tk.Entry(complaint_box, bg="#1e293b", fg="white")
        self.complaint_text.pack(fill="x", pady=5)

        self.create_button(complaint_box, "Submit Complaint",
                           self.add_complaint, "#ef4444").pack(pady=5)

        # Maintenance section
        maintenance_box = tk.Frame(right, bg="#0f172a")
        maintenance_box.pack(fill="x", padx=20, pady=10)

        tk.Label(maintenance_box, text="Maintenance Request",
                 fg="white", bg="#0f172a").pack(anchor="w")

        self.apartment_id = tk.Entry(maintenance_box, bg="#1e293b", fg="white")
        self.apartment_id.pack(fill="x", pady=5)
        self.apartment_id.insert(0, "Apartment ID")

        self.issue = tk.Entry(maintenance_box, bg="#1e293b", fg="white")
        self.issue.pack(fill="x", pady=5)
        self.issue.insert(0, "Issue description")

        self.create_button(maintenance_box, "Submit Request",
                           self.add_maintenance, "#22c55e").pack(pady=5)

    # ---------------- UI HELPERS ----------------
    def create_field(self, parent, label):
        frame = tk.Frame(parent, bg="#1e293b")
        frame.pack(fill="x", padx=10, pady=5)

        tk.Label(frame, text=label,
                 fg="#cbd5f5", bg="#1e293b").pack(anchor="w")

        entry = tk.Entry(frame, bg="#0f172a", fg="white", insertbackground="white")
        entry.pack(fill="x", pady=2)

        return entry

    def create_button(self, parent, text, command, color):
        return tk.Button(parent,
                         text=text,
                         bg=color,
                         fg="darkblue",
                         relief="flat",
                         width=12,
                         height=2,
                         command=command)

    # ---------------- FUNCTIONS ----------------

    def add_tenant(self):
        try:
            TenantController.AddTenant(
                self.ni.get(),
                self.first.get(),
                self.last.get(),
                self.phone.get(),
                self.email.get(),
                self.occupation.get(),
                self.reference.get()
            )
            messagebox.showinfo("Success", "Tenant added")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def search_tenant(self):
        try:
            t = TenantController.GetTenant(self.ni.get())

            if t:
                self.first.delete(0, tk.END)
                self.first.insert(0, t["first_name"])

                self.last.delete(0, tk.END)
                self.last.insert(0, t["last_name"])

                self.phone.delete(0, tk.END)
                self.phone.insert(0, t["phone"])

                self.email.delete(0, tk.END)
                self.email.insert(0, t["email"])

                self.occupation.delete(0, tk.END)
                self.occupation.insert(0, t["occupation"] or "")

                self.reference.delete(0, tk.END)
                self.reference.insert(0, t["tenant_references"] or "")

                messagebox.showinfo("Loaded", "Tenant found")
            else:
                messagebox.showwarning("Not Found", "No tenant found")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_tenant(self):
        try:
            TenantController.UpdateTenant(
                self.ni.get(),
                self.first.get(),
                self.last.get(),
                self.phone.get(),
                self.email.get(),
                self.occupation.get(),
                self.reference.get()
            )
            messagebox.showinfo("Success", "Updated")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_tenant(self):
        try:
            TenantController.DeleteTenant(self.ni.get())
            messagebox.showinfo("Success", "Deleted")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def view_lease(self):
        lease = TenantController.GetLease(self.ni.get())
        if lease:
            messagebox.showinfo("Lease",
                                f"Apt: {lease['apartment_id']}\n"
                                f"Rent: £{lease['rent']}\n"
                                f"Status: {lease['status']}")
        else:
            messagebox.showwarning("Not Found", "No lease")

    def view_payments(self):
        payments = TenantController.GetPayments(self.ni.get())
        if payments:
            text = "\n".join([f"£{p['amount']} - {p['date']}" for p in payments])
            messagebox.showinfo("Payments", text)
        else:
            messagebox.showwarning("Empty", "No payments")

    def request_early_leave(self):
        try:
            penalty = TenantController.TerminateLease(self.ni.get())
            messagebox.showinfo("Exit", f"Penalty: £{penalty:.2f}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def add_complaint(self):
        try:
            TenantController.AddComplaint(
                self.ni.get(),
                self.complaint_text.get()
            )
            messagebox.showinfo("Success", "Complaint added")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def add_maintenance(self):
        try:
            TenantController.AddMaintenance(
                self.ni.get(),
                self.apartment_id.get(),
                self.issue.get()
            )
            messagebox.showinfo("Success", "Request added")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def logout(self):
        self.window.destroy()
        self.parent.deiconify()
        self.parent.lift()
        self.parent.focus_force()