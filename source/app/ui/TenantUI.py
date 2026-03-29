import tkinter as tk
from tkinter import messagebox, ttk
from source.app.controllers.Lease import LeaseController
from source.app.controllers.Tenants import TenantController


class TenantUI:

    def __init__(self, parent, user):
        self.parent = parent
        self.user = user

        self.window = tk.Toplevel(parent)
        self.window.title("Paragon • Front Desk")
        self.window.geometry("1200x750")
        self.window.configure(bg="#0f172a")

        self.build_ui()

    # ---------------- UI ----------------
    def build_ui(self):

        # Sidebar
        sidebar = tk.Frame(self.window, bg="#020617", width=220)
        sidebar.pack(side="left", fill="y")

        tk.Label(sidebar, text="PARAGON",
                 fg="white", bg="#020617",
                 font=("Arial", 18, "bold")).pack(pady=20)

        self.nav_button(sidebar, "Tenant", self.show_tenant)
        self.nav_button(sidebar, "Lease", self.show_lease)
        self.nav_button(sidebar, "Payments", self.show_payments)
        self.nav_button(sidebar, "Maintenance", self.show_maintenance)
        self.nav_button(sidebar, "Complaints", self.show_complaints)

        tk.Button(sidebar, text="Logout",
                  bg="red", fg="black",
                  command=self.logout).pack(side="bottom", pady=20)

        # Content
        self.content = tk.Frame(self.window, bg="#0f172a")
        self.content.pack(side="right", fill="both", expand=True)

        self.show_tenant()

    def nav_button(self, parent, text, command):
        tk.Button(parent, text=text,
                  bg="#020617", fg="#cbd5f5",
                  relief="flat",
                  command=command).pack(fill="x", pady=2)

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    # ---------------- TENANT ----------------
    def show_tenant(self):
        self.clear_content()

        tk.Label(self.content, text="Tenant Management",
                 fg="white", bg="#0f172a",
                 font=("Arial", 20, "bold")).pack(pady=10)

        # SEARCH BAR
        search_frame = tk.Frame(self.content, bg="#1e293b")
        search_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(search_frame, text="Search",
                 bg="#1e293b", fg="white").pack(side="left")

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.live_search)

        self.search_entry = tk.Entry(search_frame,
                                    textvariable=self.search_var,
                                    bg="#020617", fg="white")
        self.search_entry.pack(side="left", padx=10)

        tk.Label(search_frame, text="Occupation",
                 bg="#1e293b", fg="white").pack(side="left")

        self.filter_occ = tk.Entry(search_frame, bg="#020617", fg="white")
        self.filter_occ.pack(side="left", padx=10)

        tk.Button(search_frame, text="Apply",
                  bg="#3b82f6", fg="black",
                  command=self.apply_filter).pack(side="left", padx=10)

        tk.Button(search_frame, text="Reset",
                  bg="#64748b", fg="black",
                  command=self.load_all_tenants).pack(side="left", padx=5)

        # TABLE
        table_frame = tk.Frame(self.content)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("ID", "NI", "First", "Last", "Phone", "Email", "Occupation", "Requirement", "Lease")

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=110)

        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.fill_form)

        # FORM
        form = tk.Frame(self.content, bg="#1e293b")
        form.pack(fill="x", padx=20, pady=10)

        self.ni = self.field(form, "NI")
        self.first = self.field(form, "First")
        self.last = self.field(form, "Last")
        self.phone = self.field(form, "Phone")
        self.email = self.field(form, "Email")
        self.occupation = self.field(form, "Occupation")
        self.reference = self.field(form, "Reference")
        self.requirement = self.field(form, "Apartment Type")
        self.lease_years = self.field(form, "Lease Years")

        # 🔥 NEW FIELDS
        self.apartment_req = self.field(form, "Apartment Req")
        self.lease_years = self.field(form, "Lease Years")
        self.priority = self.field(form, "Priority")
        self.notes = self.field(form, "Notes")

        btns = tk.Frame(form, bg="#1e293b")
        btns.pack(pady=10)

        tk.Button(btns, text="Add", bg="#22c55e",
                  command=self.add_tenant).grid(row=0, column=0, padx=5)

        tk.Button(btns, text="Update", bg="#3b82f6",
                  command=self.update_tenant).grid(row=0, column=1, padx=5)

        tk.Button(btns, text="Delete", bg="#ef4444",
                  command=self.delete_tenant).grid(row=0, column=2, padx=5)

        self.load_all_tenants()

    # ---------------- FIELD ----------------
    def field(self, parent, label):
        frame = tk.Frame(parent, bg="#1e293b")
        frame.pack(fill="x", padx=10, pady=5)

        tk.Label(frame, text=label, width=14,
                 bg="#1e293b", fg="#cbd5f5").pack(side="left")

        entry = tk.Entry(frame, bg="#020617", fg="white", insertbackground="white")
        entry.pack(side="left", fill="x", expand=True)

        return entry

    # ---------------- DATA ----------------
    def load_all_tenants(self):
        self.tree.delete(*self.tree.get_children())

        tenants = TenantController.GetAllTenants()

        for t in tenants:
            self.tree.insert("", "end", values=t)

    def apply_filter(self):
        keyword = self.search_entry.get()
        occ = self.filter_occ.get()

        results = TenantController.SearchTenants(keyword, occ)

        self.tree.delete(*self.tree.get_children())

        for r in results:
            self.tree.insert("", "end", values=r)

    def live_search(self, *args):
        keyword = self.search_var.get()

        results = TenantController.SearchTenants(keyword, "")

        self.tree.delete(*self.tree.get_children())

        for r in results:
            self.tree.insert("", "end", values=r)

    # ---------------- FORM AUTO-FILL ----------------
    def fill_form(self, event):
        selected = self.tree.focus()
        data = self.tree.item(selected, "values")

        if not data:
            return

        fields = [
            self.ni, self.first, self.last, self.phone,
            self.email, self.occupation
        ]

        for i, field in enumerate(fields, start=1):
            field.delete(0, tk.END)
            field.insert(0, data[i])

        if len(data) > 7:
            self.apartment_req.insert(0, data[7])
        if len(data) > 8:
            self.lease_years.insert(0, data[8])

    # ---------------- ACTIONS ----------------
    def add_tenant(self):
        try:
            TenantController.AddTenant(
                self.ni.get(),
                self.first.get(),
                self.last.get(),
                self.phone.get(),
                self.email.get(),
                self.occupation.get(),
                self.reference.get(),
                self.requirement.get(),
                self.lease_years.get()
            )
            self.load_all_tenants()
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
                self.reference.get(),
                self.requirement.get(),
                self.lease_years.get()
            )
            self.load_all_tenants()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_tenant(self):
        try:
            if messagebox.askyesno("Confirm", "Delete tenant?"):
                TenantController.DeleteTenant(self.ni.get())
                self.load_all_tenants()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---------------- OTHER ----------------
    def show_lease(self):
        self.clear_content()

        tk.Label(self.content, text="Lease Management",
                fg="white", bg="#0f172a",
                font=("Arial", 20, "bold")).pack(pady=10)

        # TABLE
        frame = tk.Frame(self.content)
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("LeaseID", "First Name", "Last Name", "Apartment", "Start", "End", "Status")

        self.lease_table = ttk.Treeview(frame, columns=columns, show="headings")

        for col in columns:
            self.lease_table.heading(col, text=col)
            self.lease_table.column(col, anchor="center", width=120)

        self.lease_table.pack(fill="both", expand=True)

        # LOAD DATA
        leases = LeaseController.GetAllLeases()

        for l in leases:
            self.lease_table.insert("", "end", values=l)

        # ACTIONS
        action_frame = tk.Frame(self.content, bg="#0f172a")
        action_frame.pack(pady=10)

        tk.Button(action_frame, text="Generate Invoice",
                bg="#3b82f6", fg="white",
                command=self.generate_invoice).grid(row=0, column=0, padx=10)

        tk.Button(action_frame, text="Terminate Lease",
                bg="#ef4444", fg="white",
                command=self.terminate_lease).grid(row=0, column=1, padx=10)

    def show_payments(self):
        self.clear_content()
        tk.Label(self.content, text="Payments Section",
                 fg="black", bg="#0f172a").pack()

    def show_maintenance(self):
        self.clear_content()
        tk.Label(self.content, text="Maintenance Section",
                 fg="black", bg="#0f172a").pack()

    def show_complaints(self):
        self.clear_content()
        tk.Label(self.content, text="Complaints Section",
                 fg="black", bg="#0f172a").pack()

    # ---------------- LOGOUT ----------------
    def logout(self):
        self.window.destroy()
        self.parent.deiconify()

    def generate_invoice(self):
        selected = self.lease_table.focus()
        data = self.lease_table.item(selected, "values")

        if not data:
            messagebox.showwarning("Select", "Select a lease first")
            return

        lease_id = data[0]

        try:
            LeaseController.GenerateInvoice(lease_id)
            messagebox.showinfo("Success", "Invoice generated")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def terminate_lease(self):
        ni = self.ni.get()

        if not ni:
            messagebox.showwarning("Input", "Enter tenant NI")
            return

        try:
            penalty = LeaseController.TerminateLease(ni)
            messagebox.showinfo("Terminated", f"Penalty: £{penalty:.2f}")
        except Exception as e:
            messagebox.showerror("Error", str(e))