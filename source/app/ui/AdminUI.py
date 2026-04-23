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

import datetime
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

TYPE_ROOM_MAP = {
    "Studio": 1,
    "1 Bedroom": 1,
    "2 Bedroom": 2,
    "3 Bedroom": 3,
    "4 Bedroom": 4,
    "Penthouse": 4,
}


class AdminUI(tk.Toplevel):

    def __init__(self, parent, user_data: dict):
        super().__init__(parent)
        self.parent = parent
        self.user   = user_data
        self.role   = user_data["role"]
        self.loc_id = user_data["location_id"]

        self.title(f"PAMS — {self.role} Dashboard ({user_data['username']})")
        self.geometry("1450x860")
        self.configure(bg=BG)

        self.protocol("WM_DELETE_WINDOW", self.close)

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

    def _load_location_options(self):
        """Returns [(location_id, city), ...] for location dropdowns."""
        try:
            rows = AdminController.GetAllLocations()
        except Exception:
            rows = []
        options = []
        for row in rows:
            try:
                options.append((int(row[0]), str(row[1])))
            except Exception:
                continue
        return options

    def _set_location_combobox_values(self, combo):
        options = self._load_location_options()
        display = [f"{loc_id} - {city}" for loc_id, city in options]
        combo["values"] = display
        return options

    def _parse_location_choice(self, value: str):
        if not value:
            return None
        try:
            return int(str(value).split(" - ", 1)[0])
        except Exception:
            return None


    def _scope_text(self):
        if self.role == "MANAGER":
            return "All Locations"
        try:
            for loc_id, city in self._load_location_options():
                if int(loc_id) == int(self.loc_id):
                    return city
        except Exception:
            pass
        return f"Location {self.loc_id}"

    def _on_apartment_type_selected(self, _event=None):
        selected = self._apt_type_combo.get().strip() if hasattr(self, "_apt_type_combo") else ""
        if not selected:
            return
        rooms = TYPE_ROOM_MAP.get(selected)
        if rooms is not None and "Rooms" in self._apt_e:
            self._apt_e["Rooms"].delete(0, "end")
            self._apt_e["Rooms"].insert(0, str(rooms))

    def _expected_apartment_prefix(self, location_id: int):
        try:
            for loc_id, city in self._load_location_options():
                if int(loc_id) == int(location_id) and city:
                    return str(city).strip()[0].upper()
        except Exception:
            pass
        return None
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

        topbar = tk.Frame(self, bg=BG)
        topbar.pack(fill="x", padx=12, pady=(10, 0))
        tk.Label(topbar,
                 text=f"{self.role.title()} Scope: {self._scope_text()}",
                 bg=BG, fg="#94a3b8", font=("Segoe UI", 10, "bold")).pack(side="left")
        self._button(topbar, "Logout", self.close, RED).pack(side="right")

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
                self._dash["total"].config(   text=str(occ.get("total_apartments", 0)))
                self._dash["occupied"].config(text=str(occ.get("occupied_count", 0)))
                self._dash["available"].config(text=str(occ.get("available_count", 0)))
                self._dash["maint_apt"].config(text=str(occ.get("maintenance_count", 0)))

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

        # ── Search / Filter row ─────────────────────────
        search_row = tk.Frame(tab, bg=BG)
        search_row.pack(fill="x", padx=20, pady=(0, 4))

        tk.Label(search_row, text="Search Tenant", bg=BG, fg=FG,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
        self._ten_search_entry = self._entry(search_row, width=22)
        self._ten_search_entry.pack(side="left", padx=(0, 10))

        tk.Label(search_row, text="Occupation", bg=BG, fg=FG,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
        self._ten_occ_entry = self._entry(search_row, width=18)
        self._ten_occ_entry.pack(side="left", padx=(0, 10))

        self._button(search_row, "Apply Search", self._refresh_tenants).pack(side="left", padx=4)
        self._button(search_row, "Clear Search", self._clear_tenant_search, YELLOW).pack(side="left", padx=4)

        # ── Treeview ─────────────────────────────────────
        cols = ("ID", "NI", "First", "Last", "Phone", "Email", "Occupation", "Reference", "Created")
        w    = [50, 100, 90, 90, 110, 160, 90, 120, 130]
        self._ten_frame, self._ten_tree = self._treeview(tab, cols, w)
        self._ten_frame.pack(fill="both", expand=True, padx=20, pady=4)
        self._ten_tree.bind("<<TreeviewSelect>>", self._on_tenant_select)

        if self.role == "MANAGER":
            filter_row = tk.Frame(tab, bg=BG)
            filter_row.pack(fill="x", padx=20, pady=(0, 4))
            tk.Label(filter_row, text="Location View", bg=BG, fg=FG, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
            self._ten_filter_combo = ttk.Combobox(filter_row, state="readonly", width=22)
            self._ten_filter_combo.pack(side="left")
            opts = ["All Locations"] + [f"{loc_id} - {city}" for loc_id, city in self._load_location_options()]
            self._ten_filter_combo["values"] = opts
            self._ten_filter_combo.current(0)
            self._ten_filter_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_tenants())

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

    def _clear_tenant_search(self):
        if hasattr(self, "_ten_search_entry"):
            self._ten_search_entry.delete(0, "end")
        if hasattr(self, "_ten_occ_entry"):
            self._ten_occ_entry.delete(0, "end")
        self._refresh_tenants()

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
            rows = AdminController.GetTenants(*self._R())

            if self.role == "MANAGER" and hasattr(self, "_ten_filter_combo"):
                selected = self._ten_filter_combo.get()
                selected_id = self._parse_location_choice(selected)
                if selected and selected != "All Locations" and selected_id is not None:
                    from source.app.databases.database import Get_Connection
                    conn = Get_Connection()
                    try:
                        cur = conn.cursor()
                        cur.execute("""
                            SELECT DISTINCT
                                t.tenant_id, t.ni_number, t.first_name, t.last_name,
                                t.phone, t.email, t.occupation, t.tenant_references, t.created_at
                            FROM Tenant t
                            LEFT JOIN Lease l ON t.tenant_id = l.tenant_id AND l.status='ACTIVE'
                            LEFT JOIN Apartment a ON l.apartment_id = a.apartment_id
                            WHERE t.is_active = 1
                              AND (a.location_id = ? OR l.lease_id IS NULL)
                            ORDER BY t.tenant_id DESC
                        """, (selected_id,))
                        rows = cur.fetchall()
                    finally:
                        conn.close()

            keyword = self._ten_search_entry.get().strip().lower() if hasattr(self, "_ten_search_entry") else ""
            occ = self._ten_occ_entry.get().strip().lower() if hasattr(self, "_ten_occ_entry") else ""
            if keyword or occ:
                filtered = []
                for r in rows:
                    ni = str(r[1]).lower()
                    first = str(r[2]).lower()
                    last = str(r[3]).lower()
                    occupation = str(r[6] or "").lower()
                    if keyword and not (keyword in ni or keyword in first or keyword in last):
                        continue
                    if occ and occ not in occupation:
                        continue
                    filtered.append(r)
                rows = filtered

            for r in rows:
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

        search_row = tk.Frame(tab, bg=BG)
        search_row.pack(fill="x", padx=20, pady=(0, 4))
        tk.Label(search_row, text="Search Lease", bg=BG, fg=FG,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
        self._lea_search_entry = self._entry(search_row, width=22)
        self._lea_search_entry.pack(side="left", padx=(0, 10))
        self._button(search_row, "Apply Search", self._refresh_leases).pack(side="left", padx=4)
        self._button(search_row, "Clear Search", self._clear_lease_search, YELLOW).pack(side="left", padx=4)


        if self.role == "MANAGER":
            filter_row = tk.Frame(tab, bg=BG)
            filter_row.pack(fill="x", padx=20, pady=(0, 4))
            tk.Label(filter_row, text="Location View", bg=BG, fg=FG, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
            self._lea_filter_combo = ttk.Combobox(filter_row, state="readonly", width=22)
            self._lea_filter_combo.pack(side="left")
            opts = ["All Locations"] + [f"{loc_id} - {city}" for loc_id, city in self._load_location_options()]
            self._lea_filter_combo["values"] = opts
            self._lea_filter_combo.current(0)
            self._lea_filter_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_leases())

        row = tk.Frame(tab, bg=BG)
        row.pack(pady=8)
        self._button(row, "⟳ Refresh",           self._refresh_leases).pack(side="left", padx=5)
        self._button(row, "Standard Terminate",   self._terminate_lease, YELLOW).pack(side="left", padx=5)
        self._button(row, "Early Terminate",       self._early_terminate_lease, RED).pack(side="left", padx=5)

        self._refresh_leases()

    def _clear_lease_search(self):
        if hasattr(self, "_lea_search_entry"):
            self._lea_search_entry.delete(0, "end")
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
            rows = AdminController.GetLeases(*self._R())

            if self.role == "MANAGER" and hasattr(self, "_lea_filter_combo"):
                selected = self._lea_filter_combo.get()
                selected_id = self._parse_location_choice(selected)
                if selected and selected != "All Locations" and selected_id is not None:
                    from source.app.databases.database import Get_Connection
                    conn = Get_Connection()
                    try:
                        cur = conn.cursor()
                        cur.execute("""
                            SELECT l.lease_id,
                                   t.first_name || ' ' || t.last_name AS tenant_name,
                                   t.ni_number,
                                   a.apartment_number,
                                   loc.city,
                                   l.start_date,
                                   l.end_date,
                                   l.agreed_monthly_rent,
                                   l.deposit_amount,
                                   l.status
                            FROM Lease l
                            JOIN Tenant t ON l.tenant_id = t.tenant_id
                            JOIN Apartment a ON l.apartment_id = a.apartment_id
                            JOIN Location loc ON a.location_id = loc.location_id
                            WHERE a.location_id = ?
                            ORDER BY l.lease_id DESC
                        """, (selected_id,))
                        rows = cur.fetchall()
                    finally:
                        conn.close()

            keyword = self._lea_search_entry.get().strip().lower() if hasattr(self, "_lea_search_entry") else ""
            if keyword:
                filtered = []
                for r in rows:
                    hay = " ".join(str(x).lower() for x in r)
                    if keyword in hay:
                        filtered.append(r)
                rows = filtered

            for r in rows:
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

    from datetime import datetime, timedelta

    def _early_terminate_lease(self):
        """Early termination — 1 month notice required, 5% penalty invoice created."""
        sel = self._lea_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a lease first.")
            return

        values = self._lea_tree.item(sel[0])["values"]
        lid = values[0]
        monthly_rent = float(values[7]) if len(values) > 7 and values[7] not in ("", None) else 0.0

        notice_text = simpledialog.askstring(
            "Early Termination — Notice Date",
            "Enter the date the tenant gave notice (YYYY-MM-DD):\n\n"
            "Rule: tenant must give 1 month notice and pays 5% of monthly rent.",
            parent=self.parent
        )
        if not notice_text:
            return

        try:
            notice_date = datetime.strptime(notice_text.strip(), "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Error", "Notice date must use YYYY-MM-DD format.")
            return

        earliest_leave_date = notice_date + timedelta(days=30)
        penalty_amount = round(monthly_rent * 0.05, 2)

        if not messagebox.askyesno(
            "Confirm Early Termination",
            f"Lease ID: {lid}\n"
            f"Notice Date: {notice_date}\n"
            f"Earliest Valid Leave Date: {earliest_leave_date}\n"
            f"Penalty: £{penalty_amount:.2f}\n\n"
            "Proceed with early termination?"
        ):
            return

        try:
            result = AdminController.TerminateLeaseEarly(lid, notice_date.isoformat(), *self._R())

            if result.get("is_early"):
                messagebox.showinfo(
                    "Terminated — Early",
                    f"Lease #{lid} terminated early.\n\n"
                    f"Notice Date: {notice_date}\n"
                    f"Earliest Valid Leave Date: {earliest_leave_date}\n"
                    f"Penalty charged: £{result['penalty_amount']:.2f}\n"
                    f"Penalty invoice: #{result['penalty_invoice_id']}\n\n"
                    "Apartment is now AVAILABLE."
                )
            else:
                messagebox.showinfo(
                    "Terminated",
                    f"Lease #{lid} terminated.\n"
                    "No early penalty was applied.\n"
                    "Apartment is now AVAILABLE."
                )

            self._refresh_leases()
            self._refresh_dashboard()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ══════════════════════════════════════════════════════
    #  4)  APARTMENTS
    # ══════════════════════════════════════════════════════
    def _build_apartments(self, tab):
        self._heading(tab, "Apartment Management").pack(anchor="w", padx=20, pady=(15, 4))

        helper = (
            "Admins can add apartments only for their assigned location. Managers can choose any location. "
            "Apartment numbers should start with the location letter, e.g. B for Bristol or L for London."
        )
        tk.Label(tab, text=helper, bg=BG, fg="#94a3b8", justify="left", wraplength=1200,
                 font=("Segoe UI", 9, "italic")).pack(anchor="w", padx=20, pady=(0, 6))

        form = tk.Frame(tab, bg=BG_CARD, padx=14, pady=10)
        form.pack(fill="x", padx=20, pady=6)

        self._apt_e = {}

        tk.Label(form, text="Location", bg=BG_CARD, fg=FG, font=("Segoe UI", 9)).grid(row=0, column=0, padx=4)
        if self.role == "ADMIN":
            self._apt_location_locked = tk.StringVar(value=f"{self.loc_id} - {self._scope_text()}")
            locked = self._entry(form, width=18)
            locked.grid(row=1, column=0, padx=4, pady=4)
            locked.insert(0, self._apt_location_locked.get())
            locked.config(state="disabled")
            self._apt_location_combo = None
        else:
            self._apt_location_combo = ttk.Combobox(form, state="readonly", width=18)
            self._apt_location_combo.grid(row=1, column=0, padx=4, pady=4)
            self._set_location_combobox_values(self._apt_location_combo)
            if self._apt_location_combo["values"]:
                self._apt_location_combo.current(0)

        tk.Label(form, text="Apartment No.", bg=BG_CARD, fg=FG, font=("Segoe UI", 9)).grid(row=0, column=1, padx=4)
        self._apt_e["Apartment No."] = self._entry(form, width=14)
        self._apt_e["Apartment No."].grid(row=1, column=1, padx=4, pady=4)

        tk.Label(form, text="Type", bg=BG_CARD, fg=FG, font=("Segoe UI", 9)).grid(row=0, column=2, padx=4)
        self._apt_type_combo = ttk.Combobox(
            form, state="readonly", width=16,
            values=list(TYPE_ROOM_MAP.keys())
        )
        self._apt_type_combo.grid(row=1, column=2, padx=4, pady=4)
        self._apt_type_combo.bind("<<ComboboxSelected>>", self._on_apartment_type_selected)

        tk.Label(form, text="Rooms", bg=BG_CARD, fg=FG, font=("Segoe UI", 9)).grid(row=0, column=3, padx=4)
        self._apt_e["Rooms"] = self._entry(form, width=10)
        self._apt_e["Rooms"].grid(row=1, column=3, padx=4, pady=4)

        tk.Label(form, text="Monthly Rent", bg=BG_CARD, fg=FG, font=("Segoe UI", 9)).grid(row=0, column=4, padx=4)
        self._apt_e["Monthly Rent"] = self._entry(form, width=14)
        self._apt_e["Monthly Rent"].grid(row=1, column=4, padx=4, pady=4)

        self._button(form, "Add Apartment", self._add_apartment).grid(row=1, column=5, padx=8)

        filter_row = tk.Frame(tab, bg=BG)
        filter_row.pack(fill="x", padx=20, pady=(0, 4))
        if self.role == "ADMIN":
            tk.Label(filter_row, text=f"Showing apartments for your location: {self._scope_text()}",
                     bg=BG, fg="#94a3b8", font=("Segoe UI", 9, "italic")).pack(side="left")
            self._apt_filter_combo = None
        else:
            tk.Label(filter_row, text="Location View", bg=BG, fg=FG, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
            self._apt_filter_combo = ttk.Combobox(filter_row, state="readonly", width=22)
            self._apt_filter_combo.pack(side="left")
            opts = ["All Locations"] + [f"{loc_id} - {city}" for loc_id, city in self._load_location_options()]
            self._apt_filter_combo["values"] = opts
            self._apt_filter_combo.current(0)
            self._apt_filter_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_apartments())

        cols = ("ID", "Apt Number", "Type", "Rooms", "Rent", "Status", "City")
        w    = [60, 110, 120, 70, 90, 110, 120]
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
            if self.role == "ADMIN":
                location_id = self.loc_id
            else:
                location_id = self._parse_location_choice(self._apt_location_combo.get())
                if not location_id:
                    raise ValueError("Select a location before adding an apartment.")

            apartment_no = e["Apartment No."].get().strip().upper()
            apartment_type = self._apt_type_combo.get().strip()
            rooms = int(e["Rooms"].get())
            monthly_rent = float(e["Monthly Rent"].get())

            if not apartment_no:
                raise ValueError("Apartment number is required.")
            if not apartment_no[0].isalpha():
                raise ValueError("Apartment number must start with a letter.")
            expected_prefix = self._expected_apartment_prefix(int(location_id))
            if expected_prefix and apartment_no[0].upper() != expected_prefix:
                raise ValueError(f"Apartment number should start with '{expected_prefix}' for this location.")

            if not apartment_type:
                raise ValueError("Select an apartment type.")
            suggested_rooms = TYPE_ROOM_MAP.get(apartment_type)
            if suggested_rooms is not None and apartment_type != "Penthouse" and rooms != suggested_rooms:
                raise ValueError(f"{apartment_type} should use {suggested_rooms} room(s).")
            if apartment_type == "Penthouse" and rooms < 4:
                raise ValueError("Penthouse should have at least 4 rooms.")

            AdminController.CreateApartment(
                int(location_id),
                apartment_no,
                apartment_type,
                rooms,
                monthly_rent
            )
            messagebox.showinfo("Success", "Apartment added.")
            for ent in e.values():
                ent.delete(0, "end")
            if hasattr(self, "_apt_type_combo"):
                self._apt_type_combo.set("")
            if self.role == "MANAGER" and self._apt_location_combo and self._apt_location_combo["values"]:
                self._apt_location_combo.current(0)
            self._refresh_apartments()
        except Exception as err:
            messagebox.showerror("Error", str(err))

    def _refresh_apartments(self):
        self._apt_tree.delete(*self._apt_tree.get_children())
        try:
            rows = AdminController.GetApartments(*self._R())
            if self.role == "MANAGER" and hasattr(self, "_apt_filter_combo"):
                selected = self._apt_filter_combo.get()
                selected_id = self._parse_location_choice(selected)
                if selected and selected != "All Locations" and selected_id is not None:
                    city_map = {loc_id: city for loc_id, city in self._load_location_options()}
                    rows = [r for r in rows if len(r) > 6 and str(r[6]) == city_map.get(selected_id)]
            for r in rows:
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

        if self.role == "MANAGER":
            filter_row = tk.Frame(tab, bg=BG)
            filter_row.pack(fill="x", padx=20, pady=(0, 4))
            tk.Label(filter_row, text="Location View", bg=BG, fg=FG, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
            self._inv_filter_combo = ttk.Combobox(filter_row, state="readonly", width=22)
            self._inv_filter_combo.pack(side="left")
            opts = ["All Locations"] + [f"{loc_id} - {city}" for loc_id, city in self._load_location_options()]
            self._inv_filter_combo["values"] = opts
            self._inv_filter_combo.current(0)
            self._inv_filter_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_invoices())

        self._button(tab, "⟳ Refresh", self._refresh_invoices).pack(pady=8)
        self._refresh_invoices()

    def _refresh_invoices(self):
        self._inv_tree.delete(*self._inv_tree.get_children())
        try:
            rows = AdminController.GetAllInvoices(*self._R())
            if self.role == "MANAGER" and hasattr(self, "_inv_filter_combo"):
                selected = self._inv_filter_combo.get()
                selected_id = self._parse_location_choice(selected)
                if selected and selected != "All Locations" and selected_id is not None:
                    city_map = {loc_id: city for loc_id, city in self._load_location_options()}
                    rows = [r for r in rows if len(r) > 3 and str(r[3]) == city_map.get(selected_id)]
            counts = {"total": len(rows), "paid": 0, "pending": 0, "overdue": 0}
            for r in rows:
                status = r[6]
                tag    = status
                self._inv_tree.insert("", "end", values=r, tags=(tag,))
                if status == "PAID":
                    counts["paid"] += 1
                elif status == "OVERDUE":
                    counts["overdue"] += 1
                else:
                    counts["pending"] += 1
            self._inv_summary["total"].config(text=str(counts["total"]))
            self._inv_summary["paid"].config(text=str(counts["paid"]), fg=GREEN)
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

        if self.role == "MANAGER":
            filter_row = tk.Frame(tab, bg=BG)
            filter_row.pack(fill="x", padx=20, pady=(0, 4))
            tk.Label(filter_row, text="Location View", bg=BG, fg=FG, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
            self._comp_filter_combo = ttk.Combobox(filter_row, state="readonly", width=22)
            self._comp_filter_combo.pack(side="left")
            opts = ["All Locations"] + [f"{loc_id} - {city}" for loc_id, city in self._load_location_options()]
            self._comp_filter_combo["values"] = opts
            self._comp_filter_combo.current(0)
            self._comp_filter_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_complaints())

        row = tk.Frame(tab, bg=BG)
        row.pack(pady=8)
        self._button(row, "⟳ Refresh",      self._refresh_complaints).pack(side="left", padx=5)
        self._button(row, "Close Selected", self._close_complaint, RED).pack(side="left", padx=5)

        self._refresh_complaints()

    def _refresh_complaints(self):
        self._comp_tree.delete(*self._comp_tree.get_children())
        try:
            rows = AdminController.GetComplaints(*self._R())
            if self.role == "MANAGER" and hasattr(self, "_comp_filter_combo"):
                selected = self._comp_filter_combo.get()
                selected_id = self._parse_location_choice(selected)
                if selected and selected != "All Locations" and selected_id is not None:
                    city_map = {loc_id: city for loc_id, city in self._load_location_options()}
                    rows = [r for r in rows if len(r) > 6 and str(r[6]) == city_map.get(selected_id)]
            for r in rows:
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
                self._refresh_dashboard()
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

        if self.role == "MANAGER":
            filter_row = tk.Frame(tab, bg=BG)
            filter_row.pack(fill="x", padx=20, pady=(0, 4))
            tk.Label(filter_row, text="Location View", bg=BG, fg=FG, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
            self._sta_filter_combo = ttk.Combobox(filter_row, state="readonly", width=22)
            self._sta_filter_combo.pack(side="left")
            opts = ["All Locations"] + [f"{loc_id} - {city}" for loc_id, city in self._load_location_options()]
            self._sta_filter_combo["values"] = opts
            self._sta_filter_combo.current(0)
            self._sta_filter_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_staff())

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
            for key, ent in e.items():
                if self.role == "ADMIN" and key == "Location ID":
                    continue
                ent.delete(0, "end")
            self._refresh_staff()
        except Exception as err:
            messagebox.showerror("Error", str(err))

    def _refresh_staff(self):
        self._sta_tree.delete(*self._sta_tree.get_children())
        try:
            rows = AdminController.GetStaff(*self._R())
            if self.role == "MANAGER" and hasattr(self, "_sta_filter_combo"):
                selected = self._sta_filter_combo.get()
                selected_id = self._parse_location_choice(selected)
                if selected and selected != "All Locations" and selected_id is not None:
                    city_map = {loc_id: city for loc_id, city in self._load_location_options()}
                    rows = [r for r in rows if len(r) > 3 and str(r[3]) == city_map.get(selected_id)]
            for r in rows:
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
            self._refresh_dashboard()
            for combo_name in ("_apt_location_combo", "_apt_filter_combo", "_inv_filter_combo", "_comp_filter_combo", "_sta_filter_combo", "_ten_filter_combo", "_lea_filter_combo"):
                combo = getattr(self, combo_name, None)
                if combo:
                    opts = ["All Locations"] + [f"{loc_id} - {city}" for loc_id, city in self._load_location_options()]
                    if combo_name == "_apt_location_combo":
                        opts = [f"{loc_id} - {city}" for loc_id, city in self._load_location_options()]
                    combo["values"] = opts
                    if opts:
                        combo.current(0)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _refresh_locations(self):
        self._loc_tree.delete(*self._loc_tree.get_children())
        try:
            for r in AdminController.GetAllLocations():
                self._loc_tree.insert("", "end", values=r)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def close(self):
        self.destroy()
        if self.parent:
            self.parent.deiconify()