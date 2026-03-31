"""
AdminUI — Admin / Manager Dashboard  (Cem's Module)

Tabs:
  1. Dashboard    — role-scoped occupancy, rent, maintenance, complaint cards
  2. Tenants      — add / edit (inline pre-fill) / view (scoped) / deactivate
  3. Leases       — create / standard terminate / early terminate (notice + penalty)
  4. Apartments   — add / view (scoped) / change status
  5. Invoices     — full payment history with PAID/PENDING/OVERDUE colour coding
  6. Complaints   — view (scoped) / close
  7. Staff        — create / view (scoped) / deactivate (soft-delete)
  8. Locations    — view / add  (Manager only)

RBAC rules (enforced via AdminController):
  ADMIN   → all data scoped to own location_id
  MANAGER → full system view + Locations tab
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from source.app.controllers.AdminController import AdminController

# ── Colour palette ────────────────────────────────────────────────────
BG       = "#0f172a"
BG_CARD  = "#1e293b"
FG       = "#e2e8f0"
ACCENT   = "#0ea5e9"
ACCENT2  = "#38bdf8"
BORDER   = "#334155"
INPUT_BG = "#020617"
RED      = "#ef4444"
GREEN    = "#22c55e"
YELLOW   = "#f59e0b"


class AdminUI(tk.Frame):

    def __init__(self, parent, user_data: dict):
        super().__init__(parent, bg=BG)
        self.parent   = parent
        self.user     = user_data
        self.role     = user_data["role"]
        self.loc_id   = user_data["location_id"]
        self.pack(fill="both", expand=True)

        parent.title(f"PAMS — {self.role} Dashboard  ({user_data['username']})")
        parent.geometry("1450x860")
        parent.configure(bg=BG)

        self._build_tabs()

    # ══════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════
    def _R(self):
        """Shorthand: returns (role, location_id) for all controller calls."""
        return self.role, self.loc_id

    def _label(self, parent, text, **kw):
        return tk.Label(parent, text=text, bg=BG, fg=FG,
                        font=kw.pop("font", ("Segoe UI", 11)), **kw)

    def _heading(self, parent, text):
        return tk.Label(parent, text=text, bg=BG, fg=ACCENT,
                        font=("Segoe UI", 16, "bold"))

    def _entry(self, parent, width=25):
        return tk.Entry(parent, bg=INPUT_BG, fg="white",
                        insertbackground="white", relief="flat",
                        font=("Segoe UI", 11), width=width)

    def _button(self, parent, text, command, color=ACCENT):
        fg = "#020617" if color not in (RED, YELLOW) else "white"
        btn = tk.Button(parent, text=text, command=command,
                        bg=color, fg=fg,
                        font=("Segoe UI", 10, "bold"),
                        relief="flat", cursor="hand2", padx=14, pady=6)
        hover = ACCENT2 if color == ACCENT else ("#dc2626" if color == RED else "#d97706")
        btn.bind("<Enter>", lambda e: btn.config(bg=hover))
        btn.bind("<Leave>", lambda e: btn.config(bg=color))
        return btn

    def _treeview(self, parent, columns, widths=None):
        frame = tk.Frame(parent, bg=BG)
        tree  = ttk.Treeview(frame, columns=columns, show="headings", height=16)
        for i, col in enumerate(columns):
            w = widths[i] if widths else 120
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        s = ttk.Style()
        s.configure("Treeview", background=BG_CARD, foreground=FG,
                    fieldbackground=BG_CARD, rowheight=26,
                    font=("Segoe UI", 10))
        s.configure("Treeview.Heading", background=BORDER, foreground=FG,
                    font=("Segoe UI", 10, "bold"))
        s.map("Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", "#020617")])
        return frame, tree

    # ══════════════════════════════════════════════════════
    #  NOTEBOOK
    # ══════════════════════════════════════════════════════
    def _build_tabs(self):
        s = ttk.Style()
        s.theme_use("default")
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=BG_CARD, foreground=FG,
                    padding=[16, 8], font=("Segoe UI", 10, "bold"))
        s.map("TNotebook.Tab",
              background=[("selected", ACCENT)],
              foreground=[("selected", "#020617")])

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        tabs = {
            "dashboard":  tk.Frame(nb, bg=BG),
            "tenants":    tk.Frame(nb, bg=BG),
            "leases":     tk.Frame(nb, bg=BG),
            "apartments": tk.Frame(nb, bg=BG),
            "invoices":   tk.Frame(nb, bg=BG),
            "complaints": tk.Frame(nb, bg=BG),
            "staff":      tk.Frame(nb, bg=BG),
        }
        nb.add(tabs["dashboard"],  text="  Dashboard  ")
        nb.add(tabs["tenants"],    text="  Tenants  ")
        nb.add(tabs["leases"],     text="  Leases  ")
        nb.add(tabs["apartments"], text="  Apartments  ")
        nb.add(tabs["invoices"],   text="  Invoices  ")
        nb.add(tabs["complaints"], text="  Complaints  ")
        nb.add(tabs["staff"],      text="  Staff  ")

        if self.role == "MANAGER":
            tabs["locations"] = tk.Frame(nb, bg=BG)
            nb.add(tabs["locations"], text="  Locations  ")

        self._build_dashboard(tabs["dashboard"])
        self._build_tenants(tabs["tenants"])
        self._build_leases(tabs["leases"])
        self._build_apartments(tabs["apartments"])
        self._build_invoices(tabs["invoices"])
        self._build_complaints(tabs["complaints"])
        self._build_staff(tabs["staff"])
        if self.role == "MANAGER":
            self._build_locations(tabs["locations"])

    # ══════════════════════════════════════════════════════
    #  1)  DASHBOARD
    # ══════════════════════════════════════════════════════
    def _build_dashboard(self, tab):
        scope = "Your Location" if self.role == "ADMIN" else "All Locations"
        self._heading(tab, f"Dashboard  ({scope})").pack(anchor="w", padx=20, pady=(15, 4))

        cards_frame = tk.Frame(tab, bg=BG)
        cards_frame.pack(fill="x", padx=20, pady=8)

        self._dash = {}
        card_defs = [
            ("Total Apartments",   "total"),
            ("Occupied",           "occupied"),
            ("Available",          "available"),
            ("Under Maintenance",  "maint_apt"),
            ("Collected Rent",     "collected"),
            ("Pending Rent",       "pending"),
            ("Open Issues",        "open_issues"),
            ("Avg Resolve (days)", "avg_resolve"),
            ("Maintenance Cost",   "maint_cost"),
            ("Resolved Requests",  "resolved"),
            ("Open Complaints",    "comp_open"),
            ("Closed Complaints",  "comp_closed"),
        ]
        for i, (title, key) in enumerate(card_defs):
            c = tk.Frame(cards_frame, bg=BG_CARD, padx=16, pady=10)
            c.grid(row=i // 4, column=i % 4, padx=6, pady=6, sticky="nsew")
            cards_frame.columnconfigure(i % 4, weight=1)
            tk.Label(c, text=title, bg=BG_CARD, fg="#94a3b8",
                     font=("Segoe UI", 9)).pack(anchor="w")
            lbl = tk.Label(c, text="—", bg=BG_CARD, fg="white",
                           font=("Segoe UI", 18, "bold"))
            lbl.pack(anchor="w")
            self._dash[key] = lbl

        # Occupancy by location table
        self._heading(tab, "Occupancy by Location").pack(anchor="w", padx=20, pady=(12, 4))
        cols = ("City", "Total", "Occupied", "Available", "Maintenance")
        self._dash_loc_frame, self._dash_loc_tree = self._treeview(tab, cols, [200, 90, 90, 90, 110])
        self._dash_loc_frame.pack(fill="both", expand=True, padx=20, pady=4)

        self._button(tab, "⟳  Refresh Dashboard", self._refresh_dashboard).pack(pady=10)
        self._refresh_dashboard()

    def _refresh_dashboard(self):
        try:
            r, lid = self._R()

            # Occupancy cards
            occ = AdminController.GetOccupancySummary(r, lid)
            if occ:
                self._dash["total"].config(   text=str(occ[0] or 0))
                self._dash["occupied"].config( text=str(occ[1] or 0))
                self._dash["available"].config(text=str(occ[2] or 0))
                self._dash["maint_apt"].config(text=str(occ[3] or 0))

            # Rent cards
            rent = AdminController.GetCollectedVsPendingRent(r, lid)
            if rent:
                self._dash["collected"].config(text=f"£{rent[0]:,.2f}")
                self._dash["pending"].config(  text=f"£{rent[1]:,.2f}")

            # Maintenance summary cards
            ms = AdminController.GetMaintenanceSummary(r, lid)
            if ms:
                self._dash["open_issues"].config( text=str(ms[0] or 0))
                self._dash["resolved"].config(    text=str(ms[1] or 0))
                self._dash["maint_cost"].config(  text=f"£{ms[2]:,.2f}")
                self._dash["avg_resolve"].config( text=str(ms[3] or "N/A"))

            # Complaints summary cards
            comp_rows = AdminController.GetComplaintsSummary(r, lid)
            comp = {row[0]: row[1] for row in comp_rows} if comp_rows else {}
            self._dash["comp_open"].config(  text=str(comp.get("OPEN",   0)))
            self._dash["comp_closed"].config(text=str(comp.get("CLOSED", 0)))

            # Occupancy by location table
            self._dash_loc_tree.delete(*self._dash_loc_tree.get_children())
            for row in AdminController.GetOccupancyByLocation(r, lid):
                self._dash_loc_tree.insert("", "end", values=row)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ══════════════════════════════════════════════════════
    #  2)  TENANTS
    # ══════════════════════════════════════════════════════
    def _build_tenants(self, tab):
        self._heading(tab, "Tenant Management").pack(anchor="w", padx=20, pady=(15, 4))

        # ── Add Tenant form ──────────────────────────────
        add_frame = tk.LabelFrame(tab, text=" Add New Tenant ", bg=BG, fg=ACCENT,
                                  font=("Segoe UI", 9, "bold"), padx=10, pady=8)
        add_frame.pack(fill="x", padx=20, pady=(4, 2))

        add_fields = ["NI Number", "First Name", "Last Name", "Phone", "Email", "Occupation", "Reference"]
        self._ten_e = {}
        for i, f in enumerate(add_fields):
            tk.Label(add_frame, text=f, bg=BG, fg=FG,
                     font=("Segoe UI", 9)).grid(row=0, column=i, padx=4)
            e = self._entry(add_frame, width=13)
            e.grid(row=1, column=i, padx=4, pady=4)
            self._ten_e[f] = e
        self._button(add_frame, "Add Tenant", self._add_tenant).grid(row=1, column=len(add_fields), padx=8)

        # ── Edit Tenant form (pre-filled on row select) ──
        edit_frame = tk.LabelFrame(tab, text=" Edit Selected Tenant ", bg=BG, fg=YELLOW,
                                   font=("Segoe UI", 9, "bold"), padx=10, pady=8)
        edit_frame.pack(fill="x", padx=20, pady=(2, 4))

        edit_fields = ["Phone", "Email", "Occupation", "Reference"]
        self._ten_edit = {}
        for i, f in enumerate(edit_fields):
            tk.Label(edit_frame, text=f, bg=BG, fg=FG,
                     font=("Segoe UI", 9)).grid(row=0, column=i, padx=4)
            e = self._entry(edit_frame, width=20)
            e.grid(row=1, column=i, padx=4, pady=4)
            self._ten_edit[f] = e
        self._button(edit_frame, "Save Changes", self._update_tenant, YELLOW).grid(
            row=1, column=len(edit_fields), padx=8)
        tk.Label(edit_frame, text="← Select a row above to pre-fill",
                 bg=BG, fg="#64748b", font=("Segoe UI", 8, "italic")).grid(
            row=2, column=0, columnspan=5, pady=2, sticky="w")

        # ── Treeview ─────────────────────────────────────
        cols = ("ID", "NI", "First", "Last", "Phone", "Email", "Occupation", "Reference", "Created")
        w    = [50, 100, 90, 90, 110, 160, 90, 120, 130]
        self._ten_frame, self._ten_tree = self._treeview(tab, cols, w)
        self._ten_frame.pack(fill="both", expand=True, padx=20, pady=4)
        self._ten_tree.bind("<<TreeviewSelect>>", self._on_tenant_select)

        row = tk.Frame(tab, bg=BG)
        row.pack(pady=8)
        self._button(row, "⟳ Refresh",           self._refresh_tenants).pack(side="left", padx=5)
        self._button(row, "Deactivate Selected",  self._deactivate_tenant, RED).pack(side="left", padx=5)

        self._refresh_tenants()

    def _on_tenant_select(self, event):
        """Pre-fill the edit form when a tenant row is selected."""
        sel = self._ten_tree.selection()
        if not sel:
            return
        vals = self._ten_tree.item(sel[0])["values"]
        # cols: ID(0) NI(1) First(2) Last(3) Phone(4) Email(5) Occupation(6) Reference(7) Created(8)
        for key, idx in [("Phone", 4), ("Email", 5), ("Occupation", 6), ("Reference", 7)]:
            self._ten_edit[key].delete(0, "end")
            self._ten_edit[key].insert(0, vals[idx] if vals[idx] else "")

    def _add_tenant(self):
        e = self._ten_e
        try:
            AdminController.AddTenant(
                e["NI Number"].get().strip(),
                e["First Name"].get().strip(),
                e["Last Name"].get().strip(),
                e["Phone"].get().strip(),
                e["Email"].get().strip(),
                e["Occupation"].get().strip() or None,
                e["Reference"].get().strip()  or None
            )
            messagebox.showinfo("Success", "Tenant added.")
            for ent in e.values(): ent.delete(0, "end")
            self._refresh_tenants()
        except Exception as err:
            messagebox.showerror("Error", str(err))

    def _update_tenant(self):
        sel = self._ten_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a tenant first.")
            return
        tid = self._ten_tree.item(sel[0])["values"][0]
        e = self._ten_edit
        try:
            AdminController.UpdateTenant(
                tid,
                e["Phone"].get().strip(),
                e["Email"].get().strip(),
                e["Occupation"].get().strip() or None,
                e["Reference"].get().strip()  or None
            )
            messagebox.showinfo("Success", f"Tenant #{tid} updated.")
            self._refresh_tenants()
        except Exception as err:
            messagebox.showerror("Error", str(err))

    def _refresh_tenants(self):
        self._ten_tree.delete(*self._ten_tree.get_children())
        try:
            for r in AdminController.GetTenants(*self._R()):
                self._ten_tree.insert("", "end", values=r)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _deactivate_tenant(self):
        sel = self._ten_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a tenant first.")
            return
        tid = self._ten_tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirm",
                f"Deactivate tenant #{tid}?\n\n"
                "They will be hidden from all views, but their records are preserved."):
            try:
                AdminController.DeactivateTenant(tid)
                self._refresh_tenants()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ══════════════════════════════════════════════════════
    #  3)  LEASES
    # ══════════════════════════════════════════════════════
    def _build_leases(self, tab):
        self._heading(tab, "Lease Management").pack(anchor="w", padx=20, pady=(15, 4))

        form = tk.Frame(tab, bg=BG_CARD, padx=14, pady=10)
        form.pack(fill="x", padx=20, pady=6)

        fields = ["Tenant ID", "Apartment ID", "Start Date\n(YYYY-MM-DD)",
                  "End Date\n(YYYY-MM-DD)", "Deposit", "Monthly Rent",
                  "First Due Date\n(YYYY-MM-DD)"]
        self._lea_e = {}
        for i, f in enumerate(fields):
            tk.Label(form, text=f, bg=BG_CARD, fg=FG,
                     font=("Segoe UI", 9), justify="center").grid(row=0, column=i, padx=4)
            e = self._entry(form, width=13)
            e.grid(row=1, column=i, padx=4, pady=4)
            self._lea_e[f] = e

        self._button(form, "Create Lease", self._create_lease).grid(row=1, column=len(fields), padx=8)

        cols = ("ID", "Tenant", "NI", "Apartment", "City", "Start", "End", "Rent", "Deposit", "Status")
        w    = [50, 120, 100, 90, 90, 100, 100, 80, 80, 90]
        self._lea_frame, self._lea_tree = self._treeview(tab, cols, w)
        self._lea_frame.pack(fill="both", expand=True, padx=20, pady=4)

        row = tk.Frame(tab, bg=BG)
        row.pack(pady=8)
        self._button(row, "⟳ Refresh",           self._refresh_leases).pack(side="left", padx=5)
        self._button(row, "Standard Terminate",   self._terminate_lease, YELLOW).pack(side="left", padx=5)
        self._button(row, "Early Terminate",       self._early_terminate_lease, RED).pack(side="left", padx=5)

        self._refresh_leases()

    def _create_lease(self):
        e = self._lea_e
        try:
            AdminController.CreateLease(
                int(e["Tenant ID"].get()),
                int(e["Apartment ID"].get()),
                e["Start Date\n(YYYY-MM-DD)"].get().strip(),
                e["End Date\n(YYYY-MM-DD)"].get().strip(),
                float(e["Deposit"].get()),
                float(e["Monthly Rent"].get()),
                e["First Due Date\n(YYYY-MM-DD)"].get().strip()
            )
            messagebox.showinfo("Success", "Lease created with initial invoice.")
            for ent in e.values(): ent.delete(0, "end")
            self._refresh_leases()
        except Exception as err:
            messagebox.showerror("Error", str(err))

    def _refresh_leases(self):
        self._lea_tree.delete(*self._lea_tree.get_children())
        try:
            for r in AdminController.GetLeases(*self._R()):
                self._lea_tree.insert("", "end", values=r)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _terminate_lease(self):
        """Standard termination — lease reached natural end, no penalty."""
        sel = self._lea_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a lease first.")
            return
        lid = self._lea_tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirm",
                f"Standard terminate lease #{lid}?\n"
                "Use this only when the lease has reached its natural end date.\n"
                "No penalty will be applied."):
            try:
                AdminController.TerminateLease(lid, *self._R())
                messagebox.showinfo("Done", "Lease terminated. Apartment set to AVAILABLE.")
                self._refresh_leases()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _early_terminate_lease(self):
        """Early termination — 1-month notice required, 5% penalty invoice created."""
        sel = self._lea_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a lease first.")
            return
        lid = self._lea_tree.item(sel[0])["values"][0]

        notice_date = simpledialog.askstring(
            "Early Termination — Notice Date",
            "Enter the date the tenant gave notice (YYYY-MM-DD):\n\n"
            "Note: At least 30 days must have passed since notice was given.",
            parent=self.parent
        )
        if not notice_date:
            return

        try:
            result = AdminController.TerminateLeaseEarly(lid, notice_date.strip(), *self._R())
            if result["is_early"]:
                messagebox.showinfo(
                    "Terminated — Early",
                    f"Lease #{lid} terminated early.\n\n"
                    f"Penalty charged:  £{result['penalty_amount']:.2f}\n"
                    f"Penalty invoice:  #{result['penalty_invoice_id']}\n\n"
                    "Apartment is now AVAILABLE."
                )
            else:
                messagebox.showinfo(
                    "Terminated",
                    f"Lease #{lid} terminated (no early penalty — end date already passed).\n"
                    "Apartment is now AVAILABLE."
                )
            self._refresh_leases()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ══════════════════════════════════════════════════════
    #  4)  APARTMENTS
    # ══════════════════════════════════════════════════════
    def _build_apartments(self, tab):
        self._heading(tab, "Apartment Management").pack(anchor="w", padx=20, pady=(15, 4))

        form = tk.Frame(tab, bg=BG_CARD, padx=14, pady=10)
        form.pack(fill="x", padx=20, pady=6)

        fields = ["Location ID", "Apartment No.", "Type", "Rooms", "Monthly Rent"]
        self._apt_e = {}
        for i, f in enumerate(fields):
            tk.Label(form, text=f, bg=BG_CARD, fg=FG,
                     font=("Segoe UI", 9)).grid(row=0, column=i, padx=4)
            e = self._entry(form, width=14)
            e.grid(row=1, column=i, padx=4, pady=4)
            self._apt_e[f] = e

        self._button(form, "Add Apartment", self._add_apartment).grid(row=1, column=len(fields), padx=8)

        cols = ("ID", "Apt Number", "Type", "Rooms", "Rent", "Status", "City")
        w    = [60, 110, 90, 70, 90, 110, 120]
        self._apt_frame, self._apt_tree = self._treeview(tab, cols, w)
        self._apt_frame.pack(fill="both", expand=True, padx=20, pady=4)

        row = tk.Frame(tab, bg=BG)
        row.pack(pady=8)
        self._button(row, "⟳ Refresh",        self._refresh_apartments).pack(side="left", padx=4)
        self._button(row, "Set AVAILABLE",    lambda: self._set_apt_status("AVAILABLE"), GREEN).pack(side="left", padx=4)
        self._button(row, "Set MAINTENANCE",  lambda: self._set_apt_status("MAINTENANCE"), YELLOW).pack(side="left", padx=4)

        self._refresh_apartments()

    def _add_apartment(self):
        e = self._apt_e
        try:
            AdminController.CreateApartment(
                int(e["Location ID"].get()),
                e["Apartment No."].get().strip(),
                e["Type"].get().strip(),
                int(e["Rooms"].get()),
                float(e["Monthly Rent"].get())
            )
            messagebox.showinfo("Success", "Apartment added.")
            for ent in e.values(): ent.delete(0, "end")
            self._refresh_apartments()
        except Exception as err:
            messagebox.showerror("Error", str(err))

    def _refresh_apartments(self):
        self._apt_tree.delete(*self._apt_tree.get_children())
        try:
            for r in AdminController.GetApartments(*self._R()):
                self._apt_tree.insert("", "end", values=r)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _set_apt_status(self, status):
        sel = self._apt_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select an apartment first.")
            return
        aid = self._apt_tree.item(sel[0])["values"][0]
        try:
            AdminController.UpdateApartmentStatus(aid, status, *self._R())
            self._refresh_apartments()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ══════════════════════════════════════════════════════
    #  5)  INVOICES  (payment history & billing overview)
    # ══════════════════════════════════════════════════════
    def _build_invoices(self, tab):
        scope = "Your Location" if self.role == "ADMIN" else "All Locations"
        self._heading(tab, f"Invoice & Payment History  ({scope})").pack(
            anchor="w", padx=20, pady=(15, 4))

        # Summary strip
        sum_frame = tk.Frame(tab, bg=BG)
        sum_frame.pack(fill="x", padx=20, pady=(0, 6))
        self._inv_summary = {}
        for i, (label, key) in enumerate([
                ("Total Invoices", "total"),
                ("Paid",           "paid"),
                ("Pending",        "pending"),
                ("Overdue",        "overdue"),
        ]):
            c = tk.Frame(sum_frame, bg=BG_CARD, padx=14, pady=8)
            c.grid(row=0, column=i, padx=6, sticky="nsew")
            sum_frame.columnconfigure(i, weight=1)
            tk.Label(c, text=label, bg=BG_CARD, fg="#94a3b8",
                     font=("Segoe UI", 9)).pack(anchor="w")
            lbl = tk.Label(c, text="—", bg=BG_CARD, fg="white",
                           font=("Segoe UI", 16, "bold"))
            lbl.pack(anchor="w")
            self._inv_summary[key] = lbl

        cols = ("ID", "Tenant", "Apartment", "City", "Due Date", "Amount (£)", "Status")
        w    = [60, 160, 100, 100, 110, 100, 90]
        self._inv_frame, self._inv_tree = self._treeview(tab, cols, w)
        self._inv_frame.pack(fill="both", expand=True, padx=20, pady=4)

        # Tag colours: overdue = red tint, paid = green tint
        self._inv_tree.tag_configure("OVERDUE", foreground="#fca5a5")
        self._inv_tree.tag_configure("PAID",    foreground="#86efac")

        self._button(tab, "⟳ Refresh", self._refresh_invoices).pack(pady=8)
        self._refresh_invoices()

    def _refresh_invoices(self):
        self._inv_tree.delete(*self._inv_tree.get_children())
        try:
            rows = AdminController.GetAllInvoices(*self._R())
            counts = {"total": len(rows), "paid": 0, "pending": 0, "overdue": 0}
            for r in rows:
                status = r[6]
                tag    = status  # "PAID", "OVERDUE", or "PENDING"
                self._inv_tree.insert("", "end", values=r, tags=(tag,))
                if status == "PAID":    counts["paid"]    += 1
                elif status == "OVERDUE": counts["overdue"] += 1
                else:                   counts["pending"]  += 1
            self._inv_summary["total"].config(  text=str(counts["total"]))
            self._inv_summary["paid"].config(   text=str(counts["paid"]),    fg=GREEN)
            self._inv_summary["pending"].config(text=str(counts["pending"]), fg=YELLOW)
            self._inv_summary["overdue"].config(text=str(counts["overdue"]), fg=RED)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ══════════════════════════════════════════════════════
    #  6)  COMPLAINTS
    # ══════════════════════════════════════════════════════
    def _build_complaints(self, tab):
        scope = "Your Location" if self.role == "ADMIN" else "All Locations"
        self._heading(tab, f"Complaint Management  ({scope})").pack(anchor="w", padx=20, pady=(15, 4))

        cols = ("ID", "Tenant", "NI", "Description", "Status", "Created", "City")
        w    = [50, 130, 100, 310, 80, 150, 100]
        self._comp_frame, self._comp_tree = self._treeview(tab, cols, w)
        self._comp_frame.pack(fill="both", expand=True, padx=20, pady=10)

        row = tk.Frame(tab, bg=BG)
        row.pack(pady=8)
        self._button(row, "⟳ Refresh",      self._refresh_complaints).pack(side="left", padx=5)
        self._button(row, "Close Selected", self._close_complaint, RED).pack(side="left", padx=5)

        self._refresh_complaints()

    def _refresh_complaints(self):
        self._comp_tree.delete(*self._comp_tree.get_children())
        try:
            for r in AdminController.GetComplaints(*self._R()):
                self._comp_tree.insert("", "end", values=r)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _close_complaint(self):
        sel = self._comp_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a complaint first.")
            return
        cid = self._comp_tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirm", f"Close complaint #{cid}?"):
            try:
                AdminController.CloseComplaint(cid, *self._R())
                self._refresh_complaints()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ══════════════════════════════════════════════════════
    #  7)  STAFF
    # ══════════════════════════════════════════════════════
    def _build_staff(self, tab):
        scope = "Your Location" if self.role == "ADMIN" else "All Locations"
        self._heading(tab, f"Staff Account Management  ({scope})").pack(anchor="w", padx=20, pady=(15, 4))

        form = tk.Frame(tab, bg=BG_CARD, padx=14, pady=10)
        form.pack(fill="x", padx=20, pady=6)

        fields = ["Username", "Password", "Role", "Location ID"]
        self._sta_e = {}
        for i, f in enumerate(fields):
            tk.Label(form, text=f, bg=BG_CARD, fg=FG,
                     font=("Segoe UI", 9)).grid(row=0, column=i, padx=6)
            e = self._entry(form, width=16)
            e.grid(row=1, column=i, padx=6, pady=4)
            self._sta_e[f] = e

        # ADMIN: lock Location ID to their own location so they can't create
        # staff for a different location (enforced server-side too, but this
        # gives immediate feedback in the UI).
        if self.role == "ADMIN":
            self._sta_e["Location ID"].insert(0, str(self.loc_id))
            self._sta_e["Location ID"].config(state="disabled")
            tk.Label(form, text="(your location)", bg=BG_CARD, fg="#94a3b8",
                     font=("Segoe UI", 8)).grid(row=2, column=3)

        self._button(form, "Create Account", self._create_staff).grid(row=1, column=len(fields), padx=8)

        cols = ("ID", "Username", "Role", "City")
        w    = [60, 180, 140, 150]
        self._sta_frame, self._sta_tree = self._treeview(tab, cols, w)
        self._sta_frame.pack(fill="both", expand=True, padx=20, pady=4)

        row = tk.Frame(tab, bg=BG)
        row.pack(pady=8)
        self._button(row, "⟳ Refresh",          self._refresh_staff).pack(side="left", padx=5)
        self._button(row, "Deactivate Selected", self._deactivate_staff, RED).pack(side="left", padx=5)

        self._refresh_staff()

    def _create_staff(self):
        e = self._sta_e
        try:
            AdminController.CreateStaffAccount(
                e["Username"].get().strip(),
                e["Password"].get().strip(),
                e["Role"].get().strip().upper(),
                int(e["Location ID"].get()),
                *self._R()   # CallerRole, CallerLocationId
            )
            messagebox.showinfo("Success", "Staff account created.")
            for ent in e.values(): ent.delete(0, "end")
            self._refresh_staff()
        except Exception as err:
            messagebox.showerror("Error", str(err))

    def _refresh_staff(self):
        self._sta_tree.delete(*self._sta_tree.get_children())
        try:
            for r in AdminController.GetStaff(*self._R()):
                self._sta_tree.insert("", "end", values=r)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _deactivate_staff(self):
        sel = self._sta_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a staff member first.")
            return
        uid = self._sta_tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirm",
                f"Deactivate user #{uid}?\n\n"
                "They will no longer be able to log in, but their records are preserved."):
            try:
                AdminController.DeactivateStaff(uid, *self._R())
                self._refresh_staff()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ══════════════════════════════════════════════════════
    #  8)  LOCATIONS  (Manager only)
    # ══════════════════════════════════════════════════════
    def _build_locations(self, tab):
        self._heading(tab, "Location Management  (Manager Only)").pack(anchor="w", padx=20, pady=(15, 4))

        form = tk.Frame(tab, bg=BG_CARD, padx=14, pady=10)
        form.pack(fill="x", padx=20, pady=6)

        tk.Label(form, text="City Name", bg=BG_CARD, fg=FG,
                 font=("Segoe UI", 10)).pack(side="left", padx=6)
        self._loc_entry = self._entry(form, width=22)
        self._loc_entry.pack(side="left", padx=6)
        self._button(form, "Add Location", self._add_location).pack(side="left", padx=8)

        cols = ("ID", "City")
        w    = [80, 300]
        self._loc_frame, self._loc_tree = self._treeview(tab, cols, w)
        self._loc_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self._button(tab, "⟳ Refresh", self._refresh_locations).pack(pady=8)
        self._refresh_locations()

    def _add_location(self):
        city = self._loc_entry.get().strip()
        if not city:
            return
        try:
            AdminController.AddLocation(city)
            messagebox.showinfo("Success", f"Location '{city}' added.")
            self._loc_entry.delete(0, "end")
            self._refresh_locations()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _refresh_locations(self):
        self._loc_tree.delete(*self._loc_tree.get_children())
        try:
            for r in AdminController.GetAllLocations():
                self._loc_tree.insert("", "end", values=r)
        except Exception as e:
            messagebox.showerror("Error", str(e))
