import tkinter as tk
from tkinter import ttk, messagebox
from source.app.controllers.FinanceController import FinanceController


class FinanceUI(tk.Toplevel):

    def __init__(self, parent=None, user=None):
        super().__init__(parent)

        self.parent = parent
        self.user = user

        self.title("Finance Manager Dashboard")
        self.geometry("1450x860")
        self.configure(bg="#eef2f7")

        self.protocol("WM_DELETE_WINDOW", self.logout)

        self.create_styles()
        self.create_widgets()
        self.load_invoices()
        self.load_payments()

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
            text="Finance Manager Dashboard",
            font=("Arial", 22, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"]
        )
        title.pack(pady=(18, 8))

        user_text = f"Logged in as: {self.user['username']} ({self.user['role']})"
        tk.Label(
            self,
            text=user_text,
            font=("Arial", 11),
            bg=self.colors["bg"],
            fg="#4b5563"
        ).pack(pady=(0, 10))

        # NOTEBOOK TABS
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=18, pady=10)

        # TAB 1: INVOICES
        self.invoice_tab = tk.Frame(notebook, bg=self.colors["bg"])
        notebook.add(self.invoice_tab, text="Invoices")

        # TAB 2: PAYMENTS
        self.payment_tab = tk.Frame(notebook, bg=self.colors["bg"])
        notebook.add(self.payment_tab, text="Payments")

        self.build_invoice_tab()
        self.build_payment_tab()
        self.build_summary_panel()

    # INVOICE TAB

    def build_invoice_tab(self):
        top_frame = tk.Frame(self.invoice_tab, bg=self.colors["bg"])
        top_frame.pack(fill="x", pady=8)

        # Search + Filters
        tk.Label(top_frame, text="Tenant ID:", font=("Arial", 10, "bold"),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(side="left", padx=6)
        self.inv_tenant_entry = tk.Entry(top_frame, width=12)
        self.inv_tenant_entry.pack(side="left", padx=6)

        tk.Label(top_frame, text="Invoice ID:", font=("Arial", 10, "bold"),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(side="left", padx=6)
        self.inv_invoice_entry = tk.Entry(top_frame, width=12)
        self.inv_invoice_entry.pack(side="left", padx=6)

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

        tk.Button(top_frame, text="Search Tenant", command=self.search_invoice_by_tenant,
                  **button_style).pack(side="left", padx=6)
        tk.Button(top_frame, text="Search Invoice", command=self.search_invoice_by_id,
                  **button_style).pack(side="left", padx=6)
        tk.Button(top_frame, text="View All", command=self.load_invoices,
                  **button_style).pack(side="left", padx=6)

        # Table
        table_card = tk.LabelFrame(
            self.invoice_tab,
            text=" Invoices ",
            font=("Arial", 11, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"],
            bd=1,
            relief="solid"
        )
        table_card.pack(fill="both", expand=True, padx=8, pady=8)

        columns = (
            "invoice_id", "lease_id", "tenant_id", "amount_due",
            "due_date", "status", "paid_amount", "payment_date", "total_due"
        )

        self.invoice_tree = ttk.Treeview(
            table_card, columns=columns, show="headings")

        headings = {
            "invoice_id": "Invoice ID",
            "lease_id": "Lease ID",
            "tenant_id": "Tenant ID",
            "amount_due": "Amount Due",
            "due_date": "Due Date",
            "status": "Status",
            "paid_amount": "Paid Amount",
            "payment_date": "Payment Date",
            "total_due": "Total Due"
        }

        widths = {
            "invoice_id": 100,
            "lease_id": 100,
            "tenant_id": 100,
            "amount_due": 120,
            "due_date": 120,
            "status": 110,
            "paid_amount": 120,
            "payment_date": 130,
            "total_due": 120
        }

        for col in columns:
            self.invoice_tree.heading(col, text=headings[col])
            self.invoice_tree.column(col, width=widths[col], anchor="center")

        self.invoice_tree.pack(fill="both", expand=True)

    # PAYMENT TAB

    def build_payment_tab(self):
        top_frame = tk.Frame(self.payment_tab, bg=self.colors["bg"])
        top_frame.pack(fill="x", pady=8)

        tk.Label(top_frame, text="Invoice ID:", font=("Arial", 10, "bold"),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(side="left", padx=6)
        self.pay_invoice_entry = tk.Entry(top_frame, width=12)
        self.pay_invoice_entry.pack(side="left", padx=6)

        tk.Button(top_frame, text="Search Payments", command=self.search_payment_by_invoice,
                  width=14, height=2).pack(side="left", padx=6)
        tk.Button(top_frame, text="View All", command=self.load_payments,
                  width=14, height=2).pack(side="left", padx=6)

        table_card = tk.LabelFrame(
            self.payment_tab,
            text=" Payments ",
            font=("Arial", 11, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"],
            bd=1,
            relief="solid"
        )
        table_card.pack(fill="both", expand=True, padx=8, pady=8)

        columns = ("payment_id", "invoice_id",
                   "amount", "payment_date", "method")

        self.payment_tree = ttk.Treeview(
            table_card, columns=columns, show="headings")

        headings = {
            "payment_id": "Payment ID",
            "invoice_id": "Invoice ID",
            "amount": "Amount",
            "payment_date": "Payment Date",
            "method": "Method"
        }

        widths = {
            "payment_id": 100,
            "invoice_id": 100,
            "amount": 120,
            "payment_date": 130,
            "method": 120
        }

        for col in columns:
            self.payment_tree.heading(col, text=headings[col])
            self.payment_tree.column(col, width=widths[col], anchor="center")

        self.payment_tree.pack(fill="both", expand=True)

    # SUMMARY PANEL

    def build_summary_panel(self):
        panel = tk.LabelFrame(
            self,
            text=" Financial Summary ",
            font=("Arial", 11, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"],
            bd=1,
            relief="solid"
        )
        panel.pack(fill="x", padx=18, pady=10)

        button_style = {
            "width": 18,
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

        tk.Button(panel, text="Calculate Totals", command=self.calculate_totals,
                  **button_style).pack(side="left", padx=6)
        tk.Button(panel, text="Net Revenue", command=self.calculate_net_revenue,
                  **button_style).pack(side="left", padx=6)
        tk.Button(panel, text="Maintenance Cost", command=self.calculate_maintenance_cost,
                  **button_style).pack(side="left", padx=6)
        tk.Button(panel, text="Logout", command=self.logout,
                  **button_style).pack(side="right", padx=6)

    # DATA LOADING

    def load_invoices(self):
        try:
            rows = FinanceController.GetAllInvoices()
            self.insert_invoice_rows(rows)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_payments(self):
        try:
            rows = FinanceController.GetAllPayments()
            self.insert_payment_rows(rows)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def insert_invoice_rows(self, rows):
        self.invoice_tree.delete(*self.invoice_tree.get_children())
        for row in rows:
            self.invoice_tree.insert("", "end", values=row)

    def insert_payment_rows(self, rows):
        self.payment_tree.delete(*self.payment_tree.get_children())
        for row in rows:
            self.payment_tree.insert("", "end", values=row)

    # SEARCH
    def search_invoice_by_tenant(self):
        try:
            tenant_id = int(self.inv_tenant_entry.get())
            rows = FinanceController.GetInvoicesByTenant(tenant_id)
            self.insert_invoice_rows(rows)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def search_invoice_by_id(self):
        try:
            invoice_id = int(self.inv_invoice_entry.get())
            rows = FinanceController.GetInvoiceById(invoice_id)
            self.insert_invoice_rows(rows)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def search_payment_by_invoice(self):
        try:
            invoice_id = int(self.pay_invoice_entry.get())
            rows = FinanceController.GetPaymentsByInvoice(invoice_id)
            self.insert_payment_rows(rows)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # SUMMARY ACTIONS

    def calculate_totals(self):
        try:
            total = FinanceController.CalculateTotals()
            messagebox.showinfo(
                "Totals", f"Total Collected: £{total['collected']}\nTotal Pending: £{total['pending']}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def calculate_net_revenue(self):
        try:
            net = FinanceController.CalculateNetRevenue()
            messagebox.showinfo("Net Revenue", f"Net Revenue: £{net}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def calculate_maintenance_cost(self):
        try:
            cost = FinanceController.CalculateMaintenanceCost()
            messagebox.showinfo("Maintenance Cost",
                                f"Total Maintenance Cost: £{cost}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # LOGOUT

    def logout(self):
        self.destroy()
        if self.parent:
            self.parent.deiconify()
