import tkinter as tk
from tkinter import ttk, messagebox
from source.app.controllers.FinanceController import FinanceController

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


class FinanceUI(tk.Toplevel):
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.parent = parent
        self.user = user or {}
        self.role = self.user.get("role")

        if self.role != "FINANCE":
            self.destroy()
            raise PermissionError("Only FINANCE users can access the finance dashboard.")

        self.title(f"PAMS — Finance Dashboard ({self.user.get('username', 'Unknown')})")
        self.geometry("1450x860")
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self.logout)

        self.create_styles()
        self.create_widgets()
        self.load_invoices()
        self.load_payments()

    def create_styles(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background=BG_CARD,
                        foreground=FG,
                        fieldbackground=BG_CARD,
                        rowheight=30,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background=BORDER,
                        foreground=FG,
                        font=("Segoe UI", 10, "bold"),
                        relief="flat")
        style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", "#020617")])
        style.configure("TCombobox", fieldbackground=INPUT_BG, background=INPUT_BG, foreground="black")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_CARD, foreground=FG, padding=[16, 8], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", ACCENT)], foreground=[("selected", "#020617")])

    def _button(self, parent, text, command, color=ACCENT, width=14):
        fg = "#020617" if color not in (RED, YELLOW) else "white"
        return tk.Button(parent, text=text, command=command, width=width, height=2,
                         font=("Segoe UI", 10, "bold"), bg=color, fg=fg,
                         activebackground=ACCENT2 if color == ACCENT else color,
                         activeforeground=fg, relief="flat", cursor="hand2")

    def _entry(self, parent, width=12):
        return tk.Entry(parent, width=width, font=("Segoe UI", 10), bg=INPUT_BG,
                        fg="white", insertbackground="white", relief="flat")

    def create_widgets(self):
        tk.Label(self, text="Finance Manager Dashboard", font=("Segoe UI", 22, "bold"), bg=BG, fg=ACCENT).pack(pady=(18, 8))
        user_text = f"Logged in as: {self.user.get('username', 'Unknown')} ({self.role})"
        tk.Label(self, text=user_text, font=("Segoe UI", 11), bg=BG, fg="#94a3b8").pack(pady=(0, 10))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=18, pady=10)

        self.invoice_tab = tk.Frame(notebook, bg=BG)
        notebook.add(self.invoice_tab, text="  Invoices  ")
        self.payment_tab = tk.Frame(notebook, bg=BG)
        notebook.add(self.payment_tab, text="  Payments  ")

        self.build_invoice_tab()
        self.build_payment_tab()
        self.build_summary_panel()

    def build_invoice_tab(self):
        top_frame = tk.Frame(self.invoice_tab, bg=BG)
        top_frame.pack(fill="x", pady=8)

        tk.Label(top_frame, text="Tenant ID:", font=("Segoe UI", 10, "bold"), bg=BG, fg=FG).pack(side="left", padx=6)
        self.inv_tenant_entry = self._entry(top_frame)
        self.inv_tenant_entry.pack(side="left", padx=6)

        tk.Label(top_frame, text="Invoice ID:", font=("Segoe UI", 10, "bold"), bg=BG, fg=FG).pack(side="left", padx=6)
        self.inv_invoice_entry = self._entry(top_frame)
        self.inv_invoice_entry.pack(side="left", padx=6)

        self._button(top_frame, "Search Tenant", self.search_invoice_by_tenant).pack(side="left", padx=6)
        self._button(top_frame, "Search Invoice", self.search_invoice_by_id).pack(side="left", padx=6)
        self._button(top_frame, "View All", self.load_invoices).pack(side="left", padx=6)

        table_card = tk.LabelFrame(self.invoice_tab, text=" Invoices ",
                                   font=("Segoe UI", 11, "bold"), bg=BG_CARD,
                                   fg=ACCENT, bd=1, relief="solid")
        table_card.pack(fill="both", expand=True, padx=8, pady=8)

        columns = ("invoice_id", "lease_id", "tenant_id", "amount_due", "due_date", "status", "paid_amount", "payment_date", "total_due")
        self.invoice_tree = ttk.Treeview(table_card, columns=columns, show="headings")
        headings = {
            "invoice_id": "Invoice ID", "lease_id": "Lease ID", "tenant_id": "Tenant ID", "amount_due": "Amount Due",
            "due_date": "Due Date", "status": "Status", "paid_amount": "Paid Amount", "payment_date": "Payment Date", "total_due": "Total Due"
        }
        widths = {"invoice_id": 100, "lease_id": 100, "tenant_id": 100, "amount_due": 120, "due_date": 120, "status": 110, "paid_amount": 120, "payment_date": 130, "total_due": 120}
        for col in columns:
            self.invoice_tree.heading(col, text=headings[col])
            self.invoice_tree.column(col, width=widths[col], anchor="center")
        self.invoice_tree.pack(fill="both", expand=True, padx=6, pady=6)

    def build_payment_tab(self):
        top_frame = tk.Frame(self.payment_tab, bg=BG)
        top_frame.pack(fill="x", pady=8)

        tk.Label(top_frame, text="Invoice ID:", font=("Segoe UI", 10, "bold"), bg=BG, fg=FG).pack(side="left", padx=6)
        self.pay_invoice_entry = self._entry(top_frame)
        self.pay_invoice_entry.pack(side="left", padx=6)

        self._button(top_frame, "Search Payments", self.search_payment_by_invoice).pack(side="left", padx=6)
        self._button(top_frame, "View All", self.load_payments).pack(side="left", padx=6)

        table_card = tk.LabelFrame(self.payment_tab, text=" Payments ",
                                   font=("Segoe UI", 11, "bold"), bg=BG_CARD,
                                   fg=ACCENT, bd=1, relief="solid")
        table_card.pack(fill="both", expand=True, padx=8, pady=8)

        columns = ("payment_id", "invoice_id", "amount", "payment_date", "method")
        self.payment_tree = ttk.Treeview(table_card, columns=columns, show="headings")
        headings = {"payment_id": "Payment ID", "invoice_id": "Invoice ID", "amount": "Amount", "payment_date": "Payment Date", "method": "Method"}
        widths = {"payment_id": 100, "invoice_id": 100, "amount": 120, "payment_date": 130, "method": 120}
        for col in columns:
            self.payment_tree.heading(col, text=headings[col])
            self.payment_tree.column(col, width=widths[col], anchor="center")
        self.payment_tree.pack(fill="both", expand=True, padx=6, pady=6)

    def build_summary_panel(self):
        panel = tk.LabelFrame(self, text=" Financial Summary ",
                              font=("Segoe UI", 11, "bold"), bg=BG_CARD,
                              fg=ACCENT, bd=1, relief="solid")
        panel.pack(fill="x", padx=18, pady=10)

        self._button(panel, "Calculate Totals", self.calculate_totals, width=18).pack(side="left", padx=6, pady=10)
        self._button(panel, "Net Revenue", self.calculate_net_revenue, width=18).pack(side="left", padx=6, pady=10)
        self._button(panel, "Maintenance Cost", self.calculate_maintenance_cost, width=18).pack(side="left", padx=6, pady=10)
        self._button(panel, "Logout", self.logout, RED, width=18).pack(side="right", padx=6, pady=10)

    def load_invoices(self):
        try:
            self.insert_invoice_rows(FinanceController.GetAllInvoices())
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_payments(self):
        try:
            self.insert_payment_rows(FinanceController.GetAllPayments())
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

    def search_invoice_by_tenant(self):
        try:
            self.insert_invoice_rows(FinanceController.GetInvoicesByTenant(int(self.inv_tenant_entry.get())))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def search_invoice_by_id(self):
        try:
            self.insert_invoice_rows(FinanceController.GetInvoiceById(int(self.inv_invoice_entry.get())))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def search_payment_by_invoice(self):
        try:
            self.insert_payment_rows(FinanceController.GetPaymentsByInvoice(int(self.pay_invoice_entry.get())))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def calculate_totals(self):
        try:
            total = FinanceController.CalculateTotals()
            messagebox.showinfo("Totals", f"Total Collected: £{total['total_collected']}\nTotal Pending: £{total['pending']}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def calculate_net_revenue(self):
        try:
            messagebox.showinfo("Net Revenue", f"Net Revenue: £{FinanceController.CalculateNetRevenue()}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def calculate_maintenance_cost(self):
        try:
            messagebox.showinfo("Maintenance Cost", f"Total Maintenance Cost: £{FinanceController.CalculateMaintenanceCost()}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def logout(self):
        self.destroy()
        if self.parent:
            self.parent.deiconify()
