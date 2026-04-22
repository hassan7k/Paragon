import tkinter as tk
from tkinter import ttk, messagebox
from source.app.databases.database import Get_Connection


class PaymentUI(tk.Toplevel):

    def __init__(self, parent=None, user=None):
        super().__init__(parent)

        self.user = user or {}
        role = self.user.get("role")
        if role != "FINANCE":
            self.destroy()
            raise PermissionError("Only FINANCE users can access payment management.")

        self.title("Payment Management")
        self.geometry("900x600")

        self.build_ui()
        self.load_invoices()

    def build_ui(self):

        tk.Label(self, text="Payments",
                 font=("Arial", 18, "bold")).pack(pady=10)

        # TABLE
        columns = ("InvoiceID", "LeaseID", "DueDate", "Amount", "Status")

        self.tree = ttk.Treeview(self, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)

        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.fill_fields)

        # FORM
        form = tk.Frame(self)
        form.pack(pady=10)

        tk.Label(form, text="Invoice ID").grid(row=0, column=0)
        self.invoice_id = tk.Entry(form)
        self.invoice_id.grid(row=0, column=1)

        tk.Label(form, text="Amount").grid(row=1, column=0)
        self.amount = tk.Entry(form)
        self.amount.grid(row=1, column=1)

        tk.Label(form, text="Method").grid(row=2, column=0)
        self.method = tk.Entry(form)
        self.method.grid(row=2, column=1)

        tk.Button(form, text="Pay Invoice",
                  command=self.pay_invoice).grid(row=3, column=0, columnspan=2, pady=10)

    # ---------------- LOAD ----------------
    def load_invoices(self):
        conn = Get_Connection()
        cur = conn.cursor()

        cur.execute("""
        SELECT invoice_id, lease_id, due_date, amount_due, status
        FROM Invoice
        """)

        rows = cur.fetchall()
        conn.close()

        self.tree.delete(*self.tree.get_children())

        for r in rows:
            self.tree.insert("", "end", values=r)

    # ---------------- SELECT ----------------
    def fill_fields(self, event):
        selected = self.tree.focus()
        data = self.tree.item(selected, "values")

        if not data:
            return

        self.invoice_id.delete(0, tk.END)
        self.invoice_id.insert(0, data[0])

        self.amount.delete(0, tk.END)
        self.amount.insert(0, data[3])

    # ---------------- PAY ----------------
    def pay_invoice(self):
        try:
            invoice_id = int(self.invoice_id.get())
            amount = float(self.amount.get())
            method = self.method.get()

            conn = Get_Connection()
            cur = conn.cursor()

            # Insert payment
            cur.execute("""
            INSERT INTO Payment (invoice_id, amount, payment_date, method)
            VALUES (?, ?, date('now'), ?)
            """, (invoice_id, amount, method))

            # Update invoice status
            cur.execute("""
            UPDATE Invoice SET status='PAID'
            WHERE invoice_id=?
            """, (invoice_id,))

            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "Payment recorded")
            self.load_invoices()

        except Exception as e:
            messagebox.showerror("Error", str(e))