
import tkinter as tk
from tkinter import ttk, messagebox
from source.app.controllers.Maintenance import MaintenanceController

BG = "#0f172a"
BG_CARD = "#1e293b"
FG = "#e2e8f0"
ACCENT = "#0ea5e9"
ACCENT2 = "#38bdf8"
BORDER = "#334155"
INPUT_BG = "#020617"
RED = "#ef4444"
GREEN = "#22c55e"
YELLOW = "#f59e0b"


class MaintenanceUI(tk.Toplevel):
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.parent = parent
        self.user = user or {}
        self.role = self.user.get("role")

        if self.role != "MAINTENANCE":
            self.destroy()
            raise PermissionError("Only MAINTENANCE users can access the maintenance dashboard.")

        self.title(f"PAMS — Maintenance Dashboard ({self.user.get('username', 'Unknown')})")
        self.geometry("1450x860")
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self.logout)

        self.create_styles()
        self.create_widgets()
        self.load_requests()

    def create_styles(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background=BG_CARD,
            foreground=FG,
            fieldbackground=BG_CARD,
            rowheight=30,
            font=("Segoe UI", 10)
        )
        style.configure(
            "Treeview.Heading",
            background=BORDER,
            foreground=FG,
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )
        style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", "#020617")])
        style.configure("TCombobox", fieldbackground=INPUT_BG, background=INPUT_BG, foreground="black")

    def _button(self, parent, text, command, color=ACCENT, width=14):
        fg = "#020617" if color not in (RED, YELLOW) else "white"
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg=fg,
            width=width,
            height=2,
            font=("Segoe UI", 10, "bold"),
            activebackground=ACCENT2 if color == ACCENT else color,
            activeforeground=fg,
            relief="flat",
            cursor="hand2"
        )
        return btn

    def _entry(self, parent, width=22):
        return tk.Entry(
            parent,
            width=width,
            bg=INPUT_BG,
            fg="white",
            insertbackground="white",
            relief="flat",
            font=("Segoe UI", 10)
        )

    def create_widgets(self):
        tk.Label(
            self,
            text="Maintenance Staff Dashboard",
            font=("Segoe UI", 22, "bold"),
            bg=BG,
            fg=ACCENT
        ).pack(pady=(18, 8))

        user_text = f"Logged in as: {self.user.get('username', 'Unknown')} ({self.role})"
        tk.Label(self, text=user_text, font=("Segoe UI", 11), bg=BG, fg="#94a3b8").pack(pady=(0, 4))
        tk.Label(self, text="Scope: Assigned Location Only", font=("Segoe UI", 10, "italic"), bg=BG, fg="#94a3b8").pack(pady=(0, 10))

        top_frame = tk.Frame(self, bg=BG)
        top_frame.pack(fill="x", padx=18, pady=8)

        tk.Label(top_frame, text="Filter by Status:", font=("Segoe UI", 11, "bold"), bg=BG, fg=FG).pack(side="left", padx=(4, 8))
        self.status_filter = ttk.Combobox(top_frame, values=["ALL", "REPORTED", "SCHEDULED", "IN_PROGRESS", "RESOLVED"], state="readonly", width=18)
        self.status_filter.current(0)
        self.status_filter.pack(side="left", padx=5)

        self._button(top_frame, "Apply Filter", self.apply_filter).pack(side="left", padx=6)
        self._button(top_frame, "Refresh", self.load_requests).pack(side="left", padx=6)

        tk.Label(top_frame, text="Tenant ID:", font=("Segoe UI", 11, "bold"), bg=BG, fg=FG).pack(side="left", padx=(20, 8))
        self.tenant_search_entry = self._entry(top_frame, width=12)
        self.tenant_search_entry.pack(side="left", padx=5)
        self._button(top_frame, "Search Tenant", self.search_by_tenant).pack(side="left", padx=6)
        self._button(top_frame, "Show All", self.load_requests).pack(side="left", padx=6)

        table_card = tk.LabelFrame(
            self,
            text=" Maintenance Requests ",
            font=("Segoe UI", 11, "bold"),
            bg=BG_CARD,
            fg=ACCENT,
            bd=1,
            relief="solid"
        )
        table_card.pack(fill="both", expand=True, padx=18, pady=10)
        table_frame = tk.Frame(table_card, bg=BG_CARD)
        table_frame.pack(fill="both", expand=True, padx=8, pady=8)

        columns = (
            "request_id", "tenant_id", "apartment_id", "description",
            "priority", "status", "assigned_worker",
            "scheduled_date", "scheduled_time",
            "resolution_notes", "time_taken_hours",
            "reported_date", "resolved_date", "cost"
        )
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        headings = {
            "request_id": "Request ID",
            "tenant_id": "Tenant ID",
            "apartment_id": "Apartment ID",
            "description": "Description",
            "priority": "Priority",
            "status": "Status",
            "assigned_worker": "Assigned Worker",
            "scheduled_date": "Scheduled Date",
            "scheduled_time": "Scheduled Time",
            "resolution_notes": "Resolution Notes",
            "time_taken_hours": "Time Taken (hrs)",
            "reported_date": "Reported Date",
            "resolved_date": "Resolved Date",
            "cost": "Cost"
        }
        widths = {
            "request_id": 90, "tenant_id": 90, "apartment_id": 100, "description": 230,
            "priority": 90, "status": 110, "assigned_worker": 130, "scheduled_date": 115,
            "scheduled_time": 115, "resolution_notes": 220, "time_taken_hours": 120,
            "reported_date": 130, "resolved_date": 120, "cost": 90
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")

        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree.tag_configure("REPORTED", foreground="#fecaca")
        self.tree.tag_configure("SCHEDULED", foreground="#fde68a")
        self.tree.tag_configure("IN_PROGRESS", foreground="#93c5fd")
        self.tree.tag_configure("RESOLVED", foreground="#86efac")
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        form_card = tk.LabelFrame(
            self,
            text=" Maintenance Actions ",
            font=("Segoe UI", 11, "bold"),
            bg=BG_CARD,
            fg=ACCENT,
            bd=1,
            relief="solid"
        )
        form_card.pack(fill="x", padx=18, pady=10)
        form = tk.Frame(form_card, bg=BG_CARD)
        form.pack(fill="x", padx=14, pady=14)

        label_style = {"bg": BG_CARD, "fg": FG, "font": ("Segoe UI", 10, "bold")}

        tk.Label(form, text="Request ID", **label_style).grid(row=0, column=0, padx=8, pady=10, sticky="w")
        self.request_id_entry = self._entry(form)
        self.request_id_entry.grid(row=0, column=1, padx=8, pady=10)
        tk.Label(form, text="Tenant ID", **label_style).grid(row=0, column=2, padx=8, pady=10, sticky="w")
        self.tenant_id_entry = self._entry(form)
        self.tenant_id_entry.grid(row=0, column=3, padx=8, pady=10)
        tk.Label(form, text="Apartment ID", **label_style).grid(row=0, column=4, padx=8, pady=10, sticky="w")
        self.apartment_id_entry = self._entry(form)
        self.apartment_id_entry.grid(row=0, column=5, padx=8, pady=10)
        tk.Label(form, text="Description", **label_style).grid(row=1, column=0, padx=8, pady=10, sticky="w")
        self.description_entry = self._entry(form, width=54)
        self.description_entry.grid(row=1, column=1, columnspan=3, padx=8, pady=10, sticky="we")
        tk.Label(form, text="Priority", **label_style).grid(row=1, column=4, padx=8, pady=10, sticky="w")
        self.priority_combo = ttk.Combobox(form, values=["LOW", "MEDIUM", "HIGH"], state="readonly", width=19)
        self.priority_combo.set("LOW")
        self.priority_combo.grid(row=1, column=5, padx=8, pady=10)
        tk.Label(form, text="Assigned Worker", **label_style).grid(row=2, column=0, padx=8, pady=10, sticky="w")
        self.assigned_worker_entry = self._entry(form)
        self.assigned_worker_entry.grid(row=2, column=1, padx=8, pady=10)
        tk.Label(form, text="Scheduled Date", **label_style).grid(row=2, column=2, padx=8, pady=10, sticky="w")
        self.scheduled_date_entry = self._entry(form)
        self.scheduled_date_entry.grid(row=2, column=3, padx=8, pady=10)
        tk.Label(form, text="Scheduled Time", **label_style).grid(row=2, column=4, padx=8, pady=10, sticky="w")
        self.scheduled_time_entry = self._entry(form)
        self.scheduled_time_entry.grid(row=2, column=5, padx=8, pady=10)
        tk.Label(form, text="Resolution Notes", **label_style).grid(row=3, column=0, padx=8, pady=10, sticky="w")
        self.resolution_notes_entry = self._entry(form, width=54)
        self.resolution_notes_entry.grid(row=3, column=1, columnspan=3, padx=8, pady=10, sticky="we")
        tk.Label(form, text="Time Taken (hrs)", **label_style).grid(row=3, column=4, padx=8, pady=10, sticky="w")
        self.time_taken_entry = self._entry(form)
        self.time_taken_entry.grid(row=3, column=5, padx=8, pady=10)
        tk.Label(form, text="Cost", **label_style).grid(row=4, column=0, padx=8, pady=10, sticky="w")
        self.cost_entry = self._entry(form)
        self.cost_entry.grid(row=4, column=1, padx=8, pady=10)

        button_frame = tk.Frame(self, bg=BG)
        button_frame.pack(fill="x", padx=18, pady=(4, 18))
        self._button(button_frame, "Create Request", self.create_request).pack(side="left", padx=6)
        self._button(button_frame, "Change Priority", self.change_priority, YELLOW).pack(side="left", padx=6)
        self._button(button_frame, "Schedule Request", self.schedule_request).pack(side="left", padx=6)
        self._button(button_frame, "Start Maintenance", self.start_request).pack(side="left", padx=6)
        self._button(button_frame, "Resolve Request", self.resolve_request, GREEN).pack(side="left", padx=6)
        self._button(button_frame, "Clear Fields", self.clear_fields).pack(side="left", padx=6)
        self._button(button_frame, "Logout", self.logout, RED).pack(side="right", padx=6)

    def insert_rows(self, requests):
        self.tree.delete(*self.tree.get_children())
        for row in requests:
            status = row[5]
            self.tree.insert("", "end", values=row, tags=(status,))

    def load_requests(self):
        if hasattr(self, "tenant_search_entry"):
            self.tenant_search_entry.delete(0, tk.END)
        try:
            self.insert_rows(MaintenanceController.ViewAllRequests())
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def apply_filter(self):
        status = self.status_filter.get()
        try:
            rows = MaintenanceController.ViewAllRequests() if status == "ALL" else MaintenanceController.ViewRequestsByStatus(status)
            self.insert_rows(rows)
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def search_by_tenant(self):
        tenant_text = self.tenant_search_entry.get().strip()
        try:
            if not tenant_text:
                raise ValueError("Please enter a Tenant ID.")
            tenant_id = int(tenant_text)
            requests = MaintenanceController.ViewRequestsByTenant(tenant_id)
            self.insert_rows(requests)
            if not requests:
                messagebox.showinfo("No Results", f"No maintenance requests found for Tenant ID {tenant_id}.")
        except ValueError as error:
            messagebox.showerror("Search Error", str(error))
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def on_row_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        self.clear_fields()
        self.request_id_entry.insert(0, values[0])
        self.tenant_id_entry.insert(0, values[1])
        self.apartment_id_entry.insert(0, values[2])
        self.description_entry.insert(0, values[3])
        self.priority_combo.set(values[4])
        if len(values) > 6 and values[6]:
            self.assigned_worker_entry.insert(0, values[6])
        if len(values) > 7 and values[7]:
            self.scheduled_date_entry.insert(0, values[7])
        if len(values) > 8 and values[8]:
            self.scheduled_time_entry.insert(0, values[8])
        if len(values) > 9 and values[9]:
            self.resolution_notes_entry.insert(0, values[9])
        if len(values) > 10 and values[10]:
            self.time_taken_entry.insert(0, values[10])
        if len(values) > 13 and values[13]:
            self.cost_entry.insert(0, values[13])

    def create_request(self):
        try:
            rid = MaintenanceController.CreateRequest(
                int(self.tenant_id_entry.get()),
                int(self.apartment_id_entry.get()),
                self.description_entry.get(),
                self.priority_combo.get(),
            )
            messagebox.showinfo("Success", f"Request created successfully.\nRequest ID: {rid}")
            self.load_requests()
            self.clear_fields()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def change_priority(self):
        try:
            MaintenanceController.ChangePriority(int(self.request_id_entry.get()), self.priority_combo.get())
            messagebox.showinfo("Success", "Priority updated successfully.")
            self.load_requests()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def schedule_request(self):
        try:
            MaintenanceController.ScheduleRequest(
                int(self.request_id_entry.get()),
                self.assigned_worker_entry.get(),
                self.scheduled_date_entry.get(),
                self.scheduled_time_entry.get(),
            )
            messagebox.showinfo("Success", "Request scheduled successfully.")
            self.load_requests()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def start_request(self):
        try:
            MaintenanceController.StartRequest(int(self.request_id_entry.get()))
            messagebox.showinfo("Success", "Maintenance started successfully.")
            self.load_requests()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def resolve_request(self):
        try:
            MaintenanceController.ResolveRequest(
                int(self.request_id_entry.get()),
                self.resolution_notes_entry.get(),
                float(self.time_taken_entry.get()),
                float(self.cost_entry.get()),
            )
            messagebox.showinfo("Success", "Request resolved successfully.")
            self.load_requests()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear_fields(self):
        for field in [
            self.request_id_entry, self.tenant_id_entry, self.apartment_id_entry,
            self.description_entry, self.assigned_worker_entry, self.scheduled_date_entry,
            self.scheduled_time_entry, self.resolution_notes_entry, self.time_taken_entry,
            self.cost_entry
        ]:
            field.delete(0, tk.END)
        self.priority_combo.set("LOW")

    def logout(self):
        self.destroy()
        if self.parent:
            self.parent.deiconify()
