import tkinter as tk
from tkinter import ttk, messagebox
from source.app.controllers.Maintenance import MaintenanceController


class MaintenanceUI(tk.Toplevel):

    def __init__(self, parent=None, user=None):
        super().__init__(parent)

        self.parent = parent
        self.user = user

        self.title("Maintenance Staff Dashboard")
        self.geometry("1450x860")
        self.configure(bg="#eef2f7")

        self.protocol("WM_DELETE_WINDOW", self.logout)

        self.create_styles()
        self.create_widgets()
        self.load_requests()

    def create_styles(self):
        self.colors = {
            "bg": "#eef2f7",
            "card": "#ffffff",
            "text": "#1f2937",
            "muted": "#374151",
            "border": "#cbd5e1",
            "button_bg": "#ffffff",
            "button_fg": "#111827",
            "button_active": "#dbeafe",
            "heading_bg": "#dbeafe",
            "table_bg": "#ffffff"
        }

        style = ttk.Style()
        style.theme_use("default")

        style.configure(
            "Treeview",
            background=self.colors["table_bg"],
            foreground="black",
            fieldbackground=self.colors["table_bg"],
            rowheight=30,
            font=("Arial", 10)
        )

        style.configure(
            "Treeview.Heading",
            background=self.colors["heading_bg"],
            foreground="black",
            font=("Arial", 10, "bold"),
            relief="flat"
        )

        style.map(
            "Treeview",
            background=[("selected", "#93c5fd")],
            foreground=[("selected", "black")]
        )

        style.configure(
            "TCombobox",
            fieldbackground="white",
            background="white",
            foreground="black"
        )

    def create_widgets(self):
        title = tk.Label(
            self,
            text="Maintenance Staff Dashboard",
            font=("Arial", 22, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"]
        )
        title.pack(pady=(18, 8))

        user_text = "Logged in as: "
        if self.user:
            user_text += f"{self.user['username']} ({self.user['role']})"
        else:
            user_text += "Unknown user"

        user_label = tk.Label(
            self,
            text=user_text,
            font=("Arial", 11),
            bg=self.colors["bg"],
            fg="#4b5563"
        )
        user_label.pack(pady=(0, 10))

        top_frame = tk.Frame(self, bg=self.colors["bg"])
        top_frame.pack(fill="x", padx=18, pady=8)

        tk.Label(
            top_frame,
            text="Filter by Status:",
            font=("Arial", 11, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"]
        ).pack(side="left", padx=(4, 8))

        self.status_filter = ttk.Combobox(
            top_frame,
            values=["ALL", "REPORTED", "SCHEDULED", "IN_PROGRESS", "RESOLVED"],
            state="readonly",
            width=18
        )
        self.status_filter.current(0)
        self.status_filter.pack(side="left", padx=5)

        button_style = {
            "width": 14,
            "height": 2,
            "font": ("Arial", 10, "bold"),
            "bg": self.colors["button_bg"],
            "fg": self.colors["button_fg"],
            "activebackground": self.colors["button_active"],
            "activeforeground": "black",
            "relief": "solid",
            "bd": 1,
            "cursor": "hand2"
        }

        tk.Button(
            top_frame,
            text="Apply Filter",
            command=self.apply_filter,
            **button_style
        ).pack(side="left", padx=6)

        tk.Button(
            top_frame,
            text="Refresh",
            command=self.load_requests,
            **button_style
        ).pack(side="left", padx=6)

        tk.Label(
            top_frame,
            text="Tenant ID:",
            font=("Arial", 11, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"]
        ).pack(side="left", padx=(20, 8))

        self.tenant_search_entry = tk.Entry(
            top_frame,
            width=12,
            font=("Arial", 10),
            bg="#f8fafc",
            fg="#111827",
            relief="solid",
            bd=1
        )
        self.tenant_search_entry.pack(side="left", padx=5)

        tk.Button(
            top_frame,
            text="Search Tenant",
            command=self.search_by_tenant,
            **button_style
        ).pack(side="left", padx=6)

        tk.Button(
            top_frame,
            text="Show All",
            command=self.load_requests,
            **button_style
        ).pack(side="left", padx=6)

        table_card = tk.LabelFrame(
            self,
            text=" Maintenance Requests ",
            font=("Arial", 11, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"],
            bd=1,
            relief="solid"
        )
        table_card.pack(fill="both", expand=True, padx=18, pady=10)

        table_frame = tk.Frame(table_card, bg=self.colors["card"])
        table_frame.pack(fill="both", expand=True, padx=8, pady=8)

        columns = (
            "request_id", "tenant_id", "apartment_id", "description",
            "priority", "status", "assigned_worker",
            "scheduled_date", "scheduled_time",
            "resolution_notes", "time_taken_hours",
            "reported_date", "resolved_date", "cost"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

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
            "request_id": 90,
            "tenant_id": 90,
            "apartment_id": 100,
            "description": 230,
            "priority": 90,
            "status": 110,
            "assigned_worker": 130,
            "scheduled_date": 115,
            "scheduled_time": 115,
            "resolution_notes": 220,
            "time_taken_hours": 120,
            "reported_date": 130,
            "resolved_date": 120,
            "cost": 90
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")

        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)

        self.tree.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Status colour highlighting
        self.tree.tag_configure("REPORTED", background="#fee2e2")
        self.tree.tag_configure("SCHEDULED", background="#fef9c3")
        self.tree.tag_configure("IN_PROGRESS", background="#dbeafe")
        self.tree.tag_configure("RESOLVED", background="#dcfce7")

        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        form_card = tk.LabelFrame(
            self,
            text=" Maintenance Actions ",
            font=("Arial", 11, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"],
            bd=1,
            relief="solid"
        )
        form_card.pack(fill="x", padx=18, pady=10)

        form = tk.Frame(form_card, bg=self.colors["card"])
        form.pack(fill="x", padx=14, pady=14)

        label_style = {
            "bg": self.colors["card"],
            "fg": self.colors["text"],
            "font": ("Arial", 10, "bold")
        }

        entry_style = {
            "font": ("Arial", 10),
            "bg": "#f8fafc",
            "fg": "#111827",
            "insertbackground": "black",
            "relief": "solid",
            "bd": 1,
            "highlightthickness": 1,
            "highlightbackground": self.colors["border"],
            "highlightcolor": "#60a5fa"
        }

        tk.Label(form, text="Request ID", **label_style).grid(row=0, column=0, padx=8, pady=10, sticky="w")
        self.request_id_entry = tk.Entry(form, width=22, **entry_style)
        self.request_id_entry.grid(row=0, column=1, padx=8, pady=10)

        tk.Label(form, text="Tenant ID", **label_style).grid(row=0, column=2, padx=8, pady=10, sticky="w")
        self.tenant_id_entry = tk.Entry(form, width=22, **entry_style)
        self.tenant_id_entry.grid(row=0, column=3, padx=8, pady=10)

        tk.Label(form, text="Apartment ID", **label_style).grid(row=0, column=4, padx=8, pady=10, sticky="w")
        self.apartment_id_entry = tk.Entry(form, width=22, **entry_style)
        self.apartment_id_entry.grid(row=0, column=5, padx=8, pady=10)

        tk.Label(form, text="Description", **label_style).grid(row=1, column=0, padx=8, pady=10, sticky="w")
        self.description_entry = tk.Entry(form, width=54, **entry_style)
        self.description_entry.grid(row=1, column=1, columnspan=3, padx=8, pady=10, sticky="we")

        tk.Label(form, text="Priority", **label_style).grid(row=1, column=4, padx=8, pady=10, sticky="w")
        self.priority_combo = ttk.Combobox(
            form,
            values=["LOW", "MEDIUM", "HIGH"],
            state="readonly",
            width=19
        )
        self.priority_combo.set("LOW")
        self.priority_combo.grid(row=1, column=5, padx=8, pady=10)

        tk.Label(form, text="Assigned Worker", **label_style).grid(row=2, column=0, padx=8, pady=10, sticky="w")
        self.assigned_worker_entry = tk.Entry(form, width=22, **entry_style)
        self.assigned_worker_entry.grid(row=2, column=1, padx=8, pady=10)

        tk.Label(form, text="Scheduled Date", **label_style).grid(row=2, column=2, padx=8, pady=10, sticky="w")
        self.scheduled_date_entry = tk.Entry(form, width=22, **entry_style)
        self.scheduled_date_entry.grid(row=2, column=3, padx=8, pady=10)

        tk.Label(form, text="Scheduled Time", **label_style).grid(row=2, column=4, padx=8, pady=10, sticky="w")
        self.scheduled_time_entry = tk.Entry(form, width=22, **entry_style)
        self.scheduled_time_entry.grid(row=2, column=5, padx=8, pady=10)

        tk.Label(form, text="Resolution Notes", **label_style).grid(row=3, column=0, padx=8, pady=10, sticky="w")
        self.resolution_notes_entry = tk.Entry(form, width=54, **entry_style)
        self.resolution_notes_entry.grid(row=3, column=1, columnspan=3, padx=8, pady=10, sticky="we")

        tk.Label(form, text="Time Taken (hrs)", **label_style).grid(row=3, column=4, padx=8, pady=10, sticky="w")
        self.time_taken_entry = tk.Entry(form, width=22, **entry_style)
        self.time_taken_entry.grid(row=3, column=5, padx=8, pady=10)

        tk.Label(form, text="Cost", **label_style).grid(row=4, column=0, padx=8, pady=10, sticky="w")
        self.cost_entry = tk.Entry(form, width=22, **entry_style)
        self.cost_entry.grid(row=4, column=1, padx=8, pady=10)

        button_frame = tk.Frame(self, bg=self.colors["bg"])
        button_frame.pack(fill="x", padx=18, pady=(4, 18))

        tk.Button(button_frame, text="Create Request", command=self.create_request, **button_style).pack(side="left", padx=6)
        tk.Button(button_frame, text="Change Priority", command=self.change_priority, **button_style).pack(side="left", padx=6)
        tk.Button(button_frame, text="Schedule Request", command=self.schedule_request, **button_style).pack(side="left", padx=6)
        tk.Button(button_frame, text="Start Maintenance", command=self.start_request, **button_style).pack(side="left", padx=6)
        tk.Button(button_frame, text="Resolve Request", command=self.resolve_request, **button_style).pack(side="left", padx=6)
        tk.Button(button_frame, text="Clear Fields", command=self.clear_fields, **button_style).pack(side="left", padx=6)
        tk.Button(button_frame, text="Logout", command=self.logout, **button_style).pack(side="right", padx=6)

    def insert_rows(self, requests):
        self.tree.delete(*self.tree.get_children())

        for row in requests:
            status = row[5]
            self.tree.insert(
                "",
                "end",
                values=row,
                tags=(status,)
            )

    def load_requests(self):
        if hasattr(self, "tenant_search_entry"):
            self.tenant_search_entry.delete(0, tk.END)

        try:
            requests = MaintenanceController.ViewAllRequests()
            self.insert_rows(requests)
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def apply_filter(self):
        status = self.status_filter.get()

        try:
            if status == "ALL":
                requests = MaintenanceController.ViewAllRequests()
            else:
                requests = MaintenanceController.ViewRequestsByStatus(status)

            self.insert_rows(requests)
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
            tenant = int(self.tenant_id_entry.get())
            apartment = int(self.apartment_id_entry.get())
            desc = self.description_entry.get()
            priority = self.priority_combo.get()

            rid = MaintenanceController.CreateRequest(tenant, apartment, desc, priority)
            messagebox.showinfo("Success", f"Request created successfully.\nRequest ID: {rid}")
            self.load_requests()
            self.clear_fields()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def change_priority(self):
        try:
            rid = int(self.request_id_entry.get())
            priority = self.priority_combo.get()

            MaintenanceController.ChangePriority(rid, priority)
            messagebox.showinfo("Success", "Priority updated successfully.")
            self.load_requests()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def schedule_request(self):
        try:
            rid = int(self.request_id_entry.get())
            worker = self.assigned_worker_entry.get()
            date = self.scheduled_date_entry.get()
            time = self.scheduled_time_entry.get()

            MaintenanceController.ScheduleRequest(rid, worker, date, time)
            messagebox.showinfo("Success", "Request scheduled successfully.")
            self.load_requests()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def start_request(self):
        try:
            rid = int(self.request_id_entry.get())

            MaintenanceController.StartRequest(rid)
            messagebox.showinfo("Success", "Maintenance started successfully.")
            self.load_requests()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def resolve_request(self):
        try:
            rid = int(self.request_id_entry.get())
            notes = self.resolution_notes_entry.get()
            hours = float(self.time_taken_entry.get())
            cost = float(self.cost_entry.get())

            MaintenanceController.ResolveRequest(rid, notes, hours, cost)
            messagebox.showinfo("Success", "Request resolved successfully.")
            self.load_requests()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear_fields(self):
        self.request_id_entry.delete(0, tk.END)
        self.tenant_id_entry.delete(0, tk.END)
        self.apartment_id_entry.delete(0, tk.END)
        self.description_entry.delete(0, tk.END)
        self.assigned_worker_entry.delete(0, tk.END)
        self.scheduled_date_entry.delete(0, tk.END)
        self.scheduled_time_entry.delete(0, tk.END)
        self.resolution_notes_entry.delete(0, tk.END)
        self.time_taken_entry.delete(0, tk.END)
        self.cost_entry.delete(0, tk.END)
        self.priority_combo.set("LOW")

    def logout(self):
        self.destroy()
        if self.parent:
            self.parent.deiconify()