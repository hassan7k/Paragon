import tkinter as tk
from tkinter import messagebox
from source.app.controllers.Lease import LeaseController


class LeaseUI(tk.Toplevel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.title("Create Lease")
        self.geometry("500x600")
        self.configure(bg="#0f172a")

        self.build_ui()

    def build_ui(self):

        tk.Label(self, text="Create Lease",
                 font=("Arial", 18, "bold"),
                 fg="white", bg="#0f172a").pack(pady=15)

        self.tenant_id = self.field("Tenant ID")
        self.apartment_id = self.field("Apartment ID")
        self.start_date = self.field("Start Date (YYYY-MM-DD)")
        self.end_date = self.field("End Date (YYYY-MM-DD)")
        self.deposit = self.field("Deposit")
        self.rent = self.field("Monthly Rent")
        self.first_due = self.field("First Payment Due Date")

        tk.Button(self, text="Create Lease",
                  bg="#22c55e", fg="black",
                  width=20,
                  command=self.create_lease).pack(pady=20)

    def field(self, label):
        frame = tk.Frame(self, bg="#0f172a")
        frame.pack(fill="x", padx=30, pady=8)

        tk.Label(frame, text=label,
                 fg="white", bg="#0f172a",
                 anchor="w").pack(fill="x")

        entry = tk.Entry(frame, bg="#020617", fg="white")
        entry.pack(fill="x")

        return entry

    def create_lease(self):
        try:
            lease_id = LeaseController.CreateLease(
                int(self.tenant_id.get()),
                int(self.apartment_id.get()),
                self.start_date.get(),
                self.end_date.get(),
                float(self.deposit.get()),
                float(self.rent.get()),
                self.first_due.get()
            )

            messagebox.showinfo("Success", f"Lease created!\nLease ID: {lease_id}")
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", str(e))