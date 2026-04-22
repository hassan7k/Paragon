import tkinter as tk
from tkinter import messagebox, ttk
from source.app.controllers.Tenants import TenantController
from source.app.controllers.Complaints import ComplaintController
from source.app.controllers.Maintenance import MaintenanceController
from source.app.controllers.Lease import LeaseController
from source.app.databases.database import Get_Connection


class TenantUI:

    def __init__(self, parent, user):
        self.parent = parent
        self.user = user
        self.role = (user or {}).get("role")

        if self.role != "FRONT_DESK":
            raise PermissionError("Only FRONT_DESK users can access the front-desk dashboard.")

        self.window = tk.Toplevel(parent)
        self.window.title("Paragon • Front Desk")
        self.window.geometry("1280x780")
        self.window.configure(bg="#0f172a")
        self.window.protocol("WM_DELETE_WINDOW", self.logout)

        self.build_ui()

    # ============================================================
    # Shared helpers
    # ============================================================
    def nav_button(self, parent, text, command):
        tk.Button(parent, text=text, bg="#020617", fg="#cbd5f5", relief="flat", command=command).pack(fill="x", pady=2)

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def field(self, parent, label):
        frame = tk.Frame(parent, bg="#1e293b")
        frame.pack(fill="x", padx=10, pady=5)
        tk.Label(frame, text=label, width=20, bg="#1e293b", fg="#cbd5f5").pack(side="left")
        entry = tk.Entry(frame, bg="#020617", fg="white", insertbackground="white")
        entry.pack(side="left", fill="x", expand=True)
        return entry

    def _resolve_tenant_identifier(self, raw_value: str) -> int:
        """
        Accept either a numeric tenant_id or a tenant NI number.
        Front-desk staff usually know NI, not DB ids, so both are supported.
        """
        value = (raw_value or "").strip()
        if not value:
            raise ValueError("Tenant ID / NI is required.")

        if value.isdigit():
            return int(value)

        tenant = TenantController.GetTenantByNI(value)
        if not tenant:
            raise ValueError("Tenant not found.")
        if isinstance(tenant, dict):
            return int(tenant["tenant_id"])
        return int(tenant[0])

    def _get_active_apartment_id(self, tenant_id: int):
        """
        Try the complaint helper first, then fall back to a direct DB lookup.
        """
        try:
            apartment_id = ComplaintController.GetTenantActiveApartmentId(tenant_id)
            if apartment_id:
                return apartment_id
        except Exception:
            pass

        conn = Get_Connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT apartment_id
                FROM Lease
                WHERE tenant_id = ? AND status = 'ACTIVE'
                ORDER BY lease_id DESC
                LIMIT 1
            """, (tenant_id,))
            row = cur.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def _get_complaints_by_tenant(self, tenant_id: int):
        """
        ComplaintController does not expose GetComplaintsByTenant, so filter the full list here.
        """
        rows = ComplaintController.GetComplaints()
        return [row for row in rows if int(row[1]) == int(tenant_id)]

    def _safe_clear_tree(self, tree_attr_name: str):
        tree = getattr(self, tree_attr_name, None)
        if tree:
            tree.delete(*tree.get_children())

    # ============================================================
    # UI shell
    # ============================================================
    def build_ui(self):
        sidebar = tk.Frame(self.window, bg="#020617", width=220)
        sidebar.pack(side="left", fill="y")

        tk.Label(sidebar, text="PARAGON", fg="white", bg="#020617", font=("Arial", 18, "bold")).pack(pady=20)
        self.nav_button(sidebar, "Tenant", self.show_tenant)
        self.nav_button(sidebar, "Lease Allocation", self.show_lease_allocation)
        self.nav_button(sidebar, "Maintenance", self.show_maintenance)
        self.nav_button(sidebar, "Complaints", self.show_complaints)

        tk.Button(sidebar, text="Logout", bg="red", fg="black", command=self.logout).pack(side="bottom", pady=20)

        self.content = tk.Frame(self.window, bg="#0f172a")
        self.content.pack(side="right", fill="both", expand=True)
        self.show_tenant()

    # ============================================================
    # TENANT MANAGEMENT
    # ============================================================
    def show_tenant(self):
        self.clear_content()
        tk.Label(self.content, text="Tenant Management", fg="white", bg="#0f172a", font=("Arial", 20, "bold")).pack(pady=10)

        search_frame = tk.Frame(self.content, bg="#1e293b")
        search_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(search_frame, text="Search", bg="#1e293b", fg="white").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.live_search)
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, bg="#020617", fg="white")
        self.search_entry.pack(side="left", padx=10)

        tk.Label(search_frame, text="Occupation", bg="#1e293b", fg="white").pack(side="left")
        self.filter_occ = tk.Entry(search_frame, bg="#020617", fg="white")
        self.filter_occ.pack(side="left", padx=10)

        tk.Button(search_frame, text="Apply", bg="#3b82f6", fg="black", command=self.apply_filter).pack(side="left", padx=10)
        tk.Button(search_frame, text="Reset", bg="#64748b", fg="black", command=self.load_all_tenants).pack(side="left", padx=5)

        table_frame = tk.Frame(self.content)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("ID", "NI", "First", "Last", "Phone", "Email", "Occupation", "Requirement", "Lease Years")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=120)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.fill_form)

        form = tk.Frame(self.content, bg="#1e293b")
        form.pack(fill="x", padx=20, pady=10)

        self.ni = self.field(form, "NI")
        self.first = self.field(form, "First")
        self.last = self.field(form, "Last")
        self.phone = self.field(form, "Phone")
        self.email = self.field(form, "Email")
        self.occupation = self.field(form, "Occupation")
        self.reference = self.field(form, "Reference")
        self.requirement = self.field(form, "Apartment Requirement")
        self.lease_years = self.field(form, "Lease Years")
        self.emergency = self.field(form, "Emergency Contact")
        self.notes = self.field(form, "Notes")

        btns = tk.Frame(form, bg="#1e293b")
        btns.pack(pady=10)
        tk.Button(btns, text="Add", bg="#22c55e", command=self.add_tenant).grid(row=0, column=0, padx=5)
        tk.Button(btns, text="Update", bg="#3b82f6", command=self.update_tenant).grid(row=0, column=1, padx=5)
        tk.Button(btns, text="Delete", bg="#ef4444", command=self.delete_tenant).grid(row=0, column=2, padx=5)
        tk.Button(btns, text="Send To Lease Allocation", bg="#f59e0b", command=self.prefill_selected_tenant_to_lease).grid(row=0, column=3, padx=5)

        self.load_all_tenants()

    def load_all_tenants(self):
        self.tree.delete(*self.tree.get_children())
        for tenant in TenantController.GetAllTenants():
            self.tree.insert("", "end", values=tenant)

    def apply_filter(self):
        keyword = self.search_entry.get()
        occupation = self.filter_occ.get()
        self.tree.delete(*self.tree.get_children())
        for row in TenantController.SearchTenants(keyword, occupation):
            self.tree.insert("", "end", values=row)

    def live_search(self, *args):
        keyword = self.search_var.get()
        self.tree.delete(*self.tree.get_children())
        for row in TenantController.SearchTenants(keyword, ""):
            self.tree.insert("", "end", values=row)

    def fill_form(self, event):
        selected = self.tree.focus()
        if not selected:
            return
        data = self.tree.item(selected, "values")
        if not data:
            return

        fields = [self.ni, self.first, self.last, self.phone, self.email, self.occupation]
        for i, field in enumerate(fields, start=1):
            field.delete(0, tk.END)
            field.insert(0, data[i])

        self.requirement.delete(0, tk.END)
        self.requirement.insert(0, data[7] if len(data) > 7 else "")
        self.lease_years.delete(0, tk.END)
        self.lease_years.insert(0, data[8] if len(data) > 8 else "")

    def add_tenant(self):
        try:
            TenantController.AddTenantExtended(
                self.ni.get(), self.first.get(), self.last.get(), self.phone.get(), self.email.get(),
                self.occupation.get(), self.reference.get(), self.requirement.get(), self.lease_years.get(),
                self.emergency.get(), self.notes.get(),
            )
            self.load_all_tenants()
            self.clear_tenant_form()
            messagebox.showinfo("Success", "Tenant added successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_tenant(self):
        try:
            TenantController.UpdateTenant(
                self.ni.get(), self.first.get(), self.last.get(), self.phone.get(), self.email.get(),
                self.occupation.get(), self.reference.get(), self.requirement.get(), self.lease_years.get(),
            )
            self.load_all_tenants()
            self.clear_tenant_form()
            messagebox.showinfo("Success", "Tenant updated")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_tenant(self):
        try:
            if messagebox.askyesno("Confirm", "Delete tenant?"):
                TenantController.DeleteTenant(self.ni.get())
                self.load_all_tenants()
                self.clear_tenant_form()
                messagebox.showinfo("Success", "Tenant deleted")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear_tenant_form(self):
        for field in [self.ni, self.first, self.last, self.phone, self.email,
                      self.occupation, self.reference, self.requirement,
                      self.lease_years, self.emergency, self.notes]:
            field.delete(0, tk.END)

    # ============================================================
    # LEASE ALLOCATION
    # ============================================================
    def show_lease_allocation(self):
        self.clear_content()
        tk.Label(self.content, text="Lease Allocation", fg="white", bg="#0f172a", font=("Arial", 20, "bold")).pack(pady=10)

        note = (
            "Front-desk staff can allocate an available apartment to a tenant by creating a lease. "
            "This does not include apartment creation, apartment status management, or administrative property controls."
        )
        tk.Label(self.content, text=note, wraplength=900, justify="left", fg="#cbd5f5", bg="#0f172a").pack(padx=20, pady=(0, 12))

        form = tk.Frame(self.content, bg="#1e293b")
        form.pack(fill="x", padx=20, pady=10)
        self.lease_tenant_id = self.field(form, "Tenant ID / NI")
        self.lease_apartment_id = self.field(form, "Apartment ID")
        self.lease_start = self.field(form, "Start Date (YYYY-MM-DD)")
        self.lease_end = self.field(form, "End Date (YYYY-MM-DD)")
        self.lease_deposit = self.field(form, "Deposit")
        self.lease_rent = self.field(form, "Monthly Rent")
        self.lease_due = self.field(form, "First Due Date (YYYY-MM-DD)")

        button_row = tk.Frame(form, bg="#1e293b")
        button_row.pack(pady=10)
        tk.Button(button_row, text="Create Lease", bg="#22c55e", command=self.create_lease).pack(side="left", padx=5)
        tk.Button(button_row, text="Load Available Apartments", bg="#3b82f6", command=self.load_available_apartments).pack(side="left", padx=5)
        tk.Button(button_row, text="Load Leases", bg="#64748b", command=self.load_leases).pack(side="left", padx=5)
        tk.Button(button_row, text="Clear", bg="#f59e0b", command=self.clear_lease_form).pack(side="left", padx=5)

        tables = tk.Frame(self.content, bg="#0f172a")
        tables.pack(fill="both", expand=True, padx=20, pady=10)

        left = tk.LabelFrame(tables, text=" Available Apartments ", bg="#1e293b", fg="#38bdf8")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = tk.LabelFrame(tables, text=" Existing Leases ", bg="#1e293b", fg="#38bdf8")
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        apt_cols = ("Apartment ID", "Location ID", "Number", "Type", "Rooms", "Rent", "Status")
        self.available_apartment_tree = ttk.Treeview(left, columns=apt_cols, show="headings", height=14)
        for col in apt_cols:
            self.available_apartment_tree.heading(col, text=col)
            self.available_apartment_tree.column(col, anchor="center", width=110)
        self.available_apartment_tree.pack(fill="both", expand=True, padx=6, pady=6)
        self.available_apartment_tree.bind("<<TreeviewSelect>>", self.prefill_selected_apartment)

        lease_cols = ("Lease ID", "First Name", "Last Name", "Apartment", "Start", "End", "Status")
        self.lease_table = ttk.Treeview(right, columns=lease_cols, show="headings", height=14)
        for col in lease_cols:
            self.lease_table.heading(col, text=col)
            self.lease_table.column(col, anchor="center", width=120)
        self.lease_table.pack(fill="both", expand=True, padx=6, pady=6)

        self.load_available_apartments()
        self.load_leases()

    def load_available_apartments(self):
        self.available_apartment_tree.delete(*self.available_apartment_tree.get_children())
        conn = Get_Connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT apartment_id, location_id, apartment_number, type, rooms, monthly_rent, status
            FROM Apartment
            WHERE status = 'AVAILABLE'
            ORDER BY location_id, apartment_number
        """)
        rows = cur.fetchall()
        conn.close()
        for row in rows:
            self.available_apartment_tree.insert("", "end", values=row)

    def prefill_selected_apartment(self, event=None):
        selected = self.available_apartment_tree.focus()
        if not selected:
            return
        data = self.available_apartment_tree.item(selected, "values")
        if not data:
            return
        self.lease_apartment_id.delete(0, tk.END)
        self.lease_apartment_id.insert(0, data[0])
        self.lease_rent.delete(0, tk.END)
        self.lease_rent.insert(0, data[5])

    def prefill_selected_tenant_to_lease(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Select a tenant first.")
            return
        data = self.tree.item(selected, "values")
        self.show_lease_allocation()
        self.lease_tenant_id.delete(0, tk.END)
        # Insert NI because front desk naturally works with NI
        self.lease_tenant_id.insert(0, data[1])

    def create_lease(self):
        try:
            tenant_id = self._resolve_tenant_identifier(self.lease_tenant_id.get())
            lease_id = LeaseController.CreateLease(
                tenant_id,
                int(self.lease_apartment_id.get()),
                self.lease_start.get().strip(),
                self.lease_end.get().strip(),
                float(self.lease_deposit.get()),
                float(self.lease_rent.get()),
                self.lease_due.get().strip(),
            )
            messagebox.showinfo("Success", f"Lease created successfully.\nLease ID: {lease_id}")
            self.load_leases()
            self.load_available_apartments()
            self.clear_lease_form()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_leases(self):
        if hasattr(self, "lease_table"):
            self.lease_table.delete(*self.lease_table.get_children())
            for lease in LeaseController.GetAllLeases():
                self.lease_table.insert("", "end", values=lease)

    def clear_lease_form(self):
        for field in [self.lease_tenant_id, self.lease_apartment_id, self.lease_start, self.lease_end,
                      self.lease_deposit, self.lease_rent, self.lease_due]:
            field.delete(0, tk.END)

    # ============================================================
    # MAINTENANCE REQUESTS
    # ============================================================
    def show_maintenance(self):
        self.clear_content()
        tk.Label(self.content, text="Maintenance Request Registration", fg="white", bg="#0f172a", font=("Arial", 20, "bold")).pack(pady=10)
        note = "Front-desk staff can register and track maintenance requests only. Scheduling, status changes, and resolution remain restricted to maintenance staff."
        tk.Label(self.content, text=note, wraplength=900, justify="left", fg="#cbd5f5", bg="#0f172a").pack(padx=20, pady=(0, 12))

        form = tk.Frame(self.content, bg="#1e293b")
        form.pack(fill="x", padx=20, pady=10)
        self.maint_tenant_id = self.field(form, "Tenant ID / NI")
        self.maint_apartment_id = self.field(form, "Apartment ID (optional)")
        self.maint_description = self.field(form, "Description")

        priority_frame = tk.Frame(form, bg="#1e293b")
        priority_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(priority_frame, text="Priority", width=20, bg="#1e293b", fg="#cbd5f5").pack(side="left")
        self.maint_priority = ttk.Combobox(priority_frame, values=["LOW", "MEDIUM", "HIGH"], state="readonly")
        self.maint_priority.pack(side="left", fill="x", expand=True)
        self.maint_priority.set("LOW")

        button_row = tk.Frame(form, bg="#1e293b")
        button_row.pack(pady=10)
        tk.Button(button_row, text="Create Request", bg="#22c55e", command=self.create_maintenance_request).pack(side="left", padx=5)
        tk.Button(button_row, text="View Tenant Requests", bg="#3b82f6", command=self.load_maintenance_requests).pack(side="left", padx=5)
        tk.Button(button_row, text="Clear", bg="#64748b", command=self.clear_maintenance_form).pack(side="left", padx=5)

        table_frame = tk.Frame(self.content)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        columns = ("Request ID", "Tenant ID", "Apartment ID", "Description", "Priority", "Status", "Reported Date", "Resolved Date", "Cost")
        self.maintenance_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.maintenance_tree.heading(col, text=col)
            self.maintenance_tree.column(col, anchor="center", width=130)
        self.maintenance_tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.maintenance_tree.yview)
        self.maintenance_tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")

    def create_maintenance_request(self):
        try:
            tenant_id = self._resolve_tenant_identifier(self.maint_tenant_id.get())
            apartment_text = self.maint_apartment_id.get().strip()

            if apartment_text:
                apartment_id = int(apartment_text)
            else:
                apartment_id = self._get_active_apartment_id(tenant_id)

            if not apartment_id:
                raise ValueError("No active apartment found for this tenant. Enter an apartment ID manually.")

            request_id = MaintenanceController.CreateRequest(
                tenant_id,
                int(apartment_id),
                self.maint_description.get().strip(),
                self.maint_priority.get().strip(),
            )
            messagebox.showinfo("Success", f"Maintenance request created.\nRequest ID: {request_id}")
            self.load_maintenance_requests()
            self.clear_maintenance_form()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_maintenance_requests(self):
        try:
            tenant_id = self._resolve_tenant_identifier(self.maint_tenant_id.get())
            rows = MaintenanceController.ViewRequestsByTenant(tenant_id)
            self.maintenance_tree.delete(*self.maintenance_tree.get_children())
            for row in rows:
                reduced = (row[0], row[1], row[2], row[3], row[4], row[5], row[11], row[12], row[13])
                self.maintenance_tree.insert("", "end", values=reduced)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear_maintenance_form(self):
        for field in [self.maint_tenant_id, self.maint_apartment_id, self.maint_description]:
            field.delete(0, tk.END)
        self.maint_priority.set("LOW")
        self._safe_clear_tree("maintenance_tree")

    # ============================================================
    # COMPLAINTS
    # ============================================================
    def show_complaints(self):
        self.clear_content()
        tk.Label(self.content, text="Complaint Registration", fg="white", bg="#0f172a", font=("Arial", 20, "bold")).pack(pady=10)
        note = "Front-desk staff can register and track complaints. Complaint closure is handled by admin/management."
        tk.Label(self.content, text=note, wraplength=900, justify="left", fg="#cbd5f5", bg="#0f172a").pack(padx=20, pady=(0, 12))

        form = tk.Frame(self.content, bg="#1e293b")
        form.pack(fill="x", padx=20, pady=10)
        self.complaint_ni = self.field(form, "Tenant NI / ID")
        self.complaint_description = self.field(form, "Complaint Description")

        button_row = tk.Frame(form, bg="#1e293b")
        button_row.pack(pady=10)
        tk.Button(button_row, text="Add Complaint", bg="#22c55e", command=self.add_complaint).pack(side="left", padx=5)
        tk.Button(button_row, text="Track Tenant Complaints", bg="#3b82f6", command=self.load_complaints).pack(side="left", padx=5)
        tk.Button(button_row, text="Clear", bg="#64748b", command=self.clear_complaint_form).pack(side="left", padx=5)

        table_frame = tk.Frame(self.content)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        columns = ("Complaint ID", "Tenant ID", "Description", "Status", "Created At")
        self.complaint_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.complaint_tree.heading(col, text=col)
            self.complaint_tree.column(col, anchor="center", width=180)
        self.complaint_tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.complaint_tree.yview)
        self.complaint_tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")

    def add_complaint(self):
        try:
            description = self.complaint_description.get().strip()
            if not description:
                raise ValueError("Complaint description is required.")

            tenant_id = self._resolve_tenant_identifier(self.complaint_ni.get())
            apartment_id = self._get_active_apartment_id(tenant_id)
            if not apartment_id:
                raise ValueError("No active apartment found for this tenant.")

            ComplaintController.CreateComplaint(tenant_id, apartment_id, description)

            messagebox.showinfo("Success", "Complaint added successfully")
            self.load_complaints()
            self.clear_complaint_form()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_complaints(self):
        try:
            tenant_id = self._resolve_tenant_identifier(self.complaint_ni.get())
            rows = self._get_complaints_by_tenant(tenant_id)
            self.complaint_tree.delete(*self.complaint_tree.get_children())
            for row in rows:
                # complaint_id, tenant_id, apartment_id, description, status, created_at
                reduced = (row[0], row[1], row[3], row[4], row[5]) if len(row) > 5 else row
                self.complaint_tree.insert("", "end", values=reduced)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear_complaint_form(self):
        for field in [self.complaint_ni, self.complaint_description]:
            field.delete(0, tk.END)
        self._safe_clear_tree("complaint_tree")

    def logout(self):
        self.window.destroy()
        self.parent.deiconify()
